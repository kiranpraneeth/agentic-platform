"""Conversation endpoints."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.api.dependencies import CurrentTenant, CurrentUser
from src.db.models import Agent, Conversation, Message
from src.db.session import get_db
from src.schemas.conversation import (
    ConversationListResponse,
    ConversationResponse,
    MessageResponse,
)

router = APIRouter()


@router.get("", response_model=ConversationListResponse)
async def list_conversations(
    tenant: CurrentTenant,
    user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    agent_id: UUID | None = Query(None),
    status: str | None = Query(None),
) -> ConversationListResponse:
    """List conversations."""
    # Build query
    query = select(Conversation).where(Conversation.tenant_id == tenant.id)

    if agent_id:
        query = query.where(Conversation.agent_id == agent_id)

    if status:
        query = query.where(Conversation.status == status)

    # Count total
    count_query = select(func.count()).select_from(query.subquery())
    total = await db.scalar(count_query) or 0

    # Get page of results
    offset = (page - 1) * limit
    query = (
        query.options(selectinload(Conversation.agent))
        .offset(offset)
        .limit(limit)
        .order_by(Conversation.started_at.desc())
    )
    result = await db.execute(query)
    conversations = result.scalars().all()

    # Format response
    data = []
    for conv in conversations:
        data.append(
            ConversationResponse(
                id=conv.id,
                agent_id=conv.agent_id,
                agent_name=conv.agent.name if conv.agent else None,
                user_id=conv.user_id,
                title=conv.title,
                status=conv.status,
                context=conv.context,
                metadata=conv.metadata,
                started_at=conv.started_at,
                completed_at=conv.completed_at,
            )
        )

    return ConversationListResponse(
        data=data,
        pagination={
            "page": page,
            "limit": limit,
            "total": total,
            "total_pages": (total + limit - 1) // limit,
        },
    )


@router.get("/{conversation_id}", response_model=ConversationResponse)
async def get_conversation(
    conversation_id: UUID,
    tenant: CurrentTenant,
    user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> ConversationResponse:
    """Get conversation details with messages."""
    result = await db.execute(
        select(Conversation)
        .options(selectinload(Conversation.agent), selectinload(Conversation.messages))
        .where(Conversation.id == conversation_id, Conversation.tenant_id == tenant.id)
    )
    conversation = result.scalar_one_or_none()

    if not conversation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found",
        )

    # Sort messages by sequence number
    messages_sorted = sorted(conversation.messages, key=lambda m: m.sequence_number)

    return ConversationResponse(
        id=conversation.id,
        agent_id=conversation.agent_id,
        agent_name=conversation.agent.name if conversation.agent else None,
        user_id=conversation.user_id,
        title=conversation.title,
        status=conversation.status,
        messages=[MessageResponse.model_validate(msg) for msg in messages_sorted],
        context=conversation.context,
        metadata=conversation.metadata,
        started_at=conversation.started_at,
        completed_at=conversation.completed_at,
    )


@router.delete("/{conversation_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_conversation(
    conversation_id: UUID,
    tenant: CurrentTenant,
    user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> None:
    """Delete a conversation."""
    result = await db.execute(
        select(Conversation).where(
            Conversation.id == conversation_id, Conversation.tenant_id == tenant.id
        )
    )
    conversation = result.scalar_one_or_none()

    if not conversation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found",
        )

    await db.delete(conversation)
    await db.commit()
