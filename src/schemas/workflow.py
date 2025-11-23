"""
Workflow Pydantic Schemas

Schemas for workflow definitions, executions, tasks, and messages.
"""

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field


# ============================================================================
# Workflow Schemas
# ============================================================================


class WorkflowStepDefinition(BaseModel):
    """Workflow step definition."""

    type: str = Field(..., description="Step type: agent, mcp_tool, parallel, conditional, http")
    name: str = Field(..., description="Step name")
    agent_id: str | None = Field(None, description="Agent ID (for agent steps)")
    server_id: str | None = Field(None, description="MCP server ID (for mcp_tool steps)")
    tool_name: str | None = Field(None, description="Tool name (for mcp_tool steps)")
    input: dict[str, Any] | None = Field(None, description="Step input data")
    output_mapping: dict[str, str] | None = Field(None, description="Output mapping")
    condition: str | None = Field(None, description="Condition expression (for conditional steps)")
    if_true: dict[str, Any] | None = Field(None, description="Step to execute if true")
    if_false: dict[str, Any] | None = Field(None, description="Step to execute if false")
    steps: list["WorkflowStepDefinition"] | None = Field(
        None, description="Nested steps (for parallel steps)"
    )
    wait_for: str | None = Field(
        None, description="Wait strategy for parallel: all, any, count:N"
    )
    method: str | None = Field(None, description="HTTP method (for http steps)")
    url: str | None = Field(None, description="URL (for http steps)")
    headers: dict[str, str] | None = Field(None, description="HTTP headers")
    body: dict[str, Any] | None = Field(None, description="HTTP body")
    max_retries: int | None = Field(None, description="Max retries for this step")
    priority: int | None = Field(None, description="Priority (1-10)")


class WorkflowTrigger(BaseModel):
    """Workflow trigger definition."""

    type: str = Field(..., description="Trigger type: manual, schedule, webhook, event")
    enabled: bool = Field(default=True, description="Whether trigger is enabled")
    config: dict[str, Any] = Field(default_factory=dict, description="Trigger configuration")


class WorkflowCreate(BaseModel):
    """Create workflow request."""

    name: str = Field(..., min_length=1, max_length=255, description="Workflow name")
    description: str | None = Field(None, max_length=1000, description="Workflow description")
    version: str = Field(default="1.0.0", description="Workflow version")
    steps: list[WorkflowStepDefinition] = Field(..., min_items=1, description="Workflow steps")
    triggers: list[WorkflowTrigger] | None = Field(None, description="Workflow triggers")
    timeout_seconds: int = Field(default=3600, ge=1, description="Workflow timeout in seconds")
    max_retries: int = Field(default=3, ge=0, le=10, description="Max retries")
    retry_strategy: str = Field(
        default="exponential", description="Retry strategy: exponential, linear, none"
    )
    tags: list[str] | None = Field(None, description="Workflow tags")
    category: str | None = Field(None, max_length=100, description="Workflow category")


class WorkflowUpdate(BaseModel):
    """Update workflow request."""

    name: str | None = Field(None, min_length=1, max_length=255, description="Workflow name")
    description: str | None = Field(None, max_length=1000, description="Workflow description")
    version: str | None = Field(None, description="Workflow version")
    steps: list[WorkflowStepDefinition] | None = Field(None, description="Workflow steps")
    triggers: list[WorkflowTrigger] | None = Field(None, description="Workflow triggers")
    timeout_seconds: int | None = Field(None, ge=1, description="Workflow timeout in seconds")
    max_retries: int | None = Field(None, ge=0, le=10, description="Max retries")
    retry_strategy: str | None = Field(None, description="Retry strategy")
    status: str | None = Field(None, description="Workflow status: draft, active, archived")
    tags: list[str] | None = Field(None, description="Workflow tags")
    category: str | None = Field(None, max_length=100, description="Workflow category")


