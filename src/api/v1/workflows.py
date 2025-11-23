"""
Workflow API Endpoints

Provides REST API for:
- Workflow CRUD operations
- Workflow execution and monitoring
- Agent task management
- Inter-agent messaging
"""

from datetime import datetime, timezone
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from slugify import slugify
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.api.dependencies import CurrentTenant, CurrentUser, get_db
from src.db.models import (
    AgentMessage,
    AgentTask,
    Workflow,
    WorkflowExecution,
    WorkflowStepExecution,
)
from src.schemas.workflow import (
    AgentMessageCreate,
    AgentMessageListResponse,
    AgentMessageResponse,
    AgentMessageUpdate,
    AgentTaskCreate,
    AgentTaskListResponse,
    AgentTaskResponse,
    AgentTaskUpdate,
    WorkflowCreate,
    WorkflowExecuteRequest,
    WorkflowExecutionDetailResponse,
    WorkflowExecutionListResponse,
    WorkflowExecutionResponse,
    WorkflowListResponse,
    WorkflowResponse,
    WorkflowStepExecutionResponse,
    WorkflowUpdate,
)
from src.services.workflow_engine import WorkflowEngine

router = APIRouter()


# ============================================================================
# Workflow CRUD Endpoints
# ============================================================================


@router.post("/workflows", response_model=WorkflowResponse, status_code=status.HTTP_201_CREATED)
async def create_workflow(
    workflow_data: WorkflowCreate,
    tenant: CurrentTenant,
    user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Create a new workflow."""
    # Generate slug
    slug = slugify(workflow_data.name)

    # Check for duplicate slug
    result = await db.execute(
        select(Workflow).where(
            Workflow.tenant_id == tenant.id,
            Workflow.slug == slug,
            Workflow.deleted_at.is_(None),
        )
    )
    if result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Workflow with slug '{slug}' already exists",
        )

    # Convert step definitions to dict
    steps = [step.model_dump() for step in workflow_data.steps]
    triggers = (
        [trigger.model_dump() for trigger in workflow_data.triggers]
        if workflow_data.triggers
        else None
    )

    # Create workflow
    workflow = Workflow(
        tenant_id=tenant.id,
        name=workflow_data.name,
        slug=slug,
        description=workflow_data.description,
        version=workflow_data.version,
        steps=steps,
        triggers=triggers,
        timeout_seconds=workflow_data.timeout_seconds,
        max_retries=workflow_data.max_retries,
        retry_strategy=workflow_data.retry_strategy,
        status="draft",
        tags=workflow_data.tags,
        category=workflow_data.category,
        created_by=user.id,
    )

    db.add(workflow)
    await db.commit()
    await db.refresh(workflow)

    return workflow


@router.get("/workflows", response_model=WorkflowListResponse)
async def list_workflows(
    tenant: CurrentTenant,
    db: Annotated[AsyncSession, Depends(get_db)],
    offset: int = Query(0, ge=0, description="Offset for pagination"),
    limit: int = Query(50, ge=1, le=100, description="Limit for pagination"),
    status: str | None = Query(None, description="Filter by status"),
    category: str | None = Query(None, description="Filter by category"),
):
    """List all workflows for the tenant."""
    # Build query
    query = select(Workflow).where(
        Workflow.tenant_id == tenant.id,
        Workflow.deleted_at.is_(None),
    )

    if status:
        query = query.where(Workflow.status == status)
    if category:
        query = query.where(Workflow.category == category)

    # Get total count
    count_query = select(func.count()).select_from(query.subquery())
    total = await db.scalar(count_query)

    # Get workflows
    query = query.order_by(Workflow.created_at.desc()).offset(offset).limit(limit)
    result = await db.execute(query)
    workflows = result.scalars().all()

    return WorkflowListResponse(
        workflows=workflows,
        total=total or 0,
        offset=offset,
        limit=limit,
    )


@router.get("/workflows/{workflow_id}", response_model=WorkflowResponse)
async def get_workflow(
    workflow_id: UUID,
    tenant: CurrentTenant,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Get workflow by ID."""
    result = await db.execute(
        select(Workflow).where(
            Workflow.id == workflow_id,
            Workflow.tenant_id == tenant.id,
            Workflow.deleted_at.is_(None),
        )
    )
    workflow = result.scalar_one_or_none()

    if not workflow:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Workflow {workflow_id} not found",
        )

    return workflow


