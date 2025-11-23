"""Conversation schemas."""

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel


class MessageResponse(BaseModel):
    """Message response schema."""

    id: UUID
    role: str
    content: str
    created_at: datetime
    token_count: int | None = None
    tool_calls: list[dict[str, Any]] | None = None

    model_config = {"from_attributes": True}


class ConversationResponse(BaseModel):
    """Conversation response schema."""

    id: UUID
    agent_id: UUID
    agent_name: str | None = None
    user_id: UUID | None = None
    title: str | None = None
    status: str
    messages: list[MessageResponse] | None = None
    context: dict[str, Any] | None = None
    extra_metadata: dict[str, Any] | None = None
    started_at: datetime
    completed_at: datetime | None = None

    model_config = {"from_attributes": True}


class ConversationListResponse(BaseModel):
    """Conversation list response schema."""

    data: list[ConversationResponse]
    pagination: dict[str, Any]