class WorkflowResponse(BaseModel):
    """Workflow response."""

    id: UUID = Field(..., description="Workflow ID")
    tenant_id: UUID = Field(..., description="Tenant ID")
    name: str = Field(..., description="Workflow name")
    slug: str = Field(..., description="Workflow slug")
    description: str | None = Field(None, description="Workflow description")
    version: str = Field(..., description="Workflow version")
    steps: list[dict[str, Any]] = Field(..., description="Workflow steps")
    triggers: list[dict[str, Any]] | None = Field(None, description="Workflow triggers")
    timeout_seconds: int = Field(..., description="Workflow timeout in seconds")
    max_retries: int = Field(..., description="Max retries")
    retry_strategy: str = Field(..., description="Retry strategy")
    status: str = Field(..., description="Workflow status")
    tags: list[str] | None = Field(None, description="Workflow tags")
    category: str | None = Field(None, description="Workflow category")
    execution_count: int = Field(..., description="Total execution count")
    success_count: int = Field(..., description="Successful execution count")
    failure_count: int = Field(..., description="Failed execution count")
    avg_duration_seconds: int | None = Field(None, description="Average duration in seconds")
    created_by: UUID | None = Field(None, description="Created by user ID")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")

    class Config:
        from_attributes = True


class WorkflowListResponse(BaseModel):
    """List workflows response."""

    workflows: list[WorkflowResponse] = Field(..., description="List of workflows")
    total: int = Field(..., description="Total count")
    offset: int = Field(..., description="Offset")
    limit: int = Field(..., description="Limit")


# ============================================================================
# Workflow Execution Schemas
# ============================================================================


class WorkflowExecuteRequest(BaseModel):
    """Execute workflow request."""

    workflow_id: UUID = Field(..., description="Workflow to execute")
    input_data: dict[str, Any] = Field(default_factory=dict, description="Input data")
    context: dict[str, Any] | None = Field(None, description="Execution context")


class WorkflowStepExecutionResponse(BaseModel):
    """Workflow step execution response."""

    id: UUID = Field(..., description="Step execution ID")
    workflow_execution_id: UUID = Field(..., description="Workflow execution ID")
    step_name: str = Field(..., description="Step name")
    step_type: str = Field(..., description="Step type")
    agent_id: UUID | None = Field(None, description="Agent ID")
    status: str = Field(..., description="Step status")
    input_data: dict[str, Any] | None = Field(None, description="Input data")
    output_data: dict[str, Any] | None = Field(None, description="Output data")
    error_message: str | None = Field(None, description="Error message")
    retry_count: int = Field(..., description="Retry count")
    duration_seconds: int | None = Field(None, description="Duration in seconds")
    started_at: datetime | None = Field(None, description="Start timestamp")
    completed_at: datetime | None = Field(None, description="Completion timestamp")

    class Config:
        from_attributes = True


class WorkflowExecutionResponse(BaseModel):
    """Workflow execution response."""

    id: UUID = Field(..., description="Execution ID")
    tenant_id: UUID = Field(..., description="Tenant ID")
    workflow_id: UUID = Field(..., description="Workflow ID")
    status: str = Field(..., description="Execution status")
    current_step: str = Field(..., description="Current step name")
    input_data: dict[str, Any] | None = Field(None, description="Input data")
    output_data: dict[str, Any] | None = Field(None, description="Output data")
    context: dict[str, Any] | None = Field(None, description="Execution context")
    error_message: str | None = Field(None, description="Error message")
    duration_seconds: int | None = Field(None, description="Duration in seconds")
    started_at: datetime | None = Field(None, description="Start timestamp")
    completed_at: datetime | None = Field(None, description="Completion timestamp")
    created_at: datetime = Field(..., description="Creation timestamp")

    class Config:
        from_attributes = True


class WorkflowExecutionDetailResponse(WorkflowExecutionResponse):
    """Workflow execution detail response with steps."""

    steps: list[WorkflowStepExecutionResponse] = Field(..., description="Step executions")


class WorkflowExecutionListResponse(BaseModel):
    """List workflow executions response."""

    executions: list[WorkflowExecutionResponse] = Field(..., description="List of executions")
    total: int = Field(..., description="Total count")
    offset: int = Field(..., description="Offset")
    limit: int = Field(..., description="Limit")


# ============================================================================
# Agent Task Schemas
# ============================================================================


