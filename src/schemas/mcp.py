"""MCP (Model Context Protocol) schemas."""

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field


# ============================================================================
# MCP Server Schemas
# ============================================================================


class MCPToolDefinition(BaseModel):
    """MCP tool definition schema."""

    name: str = Field(..., description="Tool name")
    description: str = Field(..., description="What this tool does")
    inputSchema: dict[str, Any] = Field(..., description="JSON Schema for tool input")


class MCPResourceDefinition(BaseModel):
    """MCP resource definition schema."""

    uri: str = Field(..., description="Resource URI")
    name: str = Field(..., description="Resource name")
    description: str | None = Field(None, description="Resource description")
    mimeType: str | None = Field(None, description="MIME type of resource")


class MCPServerCreate(BaseModel):
    """MCP server creation schema."""

    name: str = Field(..., min_length=1, max_length=255)
    slug: str = Field(..., min_length=1, max_length=100)
    description: str | None = None
    server_type: str = Field(default="stdio", description="stdio, sse, or websocket")
    command: str | None = Field(None, description="Command to start server")
    args: list[str] | None = Field(None, description="Command arguments")
    category: str | None = Field(None, description="Server category")
    author: str | None = None
    tools: list[dict[str, Any]] | None = Field(None, description="Tool definitions")
    resources: list[dict[str, Any]] | None = Field(None, description="Resource definitions")
    prompts: list[dict[str, Any]] | None = Field(None, description="Prompt templates")
    config: dict[str, Any] | None = Field(None, description="Server configuration")
    env_vars: dict[str, Any] | None = Field(None, description="Environment variables")
    visibility: str = Field(default="private", description="private, shared, or public")
    extra_metadata: dict[str, Any] | None = None


class MCPServerUpdate(BaseModel):
    """MCP server update schema."""

    name: str | None = Field(None, min_length=1, max_length=255)
    description: str | None = None
    status: str | None = Field(None, description="Server status")
    command: str | None = None
    args: list[str] | None = None
    tools: list[dict[str, Any]] | None = None
    resources: list[dict[str, Any]] | None = None
    prompts: list[dict[str, Any]] | None = None
    config: dict[str, Any] | None = None
    env_vars: dict[str, Any] | None = None
    visibility: str | None = None
    extra_metadata: dict[str, Any] | None = None


class MCPServerResponse(BaseModel):
    """MCP server response schema."""

    id: UUID
    tenant_id: UUID
    name: str
    slug: str
    description: str | None
    server_type: str
    command: str | None
    args: list[str] | None
    status: str
    version: str
    category: str | None
    author: str | None
    tools: list[dict[str, Any]] | None
    resources: list[dict[str, Any]] | None
    prompts: list[dict[str, Any]] | None
    config: dict[str, Any] | None
    env_vars: dict[str, Any] | None
    last_health_check: datetime | None
    health_status: str | None
    error_message: str | None
    visibility: str
    total_executions: int
    successful_executions: int
    failed_executions: int
    extra_metadata: dict[str, Any] | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class MCPServerListResponse(BaseModel):
    """MCP server list response schema."""

    servers: list[MCPServerResponse]
    total: int
    page: int
    page_size: int
    has_more: bool


# ============================================================================
# MCP Server Config Schemas
# ============================================================================


class MCPServerConfigCreate(BaseModel):
    """MCP server configuration creation schema."""

    server_id: UUID
    agent_id: UUID | None = None
    enabled: bool = True
    config_overrides: dict[str, Any] | None = None
    env_overrides: dict[str, Any] | None = None
    allowed_tools: list[str] | None = Field(None, description="Whitelist of tools (null = all)")
    denied_tools: list[str] | None = Field(None, description="Blacklist of tools")
    timeout_seconds: int = Field(default=30, gt=0)
    max_retries: int = Field(default=3, ge=0)
    rate_limit_per_minute: int | None = Field(None, gt=0)
    extra_metadata: dict[str, Any] | None = None


class MCPServerConfigUpdate(BaseModel):
    """MCP server configuration update schema."""

    enabled: bool | None = None
    config_overrides: dict[str, Any] | None = None
    env_overrides: dict[str, Any] | None = None
    allowed_tools: list[str] | None = None
    denied_tools: list[str] | None = None
    timeout_seconds: int | None = Field(None, gt=0)
    max_retries: int | None = Field(None, ge=0)
    rate_limit_per_minute: int | None = Field(None, gt=0)
    extra_metadata: dict[str, Any] | None = None


class MCPServerConfigResponse(BaseModel):
    """MCP server configuration response schema."""

    id: UUID
    tenant_id: UUID
    server_id: UUID
    agent_id: UUID | None
    enabled: bool
    config_overrides: dict[str, Any] | None
    env_overrides: dict[str, Any] | None
    allowed_tools: list[str] | None
    denied_tools: list[str] | None
    timeout_seconds: int
    max_retries: int
    rate_limit_per_minute: int | None
    extra_metadata: dict[str, Any] | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


