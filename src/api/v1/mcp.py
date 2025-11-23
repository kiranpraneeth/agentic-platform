"""MCP (Model Context Protocol) endpoints."""

from datetime import datetime
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.dependencies import CurrentTenant, CurrentUser
from src.db.models import MCPServer, MCPServerConfig, MCPToolExecution
from src.db.session import get_db
from src.schemas.mcp import (
    MCPServerConfigCreate,
    MCPServerConfigResponse,
    MCPServerConfigUpdate,
    MCPServerCreate,
    MCPServerDiscoveryResponse,
    MCPServerListResponse,
    MCPServerResponse,
    MCPServerUpdate,
    MCPToolExecuteRequest,
    MCPToolExecuteResponse,
    MCPToolExecutionListResponse,
    MCPToolExecutionResponse,
)
from src.services.mcp_client import MCPClient

router = APIRouter()


# ============================================================================
# MCP Server Endpoints
# ============================================================================


@router.post("/servers", response_model=MCPServerResponse, status_code=status.HTTP_201_CREATED)
async def create_mcp_server(
    server_data: MCPServerCreate,
    tenant: CurrentTenant,
    user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> MCPServer:
    """Create a new MCP server."""
    # Check if slug already exists for this tenant
    result = await db.execute(
        select(MCPServer).where(
            MCPServer.tenant_id == tenant.id,
            MCPServer.slug == server_data.slug,
            MCPServer.deleted_at.is_(None),
        )
    )
    existing = result.scalar_one_or_none()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"MCP server with slug '{server_data.slug}' already exists",
        )

    # Create server
    server = MCPServer(tenant_id=tenant.id, **server_data.model_dump())
    db.add(server)
    await db.commit()
    await db.refresh(server)

    return server


@router.get("/servers", response_model=MCPServerListResponse)
async def list_mcp_servers(
    tenant: CurrentTenant,
    user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status: str | None = Query(None),
    category: str | None = Query(None),
    search: str | None = Query(None),
) -> MCPServerListResponse:
    """List all MCP servers for tenant."""
    # Build query
    query = select(MCPServer).where(MCPServer.tenant_id == tenant.id, MCPServer.deleted_at.is_(None))

    if status:
        query = query.where(MCPServer.status == status)

    if category:
        query = query.where(MCPServer.category == category)

    if search:
        query = query.where(MCPServer.name.ilike(f"%{search}%"))

    # Count total
    count_query = select(func.count()).select_from(query.subquery())
    total = await db.scalar(count_query) or 0

    # Get page of results
    offset = (page - 1) * page_size
    query = query.offset(offset).limit(page_size).order_by(MCPServer.created_at.desc())
    result = await db.execute(query)
    servers = result.scalars().all()

    return MCPServerListResponse(
        servers=[MCPServerResponse.model_validate(server) for server in servers],
        total=total,
        page=page,
        page_size=page_size,
        has_more=(offset + len(servers)) < total,
    )


@router.get("/servers/{server_id}", response_model=MCPServerResponse)
async def get_mcp_server(
    server_id: UUID,
    tenant: CurrentTenant,
    user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> MCPServer:
    """Get a specific MCP server."""
    result = await db.execute(
        select(MCPServer).where(
            MCPServer.id == server_id, MCPServer.tenant_id == tenant.id, MCPServer.deleted_at.is_(None)
        )
    )
    server = result.scalar_one_or_none()

    if not server:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="MCP server not found")

    return server


@router.patch("/servers/{server_id}", response_model=MCPServerResponse)
async def update_mcp_server(
    server_id: UUID,
    server_data: MCPServerUpdate,
    tenant: CurrentTenant,
    user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> MCPServer:
    """Update an MCP server."""
    result = await db.execute(
        select(MCPServer).where(
            MCPServer.id == server_id, MCPServer.tenant_id == tenant.id, MCPServer.deleted_at.is_(None)
        )
    )
    server = result.scalar_one_or_none()

    if not server:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="MCP server not found")

    # Update fields
    update_data = server_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(server, field, value)

    server.updated_at = datetime.utcnow()
    await db.commit()
    await db.refresh(server)

    return server