class AgentTaskCreate(BaseModel):
    """Create agent task request."""

    agent_id: UUID = Field(..., description="Agent ID")
    parent_task_id: UUID | None = Field(None, description="Parent task ID")
    workflow_execution_id: UUID | None = Field(None, description="Workflow execution ID")
    task_type: str = Field(
        default="execute", description="Task type: execute, delegate, communicate"
    )
    instruction: str = Field(..., min_length=1, description="Task instruction")
    context: dict[str, Any] | None = Field(None, description="Task context")
    priority: int = Field(default=5, ge=1, le=10, description="Task priority")
    due_at: datetime | None = Field(None, description="Due date")


class AgentTaskUpdate(BaseModel):
    """Update agent task request."""

    status: str | None = Field(None, description="Task status")
    priority: int | None = Field(None, ge=1, le=10, description="Task priority")
    result: dict[str, Any] | None = Field(None, description="Task result")
    error_message: str | None = Field(None, description="Error message")


class AgentTaskResponse(BaseModel):
    """Agent task response."""

    id: UUID = Field(..., description="Task ID")
    tenant_id: UUID = Field(..., description="Tenant ID")
    agent_id: UUID = Field(..., description="Agent ID")
    parent_task_id: UUID | None = Field(None, description="Parent task ID")
    workflow_execution_id: UUID | None = Field(None, description="Workflow execution ID")
    task_type: str = Field(..., description="Task type")
    instruction: str = Field(..., description="Task instruction")
    context: dict[str, Any] | None = Field(None, description="Task context")
    status: str = Field(..., description="Task status")
    priority: int = Field(..., description="Task priority")
    result: dict[str, Any] | None = Field(None, description="Task result")
    error_message: str | None = Field(None, description="Error message")
    assigned_at: datetime | None = Field(None, description="Assignment timestamp")
    started_at: datetime | None = Field(None, description="Start timestamp")
    completed_at: datetime | None = Field(None, description="Completion timestamp")
    due_at: datetime | None = Field(None, description="Due date")
    created_at: datetime = Field(..., description="Creation timestamp")

    class Config:
        from_attributes = True


class AgentTaskListResponse(BaseModel):
    """List agent tasks response."""

    tasks: list[AgentTaskResponse] = Field(..., description="List of tasks")
    total: int = Field(..., description="Total count")
    offset: int = Field(..., description="Offset")
    limit: int = Field(..., description="Limit")


# ============================================================================
# Agent Message Schemas
# ============================================================================


class AgentMessageCreate(BaseModel):
    """Create agent message request."""

    from_agent_id: UUID = Field(..., description="Sender agent ID")
    to_agent_id: UUID = Field(..., description="Recipient agent ID")
    workflow_execution_id: UUID | None = Field(None, description="Workflow execution ID")
    message_type: str = Field(
        default="request", description="Message type: request, response, notification, broadcast"
    )
    content: str = Field(..., min_length=1, description="Message content")
    data: dict[str, Any] | None = Field(None, description="Message data")
    requires_response: bool = Field(default=False, description="Requires response")
    response_id: UUID | None = Field(None, description="Response to message ID")


class AgentMessageUpdate(BaseModel):
    """Update agent message request."""

    status: str | None = Field(None, description="Message status")


class AgentMessageResponse(BaseModel):
    """Agent message response."""

    id: UUID = Field(..., description="Message ID")
    tenant_id: UUID = Field(..., description="Tenant ID")
    from_agent_id: UUID = Field(..., description="Sender agent ID")
    to_agent_id: UUID = Field(..., description="Recipient agent ID")
    workflow_execution_id: UUID | None = Field(None, description="Workflow execution ID")
    message_type: str = Field(..., description="Message type")
    content: str = Field(..., description="Message content")
    data: dict[str, Any] | None = Field(None, description="Message data")
    status: str = Field(..., description="Message status")
    requires_response: bool = Field(..., description="Requires response")
    response_id: UUID | None = Field(None, description="Response to message ID")
    sent_at: datetime | None = Field(None, description="Sent timestamp")
    delivered_at: datetime | None = Field(None, description="Delivered timestamp")
    read_at: datetime | None = Field(None, description="Read timestamp")
    created_at: datetime = Field(..., description="Creation timestamp")

    class Config:
        from_attributes = True


class AgentMessageListResponse(BaseModel):
    """List agent messages response."""

    messages: list[AgentMessageResponse] = Field(..., description="List of messages")
    total: int = Field(..., description="Total count")
    offset: int = Field(..., description="Offset")
    limit: int = Field(..., description="Limit")
