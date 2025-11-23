"""Agent schemas."""

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field


class AgentCreate(BaseModel):
    """Agent creation schema."""

    name: str = Field(..., min_length=1, max_length=255)
    slug: str = Field(..., min_length=1, max_length=100)
    description: str | None = None
    model_provider: str = Field(default="anthropic")
    model_name: str = Field(default="claude-sonnet-4-5")
    system_prompt: str | None = None
    temperature: float | None = Field(default=0.7, ge=0.0, le=2.0)
    max_tokens: int | None = Field(default=4096, gt=0)
    capabilities: list[str] | None = None
    tools: list[str] | None = None
    timeout_seconds: int = Field(default=300, gt=0)
    max_iterations: int = Field(default=10, gt=0)
    memory_enabled: bool = True
    tags: list[str] | None = None
    config: dict[str, Any] | None = None
    extra_metadata: dict[str, Any] | None = None


class AgentUpdate(BaseModel):
    """Agent update schema."""

    name: str | None = Field(None, min_length=1, max_length=255)
    description: str | None = None
    system_prompt: str | None = None
    temperature: float | None = Field(None, ge=0.0, le=2.0)
    max_tokens: int | None = Field(None, gt=0)
    tools: list[str] | None = None
    timeout_seconds: int | None = Field(None, gt=0)
    max_iterations: int | None = Field(None, gt=0)
    memory_enabled: bool | None = None
    status: str | None = None
    tags: list[str] | None = None
    config: dict[str, Any] | None = None
    extra_metadata: dict[str, Any] | None = None


class AgentResponse(BaseModel):
    """Agent response schema."""

    id: UUID
    tenant_id: UUID
    name: str
    slug: str
    description: str | None
    status: str
    model_provider: str
    model_name: str
    system_prompt: str | None
    temperature: float | None
    max_tokens: int | None
    capabilities: list[str] | None
    tools: list[str] | None
    timeout_seconds: int
    max_iterations: int
    memory_enabled: bool
    version: str
    tags: list[str] | None
    config: dict[str, Any] | None
    extra_metadata: dict[str, Any] | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class AgentListResponse(BaseModel):
    """Agent list response schema."""

    data: list[AgentResponse]
    pagination: dict[str, Any]


class AgentExecuteRequest(BaseModel):
    """Agent execution request schema."""

    input: str = Field(..., min_length=1)
    conversation_id: UUID | None = None
    context: dict[str, Any] | None = None
    stream: bool = False
    max_iterations: int | None = Field(None, gt=0)


class ToolCall(BaseModel):
    """Tool call schema."""

    tool: str
    input: dict[str, Any]
    output: dict[str, Any] | None = None


class TokenUsage(BaseModel):
    """Token usage schema."""

    input_tokens: int
    output_tokens: int
    total_tokens: int


class AgentExecuteResponse(BaseModel):
    """Agent execution response schema."""

    conversation_id: UUID
    message_id: UUID
    response: str
    tool_calls: list[ToolCall] | None = None
    token_usage: TokenUsage | None = None
    latency_ms: int | None = None
    created_at: datetime