@router.delete("/servers/{server_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_mcp_server(
    server_id: UUID,
    tenant: CurrentTenant,
    user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> None:
    """Delete an MCP server (soft delete)."""
    result = await db.execute(
        select(MCPServer).where(
            MCPServer.id == server_id, MCPServer.tenant_id == tenant.id, MCPServer.deleted_at.is_(None)
        )
    )
    server = result.scalar_one_or_none()

    if not server:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="MCP server not found")

    server.deleted_at = datetime.utcnow()
    await db.commit()


# ============================================================================
# MCP Server Configuration Endpoints
# ============================================================================


@router.post("/configs", response_model=MCPServerConfigResponse, status_code=status.HTTP_201_CREATED)
async def create_mcp_server_config(
    config_data: MCPServerConfigCreate,
    tenant: CurrentTenant,
    user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> MCPServerConfig:
    """Create a new MCP server configuration."""
    # Verify server exists and belongs to tenant
    result = await db.execute(
        select(MCPServer).where(
            MCPServer.id == config_data.server_id,
            MCPServer.tenant_id == tenant.id,
            MCPServer.deleted_at.is_(None),
        )
    )
    server = result.scalar_one_or_none()
    if not server:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="MCP server not found")

    # Create config
    config = MCPServerConfig(tenant_id=tenant.id, **config_data.model_dump())
    db.add(config)
    await db.commit()
    await db.refresh(config)

    return config


@router.get("/configs/{config_id}", response_model=MCPServerConfigResponse)
async def get_mcp_server_config(
    config_id: UUID,
    tenant: CurrentTenant,
    user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> MCPServerConfig:
    """Get a specific MCP server configuration."""
    result = await db.execute(
        select(MCPServerConfig).where(MCPServerConfig.id == config_id, MCPServerConfig.tenant_id == tenant.id)
    )
    config = result.scalar_one_or_none()

    if not config:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="MCP server config not found")

    return config


@router.patch("/configs/{config_id}", response_model=MCPServerConfigResponse)
async def update_mcp_server_config(
    config_id: UUID,
    config_data: MCPServerConfigUpdate,
    tenant: CurrentTenant,
    user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> MCPServerConfig:
    """Update an MCP server configuration."""
    result = await db.execute(
        select(MCPServerConfig).where(MCPServerConfig.id == config_id, MCPServerConfig.tenant_id == tenant.id)
    )
    config = result.scalar_one_or_none()

    if not config:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="MCP server config not found")

    # Update fields
    update_data = config_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(config, field, value)

    config.updated_at = datetime.utcnow()
    await db.commit()
    await db.refresh(config)

    return config


# ============================================================================
# MCP Tool Execution Endpoints
# ============================================================================


