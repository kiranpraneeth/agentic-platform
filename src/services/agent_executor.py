"""Agent execution service."""

import time
from datetime import datetime
from typing import Any

from anthropic import Anthropic
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.config import settings
from src.db.models import Agent, Conversation, Message
from src.schemas.agent import AgentExecuteResponse, TokenUsage


class AgentExecutor:
    """Executes agents with LLM integration."""

    def __init__(self, agent: Agent, db: AsyncSession):
        """Initialize agent executor."""
        self.agent = agent
        self.db = db

        # Initialize LLM client based on provider
        if agent.model_provider == "anthropic":
            if not settings.ANTHROPIC_API_KEY:
                raise ValueError("ANTHROPIC_API_KEY not configured")
            self.client = Anthropic(api_key=settings.ANTHROPIC_API_KEY)
        elif agent.model_provider == "openai":
            if not settings.OPENAI_API_KEY:
                raise ValueError("OPENAI_API_KEY not configured")
            # OpenAI client would be initialized here
            raise NotImplementedError("OpenAI provider not yet implemented")
        else:
            raise ValueError(f"Unsupported model provider: {agent.model_provider}")

    async def execute(
        self,
        input_text: str,
        conversation: Conversation,
        max_iterations: int | None = None,
    ) -> AgentExecuteResponse:
        """Execute agent with given input."""
        start_time = time.time()

        # Get conversation history
        conversation_history = await self._get_conversation_history(conversation.id)

        # Add user message to conversation
        user_message = await self._save_message(
            conversation=conversation,
            role="user",
            content=input_text,
            sequence_number=len(conversation_history),
        )

        # Execute agent
        if self.agent.model_provider == "anthropic":
            response = await self._execute_anthropic(input_text, conversation_history)
        else:
            raise NotImplementedError(f"Provider {self.agent.model_provider} not implemented")

        # Calculate latency
        latency_ms = int((time.time() - start_time) * 1000)

        # Save assistant message
        assistant_message = await self._save_message(
            conversation=conversation,
            role="assistant",
            content=response["content"],
            sequence_number=len(conversation_history) + 1,
            model_used=self.agent.model_name,
            token_count=response.get("token_usage", {}).get("output_tokens"),
            tool_calls=response.get("tool_calls"),
            latency_ms=latency_ms,
        )

        # Update conversation status
        conversation.status = "completed"
        conversation.completed_at = datetime.utcnow()
        await self.db.commit()

        return AgentExecuteResponse(
            conversation_id=conversation.id,
            message_id=assistant_message.id,
            response=response["content"],
            tool_calls=response.get("tool_calls"),
            token_usage=TokenUsage(**response["token_usage"])
            if response.get("token_usage")
            else None,
            latency_ms=latency_ms,
            created_at=assistant_message.created_at,
        )

    async def _execute_anthropic(
        self, input_text: str, conversation_history: list[dict[str, Any]]
    ) -> dict[str, Any]:
        """Execute using Anthropic Claude."""
        # Build messages for Claude
        messages = []
        for msg in conversation_history:
            if msg["role"] in ["user", "assistant"]:
                messages.append({"role": msg["role"], "content": msg["content"]})

        # Add current user message
        messages.append({"role": "user", "content": input_text})

        # Call Claude API
        response = self.client.messages.create(
            model=self.agent.model_name,
            max_tokens=self.agent.max_tokens or 4096,
            temperature=self.agent.temperature or 0.7,
            system=self.agent.system_prompt or "You are a helpful AI assistant.",
            messages=messages,
        )

        # Extract content
        content = ""
        if response.content:
            for block in response.content:
                if hasattr(block, "text"):
                    content += block.text

        return {
            "content": content,
            "token_usage": {
                "input_tokens": response.usage.input_tokens,
                "output_tokens": response.usage.output_tokens,
                "total_tokens": response.usage.input_tokens + response.usage.output_tokens,
            },
            "tool_calls": None,  # Tool calls to be implemented
        }

    async def _get_conversation_history(self, conversation_id: Any) -> list[dict[str, Any]]:
        """Get conversation history."""
        result = await self.db.execute(
            select(Message)
            .where(Message.conversation_id == conversation_id)
            .order_by(Message.sequence_number)
        )
        messages = result.scalars().all()

        return [
            {
                "role": msg.role,
                "content": msg.content,
                "tool_calls": msg.tool_calls,
            }
            for msg in messages
        ]

    async def _save_message(
        self,
        conversation: Conversation,
        role: str,
        content: str,
        sequence_number: int,
        model_used: str | None = None,
        token_count: int | None = None,
        tool_calls: list[dict[str, Any]] | None = None,
        latency_ms: int | None = None,
    ) -> Message:
        """Save message to database."""
        message = Message(
            tenant_id=conversation.tenant_id,
            conversation_id=conversation.id,
            role=role,
            content=content,
            sequence_number=sequence_number,
            model_used=model_used,
            token_count=token_count,
            tool_calls=tool_calls,
            latency_ms=latency_ms,
        )
        self.db.add(message)
        await self.db.commit()
        await self.db.refresh(message)
        return message