@router.patch("/workflows/{workflow_id}", response_model=WorkflowResponse)
async def update_workflow(
    workflow_id: UUID,
    workflow_data: WorkflowUpdate,
    tenant: CurrentTenant,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Update a workflow."""
    # Get workflow
    result = await db.execute(
        select(Workflow).where(
            Workflow.id == workflow_id,
            Workflow.tenant_id == tenant.id,
            Workflow.deleted_at.is_(None),
        )
    )
    workflow = result.scalar_one_or_none()

    if not workflow:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Workflow {workflow_id} not found",
        )

    # Update fields
    update_data = workflow_data.model_dump(exclude_unset=True)

    # Handle name change (regenerate slug)
    if "name" in update_data:
        new_slug = slugify(update_data["name"])
        # Check for slug conflict
        result = await db.execute(
            select(Workflow).where(
                Workflow.tenant_id == tenant.id,
                Workflow.slug == new_slug,
                Workflow.id != workflow_id,
                Workflow.deleted_at.is_(None),
            )
        )
        if result.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Workflow with slug '{new_slug}' already exists",
            )
        workflow.slug = new_slug

    # Convert step definitions if provided
    if "steps" in update_data and update_data["steps"]:
        update_data["steps"] = [step.model_dump() for step in workflow_data.steps]

    # Convert trigger definitions if provided
    if "triggers" in update_data and update_data["triggers"]:
        update_data["triggers"] = [trigger.model_dump() for trigger in workflow_data.triggers]

    # Apply updates
    for field, value in update_data.items():
        setattr(workflow, field, value)

    await db.commit()
    await db.refresh(workflow)

    return workflow


@router.delete("/workflows/{workflow_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_workflow(
    workflow_id: UUID,
    tenant: CurrentTenant,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Soft delete a workflow."""
    result = await db.execute(
        select(Workflow).where(
            Workflow.id == workflow_id,
            Workflow.tenant_id == tenant.id,
            Workflow.deleted_at.is_(None),
        )
    )
    workflow = result.scalar_one_or_none()

    if not workflow:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Workflow {workflow_id} not found",
        )

    # Soft delete
    workflow.deleted_at = datetime.now(timezone.utc)
    await db.commit()


@router.post("/workflows/{workflow_id}/activate", response_model=WorkflowResponse)
async def activate_workflow(
    workflow_id: UUID,
    tenant: CurrentTenant,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Activate a workflow (change status to active)."""
    result = await db.execute(
        select(Workflow).where(
            Workflow.id == workflow_id,
            Workflow.tenant_id == tenant.id,
            Workflow.deleted_at.is_(None),
        )
    )
    workflow = result.scalar_one_or_none()

    if not workflow:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Workflow {workflow_id} not found",
        )

    workflow.status = "active"
    await db.commit()
    await db.refresh(workflow)

    return workflow


# ============================================================================
# Workflow Execution Endpoints
# ============================================================================


@router.post("/workflows/execute", response_model=WorkflowExecutionResponse)
async def execute_workflow(
    execute_data: WorkflowExecuteRequest,
    tenant: CurrentTenant,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Execute a workflow."""
    # Create workflow engine
    engine = WorkflowEngine(db, tenant.id)

    # Execute workflow
    try:
        execution = await engine.execute_workflow(
            workflow_id=execute_data.workflow_id,
            input_data=execute_data.input_data,
            context=execute_data.context,
        )
        return execution
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Workflow execution failed: {str(e)}",
        )


@router.get("/workflows/executions", response_model=WorkflowExecutionListResponse)
async def list_workflow_executions(
    tenant: CurrentTenant,
    db: Annotated[AsyncSession, Depends(get_db)],
    offset: int = Query(0, ge=0, description="Offset for pagination"),
    limit: int = Query(50, ge=1, le=100, description="Limit for pagination"),
    workflow_id: UUID | None = Query(None, description="Filter by workflow ID"),
    status: str | None = Query(None, description="Filter by status"),
):
    """List workflow executions."""
    # Build query
    query = select(WorkflowExecution).where(
        WorkflowExecution.tenant_id == tenant.id,
    )

    if workflow_id:
        query = query.where(WorkflowExecution.workflow_id == workflow_id)
    if status:
        query = query.where(WorkflowExecution.status == status)

    # Get total count
    count_query = select(func.count()).select_from(query.subquery())
    total = await db.scalar(count_query)

    # Get executions
    query = query.order_by(WorkflowExecution.created_at.desc()).offset(offset).limit(limit)
    result = await db.execute(query)
    executions = result.scalars().all()

    return WorkflowExecutionListResponse(
        executions=executions,
        total=total or 0,
        offset=offset,
        limit=limit,
    )