@router.post("/execute", response_model=MCPToolExecuteResponse)
async def execute_mcp_tool(
    execute_data: MCPToolExecuteRequest,
    tenant: CurrentTenant,
    user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> dict:
    """Execute a tool on an MCP server."""
    # Create MCP client
    client = MCPClient(db=db, tenant_id=tenant.id)

    try:
        # Execute tool
        result = await client.execute_tool(
            server_id=execute_data.server_id,
            tool_name=execute_data.tool_name,
            tool_input=execute_data.tool_input,
            conversation_id=execute_data.conversation_id,
            agent_id=execute_data.agent_id,
        )

        # Get execution record
        execution_result = await db.execute(
            select(MCPToolExecution).where(MCPToolExecution.id == result["execution_id"])
        )
        execution = execution_result.scalar_one()

        return MCPToolExecuteResponse.model_validate(execution)

    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
    finally:
        await client.close_all()


@router.get("/executions", response_model=MCPToolExecutionListResponse)
async def list_mcp_tool_executions(
    tenant: CurrentTenant,
    user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
    server_id: UUID | None = Query(None),
    agent_id: UUID | None = Query(None),
    status: str | None = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
) -> MCPToolExecutionListResponse:
    """List MCP tool execution history."""
    # Build query
    query = select(MCPToolExecution).where(MCPToolExecution.tenant_id == tenant.id)

    if server_id:
        query = query.where(MCPToolExecution.server_id == server_id)

    if agent_id:
        query = query.where(MCPToolExecution.agent_id == agent_id)

    if status:
        query = query.where(MCPToolExecution.status == status)

    # Count total
    count_query = select(func.count()).select_from(query.subquery())
    total = await db.scalar(count_query) or 0

    # Get page of results
    offset = (page - 1) * page_size
    query = query.offset(offset).limit(page_size).order_by(MCPToolExecution.started_at.desc())
    result = await db.execute(query)
    executions = result.scalars().all()

    return MCPToolExecutionListResponse(
        executions=[MCPToolExecutionResponse.model_validate(execution) for execution in executions],
        total=total,
        page=page,
        page_size=page_size,
        has_more=(offset + len(executions)) < total,
    )


@router.get("/executions/{execution_id}", response_model=MCPToolExecutionResponse)
async def get_mcp_tool_execution(
    execution_id: UUID,
    tenant: CurrentTenant,
    user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> MCPToolExecution:
    """Get a specific MCP tool execution."""
    result = await db.execute(
        select(MCPToolExecution).where(
            MCPToolExecution.id == execution_id, MCPToolExecution.tenant_id == tenant.id
        )
    )
    execution = result.scalar_one_or_none()

    if not execution:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tool execution not found")

    return execution


# ============================================================================
# MCP Discovery Endpoints
# ============================================================================


@router.get("/servers/{server_id}/discover", response_model=MCPServerDiscoveryResponse)
async def discover_server_capabilities(
    server_id: UUID,
    tenant: CurrentTenant,
    user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> dict:
    """Discover available tools and resources from an MCP server."""
    # Create MCP client
    client = MCPClient(db=db, tenant_id=tenant.id)

    try:
        # Connect and discover
        process = await client.connect_server(server_id)
        tools = process.get_tools()
        resources = process.get_resources()

        # Get server info
        result = await db.execute(select(MCPServer).where(MCPServer.id == server_id))
        server = result.scalar_one()

        # Update server with discovered tools/resources
        server.tools = tools
        server.resources = resources
        server.last_health_check = datetime.utcnow()
        server.health_status = "healthy"
        await db.commit()

        return MCPServerDiscoveryResponse(
            servers=[
                {
                    "server_id": server_id,
                    "name": server.name,
                    "server_type": server.server_type,
                    "status": server.status,
                    "available_tools": [tool["name"] for tool in tools],
                    "available_resources": [resource.get("name", resource.get("uri", "")) for resource in resources],
                }
            ],
            total_available=1,
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to discover server: {e}"
        )
    finally:
        await client.close_all()


@router.post("/servers/{server_id}/health", response_model=dict)
async def check_server_health(
    server_id: UUID,
    tenant: CurrentTenant,
    user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> dict:
    """Check health of an MCP server."""
    # Create MCP client
    client = MCPClient(db=db, tenant_id=tenant.id)

    try:
        # Check health
        is_healthy = await client.health_check_server(server_id)

        # Update server
        result = await db.execute(
            select(MCPServer).where(MCPServer.id == server_id, MCPServer.tenant_id == tenant.id)
        )
        server = result.scalar_one_or_none()

        if server:
            server.last_health_check = datetime.utcnow()
            server.health_status = "healthy" if is_healthy else "unhealthy"
            await db.commit()

        return {"server_id": server_id, "healthy": is_healthy, "checked_at": datetime.utcnow()}

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Health check failed: {e}"
        )
    finally:
        await client.close_all()