# ============================================================================
# MCP Tool Execution Schemas
# ============================================================================


class MCPToolExecuteRequest(BaseModel):
    """MCP tool execution request schema."""

    server_id: UUID
    tool_name: str = Field(..., min_length=1)
    tool_input: dict[str, Any] = Field(default_factory=dict)
    conversation_id: UUID | None = None
    agent_id: UUID | None = None
    timeout_seconds: int | None = Field(None, gt=0)


class MCPToolExecuteResponse(BaseModel):
    """MCP tool execution response schema."""

    execution_id: UUID
    server_id: UUID
    tool_name: str
    status: str
    tool_output: dict[str, Any] | None
    error_message: str | None
    error_code: str | None
    execution_time_ms: int | None
    started_at: datetime
    completed_at: datetime | None

    model_config = {"from_attributes": True}


class MCPToolExecutionResponse(BaseModel):
    """MCP tool execution history response schema."""

    id: UUID
    tenant_id: UUID
    server_id: UUID
    conversation_id: UUID | None
    message_id: UUID | None
    agent_id: UUID | None
    tool_name: str
    tool_input: dict[str, Any] | None
    tool_output: dict[str, Any] | None
    status: str
    error_message: str | None
    error_code: str | None
    execution_time_ms: int | None
    server_response_time_ms: int | None
    retry_count: int
    is_retry: bool
    parent_execution_id: UUID | None
    extra_metadata: dict[str, Any] | None
    started_at: datetime
    completed_at: datetime | None

    model_config = {"from_attributes": True}


class MCPToolExecutionListResponse(BaseModel):
    """MCP tool execution list response schema."""

    executions: list[MCPToolExecutionResponse]
    total: int
    page: int
    page_size: int
    has_more: bool


# ============================================================================
# MCP Server Registry Schemas
# ============================================================================


class MCPRegistryServerCreate(BaseModel):
    """MCP registry server creation schema."""

    name: str = Field(..., min_length=1, max_length=255)
    slug: str = Field(..., min_length=1, max_length=100)
    description: str | None = None
    long_description: str | None = None
    server_type: str = Field(..., description="stdio, sse, or websocket")
    category: str = Field(..., min_length=1, max_length=100)
    tags: list[str] | None = None
    version: str = Field(default="1.0.0")
    install_command: str | None = None
    configuration_schema: dict[str, Any] | None = None
    author: str = Field(..., min_length=1, max_length=255)
    repository_url: str | None = Field(None, max_length=1000)
    documentation_url: str | None = Field(None, max_length=1000)
    homepage_url: str | None = Field(None, max_length=1000)
    license: str | None = Field(None, max_length=100)
    tool_definitions: list[dict[str, Any]] | None = None
    resource_definitions: list[dict[str, Any]] | None = None
    extra_metadata: dict[str, Any] | None = None


class MCPRegistryServerUpdate(BaseModel):
    """MCP registry server update schema."""

    description: str | None = None
    long_description: str | None = None
    tags: list[str] | None = None
    version: str | None = None
    install_command: str | None = None
    configuration_schema: dict[str, Any] | None = None
    repository_url: str | None = None
    documentation_url: str | None = None
    homepage_url: str | None = None
    license: str | None = None
    status: str | None = None
    tool_definitions: list[dict[str, Any]] | None = None
    resource_definitions: list[dict[str, Any]] | None = None
    extra_metadata: dict[str, Any] | None = None


class MCPRegistryServerResponse(BaseModel):
    """MCP registry server response schema."""

    id: UUID
    name: str
    slug: str
    description: str | None
    long_description: str | None
    server_type: str
    category: str
    tags: list[str] | None
    version: str
    install_command: str | None
    configuration_schema: dict[str, Any] | None
    author: str
    repository_url: str | None
    documentation_url: str | None
    homepage_url: str | None
    license: str | None
    status: str
    visibility: str
    install_count: int
    usage_count: int
    star_count: int
    average_rating: float | None
    rating_count: int
    is_featured: bool
    is_official: bool
    tool_definitions: list[dict[str, Any]] | None
    resource_definitions: list[dict[str, Any]] | None
    extra_metadata: dict[str, Any] | None
    published_at: datetime | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class MCPRegistryServerListResponse(BaseModel):
    """MCP registry server list response schema."""

    servers: list[MCPRegistryServerResponse]
    total: int
    page: int
    page_size: int
    has_more: bool


# ============================================================================
# MCP Discovery Schemas
# ============================================================================


class MCPServerConnectionInfo(BaseModel):
    """MCP server connection information."""

    server_id: UUID
    name: str
    server_type: str
    status: str
    available_tools: list[str]
    available_resources: list[str]


class MCPServerDiscoveryResponse(BaseModel):
    """MCP server discovery response schema."""

    servers: list[MCPServerConnectionInfo]
    total_available: int