@router.get("/workflows/executions/{execution_id}", response_model=WorkflowExecutionDetailResponse)
async def get_workflow_execution(
    execution_id: UUID,
    tenant: CurrentTenant,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Get workflow execution detail with steps."""
    # Get execution with steps
    result = await db.execute(
        select(WorkflowExecution)
        .options(selectinload(WorkflowExecution.step_executions))
        .where(
            WorkflowExecution.id == execution_id,
            WorkflowExecution.tenant_id == tenant.id,
        )
    )
    execution = result.scalar_one_or_none()

    if not execution:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Workflow execution {execution_id} not found",
        )

    # Convert to response model
    return WorkflowExecutionDetailResponse(
        id=execution.id,
        tenant_id=execution.tenant_id,
        workflow_id=execution.workflow_id,
        status=execution.status,
        current_step=execution.current_step,
        input_data=execution.input_data,
        output_data=execution.output_data,
        context=execution.context,
        error_message=execution.error_message,
        duration_seconds=execution.duration_seconds,
        started_at=execution.started_at,
        completed_at=execution.completed_at,
        created_at=execution.created_at,
        steps=[
            WorkflowStepExecutionResponse.model_validate(step)
            for step in execution.step_executions
        ],
    )


@router.post("/workflows/executions/{execution_id}/cancel", response_model=WorkflowExecutionResponse)
async def cancel_workflow_execution(
    execution_id: UUID,
    tenant: CurrentTenant,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Cancel a running workflow execution."""
    engine = WorkflowEngine(db, tenant.id)

    try:
        execution = await engine.cancel_workflow(execution_id)
        return execution
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.get("/workflows/executions/{execution_id}/status")
async def get_execution_status(
    execution_id: UUID,
    tenant: CurrentTenant,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Get detailed execution status."""
    engine = WorkflowEngine(db, tenant.id)

    try:
        status_data = await engine.get_execution_status(execution_id)
        return status_data
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )


# ============================================================================
# Agent Task Endpoints
# ============================================================================


@router.post("/tasks", response_model=AgentTaskResponse, status_code=status.HTTP_201_CREATED)
async def create_agent_task(
    task_data: AgentTaskCreate,
    tenant: CurrentTenant,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Create a new agent task."""
    task = AgentTask(
        tenant_id=tenant.id,
        agent_id=task_data.agent_id,
        parent_task_id=task_data.parent_task_id,
        workflow_execution_id=task_data.workflow_execution_id,
        task_type=task_data.task_type,
        instruction=task_data.instruction,
        context=task_data.context,
        status="pending",
        priority=task_data.priority,
        assigned_at=datetime.now(timezone.utc),
        due_at=task_data.due_at,
    )

    db.add(task)
    await db.commit()
    await db.refresh(task)

    return task


@router.get("/tasks", response_model=AgentTaskListResponse)
async def list_agent_tasks(
    tenant: CurrentTenant,
    db: Annotated[AsyncSession, Depends(get_db)],
    offset: int = Query(0, ge=0, description="Offset for pagination"),
    limit: int = Query(50, ge=1, le=100, description="Limit for pagination"),
    agent_id: UUID | None = Query(None, description="Filter by agent ID"),
    status: str | None = Query(None, description="Filter by status"),
    workflow_execution_id: UUID | None = Query(None, description="Filter by workflow execution"),
):
    """List agent tasks."""
    # Build query
    query = select(AgentTask).where(AgentTask.tenant_id == tenant.id)

    if agent_id:
        query = query.where(AgentTask.agent_id == agent_id)
    if status:
        query = query.where(AgentTask.status == status)
    if workflow_execution_id:
        query = query.where(AgentTask.workflow_execution_id == workflow_execution_id)

    # Get total count
    count_query = select(func.count()).select_from(query.subquery())
    total = await db.scalar(count_query)

    # Get tasks
    query = query.order_by(AgentTask.created_at.desc()).offset(offset).limit(limit)
    result = await db.execute(query)
    tasks = result.scalars().all()

    return AgentTaskListResponse(
        tasks=tasks,
        total=total or 0,
        offset=offset,
        limit=limit,
    )


@router.get("/tasks/{task_id}", response_model=AgentTaskResponse)
async def get_agent_task(
    task_id: UUID,
    tenant: CurrentTenant,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Get agent task by ID."""
    result = await db.execute(
        select(AgentTask).where(
            AgentTask.id == task_id,
            AgentTask.tenant_id == tenant.id,
        )
    )
    task = result.scalar_one_or_none()

    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Task {task_id} not found",
        )

    return task


@router.patch("/tasks/{task_id}", response_model=AgentTaskResponse)
async def update_agent_task(
    task_id: UUID,
    task_data: AgentTaskUpdate,
    tenant: CurrentTenant,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Update an agent task."""
    # Get task
    result = await db.execute(
        select(AgentTask).where(
            AgentTask.id == task_id,
            AgentTask.tenant_id == tenant.id,
        )
    )
    task = result.scalar_one_or_none()

    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Task {task_id} not found",
        )

    # Update fields
    update_data = task_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(task, field, value)

    # Update timestamps based on status
    if "status" in update_data:
        if update_data["status"] == "in_progress" and not task.started_at:
            task.started_at = datetime.now(timezone.utc)
        elif update_data["status"] in ["completed", "failed"] and not task.completed_at:
            task.completed_at = datetime.now(timezone.utc)

    await db.commit()
    await db.refresh(task)

    return task


# ============================================================================
# Agent Message Endpoints
# ============================================================================


@router.post("/messages", response_model=AgentMessageResponse, status_code=status.HTTP_201_CREATED)
async def create_agent_message(
    message_data: AgentMessageCreate,
    tenant: CurrentTenant,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Create a new agent message."""
    message = AgentMessage(
        tenant_id=tenant.id,
        from_agent_id=message_data.from_agent_id,
        to_agent_id=message_data.to_agent_id,
        workflow_execution_id=message_data.workflow_execution_id,
        message_type=message_data.message_type,
        content=message_data.content,
        data=message_data.data,
        status="sent",
        requires_response=message_data.requires_response,
        response_id=message_data.response_id,
        sent_at=datetime.now(timezone.utc),
    )

    db.add(message)
    await db.commit()
    await db.refresh(message)

    return message


@router.get("/messages", response_model=AgentMessageListResponse)
async def list_agent_messages(
    tenant: CurrentTenant,
    db: Annotated[AsyncSession, Depends(get_db)],
    offset: int = Query(0, ge=0, description="Offset for pagination"),
    limit: int = Query(50, ge=1, le=100, description="Limit for pagination"),
    from_agent_id: UUID | None = Query(None, description="Filter by sender agent"),
    to_agent_id: UUID | None = Query(None, description="Filter by recipient agent"),
    workflow_execution_id: UUID | None = Query(None, description="Filter by workflow execution"),
):
    """List agent messages."""
    # Build query
    query = select(AgentMessage).where(AgentMessage.tenant_id == tenant.id)

    if from_agent_id:
        query = query.where(AgentMessage.from_agent_id == from_agent_id)
    if to_agent_id:
        query = query.where(AgentMessage.to_agent_id == to_agent_id)
    if workflow_execution_id:
        query = query.where(AgentMessage.workflow_execution_id == workflow_execution_id)

    # Get total count
    count_query = select(func.count()).select_from(query.subquery())
    total = await db.scalar(count_query)

    # Get messages
    query = query.order_by(AgentMessage.created_at.desc()).offset(offset).limit(limit)
    result = await db.execute(query)
    messages = result.scalars().all()

    return AgentMessageListResponse(
        messages=messages,
        total=total or 0,
        offset=offset,
        limit=limit,
    )


@router.get("/messages/{message_id}", response_model=AgentMessageResponse)
async def get_agent_message(
    message_id: UUID,
    tenant: CurrentTenant,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Get agent message by ID."""
    result = await db.execute(
        select(AgentMessage).where(
            AgentMessage.id == message_id,
            AgentMessage.tenant_id == message.id,
        )
    )
    message = result.scalar_one_or_none()

    if not message:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Message {message_id} not found",
        )

    return message


@router.patch("/messages/{message_id}", response_model=AgentMessageResponse)
async def update_agent_message(
    message_id: UUID,
    message_data: AgentMessageUpdate,
    tenant: CurrentTenant,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Update an agent message (mark as delivered/read/processed)."""
    # Get message
    result = await db.execute(
        select(AgentMessage).where(
            AgentMessage.id == message_id,
            AgentMessage.tenant_id == tenant.id,
        )
    )
    message = result.scalar_one_or_none()

    if not message:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Message {message_id} not found",
        )

    # Update status and timestamps
    if message_data.status:
        message.status = message_data.status
        now = datetime.now(timezone.utc)

        if message_data.status == "delivered" and not message.delivered_at:
            message.delivered_at = now
        elif message_data.status == "read" and not message.read_at:
            message.read_at = now
            if not message.delivered_at:
                message.delivered_at = now

    await db.commit()
    await db.refresh(message)

    return message
