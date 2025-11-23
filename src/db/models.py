"""Database models based on database-schema.md."""

import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import JSON, Boolean, DateTime, Float, ForeignKey, Index, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from pgvector.sqlalchemy import Vector

from src.db.base import Base, SoftDeleteMixin, TimestampMixin, UUIDMixin


class Tenant(Base, UUIDMixin, TimestampMixin, SoftDeleteMixin):
    """Tenant/Organization model."""

    __tablename__ = "tenants"

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    slug: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)
    status: Mapped[str] = mapped_column(
        String(50), nullable=False, default="active", index=True
    )  # active, suspended, deleted
    plan_type: Mapped[str] = mapped_column(
        String(50), nullable=False, default="free"
    )  # free, starter, pro, enterprise
    email: Mapped[str] = mapped_column(String(255), nullable=False)
    contact_name: Mapped[str | None] = mapped_column(String(255), nullable=True)

    # Resource limits
    max_agents: Mapped[int] = mapped_column(Integer, default=3)
    max_requests_per_day: Mapped[int] = mapped_column(Integer, default=1000)
    max_tokens_per_month: Mapped[int] = mapped_column(Integer, default=100000)

    # JSONB fields
    settings: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    extra_metadata: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)

    # Relationships
    users: Mapped[list["User"]] = relationship(back_populates="tenant", cascade="all, delete")
    agents: Mapped[list["Agent"]] = relationship(back_populates="tenant", cascade="all, delete")
    conversations: Mapped[list["Conversation"]] = relationship(
        back_populates="tenant", cascade="all, delete"
    )

    __table_args__ = (Index("idx_tenants_status_deleted", "status", "deleted_at"),)


class User(Base, UUIDMixin, TimestampMixin, SoftDeleteMixin):
    """User model."""

    __tablename__ = "users"

    tenant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True
    )
    email: Mapped[str] = mapped_column(String(255), nullable=False)
    username: Mapped[str | None] = mapped_column(String(100), nullable=True)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    first_name: Mapped[str | None] = mapped_column(String(100), nullable=True)
    last_name: Mapped[str | None] = mapped_column(String(100), nullable=True)
    avatar_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    status: Mapped[str] = mapped_column(
        String(50), nullable=False, default="active", index=True
    )  # active, inactive, suspended
    email_verified: Mapped[bool] = mapped_column(Boolean, default=False)
    last_login_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    role: Mapped[str] = mapped_column(
        String(50), nullable=False, default="user"
    )  # admin, user, viewer

    # JSONB fields
    permissions: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    extra_metadata: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)

    # Relationships
    tenant: Mapped["Tenant"] = relationship(back_populates="users")
    conversations: Mapped[list["Conversation"]] = relationship(back_populates="user")
    api_keys: Mapped[list["APIKey"]] = relationship(back_populates="user")

    __table_args__ = (
        Index("idx_users_tenant_email", "tenant_id", "email", unique=True),
        Index("idx_users_tenant_status", "tenant_id", "status"),
    )


class Agent(Base, UUIDMixin, TimestampMixin, SoftDeleteMixin):
    """Agent model."""

    __tablename__ = "agents"

    tenant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    slug: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(
        String(50), nullable=False, default="active", index=True
    )  # active, inactive, archived

    # Model configuration
    model_provider: Mapped[str] = mapped_column(
        String(50), nullable=False, default="anthropic"
    )  # anthropic, openai
    model_name: Mapped[str] = mapped_column(String(100), nullable=False, default="claude-sonnet-4-5")
    system_prompt: Mapped[str | None] = mapped_column(Text, nullable=True)
    temperature: Mapped[float | None] = mapped_column(nullable=True, default=0.7)
    max_tokens: Mapped[int | None] = mapped_column(Integer, nullable=True, default=4096)

    # Capabilities and tools
    capabilities: Mapped[list[str] | None] = mapped_column(JSON, nullable=True)
    tools: Mapped[list[str] | None] = mapped_column(JSON, nullable=True)

    # Resource limits
    timeout_seconds: Mapped[int] = mapped_column(Integer, default=300)
    max_iterations: Mapped[int] = mapped_column(Integer, default=10)
    memory_enabled: Mapped[bool] = mapped_column(Boolean, default=True)

    # Version and metadata
    version: Mapped[str] = mapped_column(String(50), nullable=False, default="1.0.0")
    tags: Mapped[list[str] | None] = mapped_column(JSON, nullable=True)
    config: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    extra_metadata: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)

    # Relationships
    tenant: Mapped["Tenant"] = relationship(back_populates="agents")
    conversations: Mapped[list["Conversation"]] = relationship(back_populates="agent")
    tool_executions: Mapped[list["ToolExecution"]] = relationship(back_populates="agent")

    __table_args__ = (
        Index("idx_agents_tenant_slug", "tenant_id", "slug", unique=True),
        Index("idx_agents_tenant_status", "tenant_id", "status"),
    )


class Conversation(Base, UUIDMixin, TimestampMixin):
    """Conversation model."""

    __tablename__ = "conversations"

    tenant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True
    )
    agent_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("agents.id", ondelete="CASCADE"), nullable=False, index=True
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True
    )

    title: Mapped[str | None] = mapped_column(String(500), nullable=True)
    status: Mapped[str] = mapped_column(
        String(50), nullable=False, default="active", index=True
    )  # active, completed, failed, cancelled

    # JSONB fields
    context: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    extra_metadata: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)

    # Timestamps
    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, index=True, server_default="now()"
    )
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # Relationships
    tenant: Mapped["Tenant"] = relationship(back_populates="conversations")
    agent: Mapped["Agent"] = relationship(back_populates="conversations")
    user: Mapped["User"] = relationship(back_populates="conversations")
    messages: Mapped[list["Message"]] = relationship(
        back_populates="conversation", cascade="all, delete"
    )

    __table_args__ = (
        Index("idx_conversations_tenant_agent", "tenant_id", "agent_id"),
        Index("idx_conversations_started_at", "started_at", postgresql_using="btree"),
    )


class Message(Base, UUIDMixin):
    """Message model."""

    __tablename__ = "messages"

    tenant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True
    )
    conversation_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("conversations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    role: Mapped[str] = mapped_column(
        String(50), nullable=False
    )  # user, assistant, system, tool
    content: Mapped[str] = mapped_column(Text, nullable=False)
    token_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    model_used: Mapped[str | None] = mapped_column(String(100), nullable=True)
    sequence_number: Mapped[int] = mapped_column(Integer, nullable=False)

    # Tool calls and results
    tool_calls: Mapped[list[dict[str, Any]] | None] = mapped_column(JSON, nullable=True)
    tool_results: Mapped[list[dict[str, Any]] | None] = mapped_column(JSON, nullable=True)

    # Performance
    latency_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)

    # JSONB metadata
    extra_metadata: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, index=True, server_default="now()"
    )

    # Relationships
    conversation: Mapped["Conversation"] = relationship(back_populates="messages")
    tool_executions: Mapped[list["ToolExecution"]] = relationship(back_populates="message")

    __table_args__ = (
        Index("idx_messages_conversation_sequence", "conversation_id", "sequence_number"),
        Index("idx_messages_created_at", "created_at", postgresql_using="btree"),
    )


class ToolExecution(Base, UUIDMixin):
    """Tool execution model."""

    __tablename__ = "tool_executions"

    tenant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True
    )
    conversation_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("conversations.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )
    message_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("messages.id", ondelete="CASCADE"), nullable=True, index=True
    )
    agent_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("agents.id", ondelete="CASCADE"), nullable=True, index=True
    )

    tool_name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    tool_input: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    tool_output: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    status: Mapped[str] = mapped_column(
        String(50), nullable=False, index=True
    )  # success, error, timeout
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    execution_time_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)

    # JSONB metadata
    extra_metadata: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)

    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, index=True, server_default="now()"
    )
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # Relationships
    agent: Mapped["Agent"] = relationship(back_populates="tool_executions")
    message: Mapped["Message"] = relationship(back_populates="tool_executions")

    __table_args__ = (
        Index("idx_tool_executions_tenant_tool", "tenant_id", "tool_name"),
        Index("idx_tool_executions_started_at", "started_at", postgresql_using="btree"),
    )


class APIKey(Base, UUIDMixin, TimestampMixin):
    """API Key model."""

    __tablename__ = "api_keys"

    tenant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    key_hash: Mapped[str] = mapped_column(String(255), nullable=False, unique=True, index=True)
    key_prefix: Mapped[str] = mapped_column(String(20), nullable=False)
    scopes: Mapped[list[str] | None] = mapped_column(JSON, nullable=True)
    status: Mapped[str] = mapped_column(
        String(50), nullable=False, default="active", index=True
    )  # active, revoked, expired

    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    last_used_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # JSONB metadata
    extra_metadata: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)

    # Relationships
    user: Mapped["User"] = relationship(back_populates="api_keys")

    __table_args__ = (Index("idx_api_keys_tenant_status", "tenant_id", "status"),)


class AuditLog(Base, UUIDMixin):
    """Audit log model."""

    __tablename__ = "audit_logs"

    tenant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True
    )
    user_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True
    )

    action: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    resource_type: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    resource_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)

    old_values: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    new_values: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)

    ip_address: Mapped[str | None] = mapped_column(String(45), nullable=True)
    user_agent: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(50), nullable=False)  # success, failure
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)

    # JSONB metadata
    extra_metadata: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)

    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, index=True, server_default="now()"
    )

    __table_args__ = (
        Index("idx_audit_logs_tenant_action", "tenant_id", "action"),
        Index("idx_audit_logs_timestamp", "timestamp", postgresql_using="btree"),
    )


class Collection(Base, UUIDMixin, TimestampMixin, SoftDeleteMixin):
    """Knowledge base collection model."""

    __tablename__ = "collections"

    tenant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Embedding configuration
    embedding_model: Mapped[str] = mapped_column(
        String(100), nullable=False, default="all-MiniLM-L6-v2"
    )
    embedding_dimensions: Mapped[int] = mapped_column(Integer, nullable=False, default=384)

    # Collection settings
    chunk_size: Mapped[int] = mapped_column(Integer, default=512)
    chunk_overlap: Mapped[int] = mapped_column(Integer, default=50)

    # Access control
    visibility: Mapped[str] = mapped_column(
        String(50), nullable=False, default="private"
    )  # private, shared, public

    # Statistics
    document_count: Mapped[int] = mapped_column(Integer, default=0)
    chunk_count: Mapped[int] = mapped_column(Integer, default=0)

    # JSONB metadata
    config: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    extra_metadata: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)

    # Relationships
    documents: Mapped[list["Document"]] = relationship(
        back_populates="collection", cascade="all, delete"
    )

    __table_args__ = (
        Index("idx_collections_tenant_name", "tenant_id", "name"),
        Index("idx_collections_visibility", "visibility"),
    )


class Document(Base, UUIDMixin, TimestampMixin, SoftDeleteMixin):
    """Document model for RAG."""

    __tablename__ = "documents"

    tenant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True
    )
    collection_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("collections.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    title: Mapped[str] = mapped_column(String(500), nullable=False)
    source: Mapped[str | None] = mapped_column(String(1000), nullable=True)  # filename or URL
    content_type: Mapped[str] = mapped_column(
        String(100), nullable=False
    )  # pdf, docx, txt, md, html, json, csv

    # Processing status
    status: Mapped[str] = mapped_column(
        String(50), nullable=False, default="pending", index=True
    )  # pending, processing, completed, failed

    # File information
    file_size_bytes: Mapped[int | None] = mapped_column(Integer, nullable=True)
    file_hash: Mapped[str | None] = mapped_column(String(64), nullable=True)  # SHA-256
    storage_path: Mapped[str | None] = mapped_column(String(1000), nullable=True)

    # Processing metadata
    chunk_count: Mapped[int] = mapped_column(Integer, default=0)
    total_tokens: Mapped[int | None] = mapped_column(Integer, nullable=True)
    processed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)

    # JSONB metadata
    extra_metadata: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)

    # Relationships
    collection: Mapped["Collection"] = relationship(back_populates="documents")
    chunks: Mapped[list["Chunk"]] = relationship(back_populates="document", cascade="all, delete")

    __table_args__ = (
        Index("idx_documents_collection_status", "collection_id", "status"),
        Index("idx_documents_tenant_collection", "tenant_id", "collection_id"),
    )


class Chunk(Base, UUIDMixin):
    """Document chunk with vector embedding."""

    __tablename__ = "chunks"

    tenant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True
    )
    document_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("documents.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    collection_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("collections.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    content: Mapped[str] = mapped_column(Text, nullable=False)
    embedding: Mapped[Any] = mapped_column(Vector(1536), nullable=True)  # pgvector type

    # Chunk metadata
    sequence_number: Mapped[int] = mapped_column(Integer, nullable=False)
    token_count: Mapped[int | None] = mapped_column(Integer, nullable=True)

    # Source location in document
    start_char: Mapped[int | None] = mapped_column(Integer, nullable=True)
    end_char: Mapped[int | None] = mapped_column(Integer, nullable=True)
    page_number: Mapped[int | None] = mapped_column(Integer, nullable=True)
    section: Mapped[str | None] = mapped_column(String(255), nullable=True)

    # JSONB metadata
    extra_metadata: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, index=True, server_default="now()"
    )

    # Relationships
    document: Mapped["Document"] = relationship(back_populates="chunks")

    __table_args__ = (
        Index("idx_chunks_document_sequence", "document_id", "sequence_number"),
        Index("idx_chunks_collection", "collection_id"),
        # Vector similarity index (HNSW for fast approximate search)
        Index(
            "idx_chunks_embedding_hnsw",
            "embedding",
            postgresql_using="hnsw",
            postgresql_with={"m": 16, "ef_construction": 64},
            postgresql_ops={"embedding": "vector_cosine_ops"},
        ),
    )


class RAGQuery(Base, UUIDMixin):
    """RAG query log for analytics."""

    __tablename__ = "rag_queries"

    tenant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True
    )
    collection_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("collections.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )
    conversation_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("conversations.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    query_text: Mapped[str] = mapped_column(Text, nullable=False)
    query_embedding: Mapped[Any] = mapped_column(Vector(1536), nullable=True)

    # Retrieval parameters
    top_k: Mapped[int] = mapped_column(Integer, default=5)
    similarity_threshold: Mapped[float | None] = mapped_column(Float, nullable=True)
    metadata_filter: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)

    # Results
    result_count: Mapped[int] = mapped_column(Integer, default=0)
    results: Mapped[list[dict[str, Any]] | None] = mapped_column(JSON, nullable=True)

    # Performance
    retrieval_time_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)

    # User feedback
    feedback_score: Mapped[int | None] = mapped_column(Integer, nullable=True)  # 1-5 rating
    feedback_text: Mapped[str | None] = mapped_column(Text, nullable=True)

    # JSONB metadata
    extra_metadata: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, index=True, server_default="now()"
    )

    __table_args__ = (
        Index("idx_rag_queries_tenant_collection", "tenant_id", "collection_id"),
        Index("idx_rag_queries_created_at", "created_at", postgresql_using="btree"),
    )


# ============================================================================
# MCP (Model Context Protocol) Models
# ============================================================================


class MCPServer(Base, UUIDMixin, TimestampMixin, SoftDeleteMixin):
    """MCP Server model for managing Model Context Protocol servers."""

    __tablename__ = "mcp_servers"

    tenant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True
    )

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    slug: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Server type and connection
    server_type: Mapped[str] = mapped_column(
        String(50), nullable=False, default="stdio"
    )  # stdio, sse, websocket
    command: Mapped[str | None] = mapped_column(String(500), nullable=True)  # Command to start server
    args: Mapped[list[str] | None] = mapped_column(JSON, nullable=True)  # Command arguments

    # Server status
    status: Mapped[str] = mapped_column(
        String(50), nullable=False, default="inactive", index=True
    )  # inactive, starting, ready, running, unhealthy, stopped, failed

    # Version and metadata
    version: Mapped[str] = mapped_column(String(50), nullable=False, default="1.0.0")
    category: Mapped[str | None] = mapped_column(
        String(100), nullable=True
    )  # system, data, api, code, etc.
    author: Mapped[str | None] = mapped_column(String(255), nullable=True)

    # Available tools/resources
    tools: Mapped[list[dict[str, Any]] | None] = mapped_column(
        JSON, nullable=True
    )  # Tool definitions
    resources: Mapped[list[dict[str, Any]] | None] = mapped_column(
        JSON, nullable=True
    )  # Resource definitions
    prompts: Mapped[list[dict[str, Any]] | None] = mapped_column(JSON, nullable=True)  # Prompt templates

    # Configuration
    config: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)  # Server configuration
    env_vars: Mapped[dict[str, Any] | None] = mapped_column(
        JSON, nullable=True
    )  # Environment variables

    # Health and monitoring
    last_health_check: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    health_status: Mapped[str | None] = mapped_column(String(50), nullable=True)  # healthy, unhealthy
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Access control
    visibility: Mapped[str] = mapped_column(
        String(50), nullable=False, default="private"
    )  # private, shared, public

    # Usage statistics
    total_executions: Mapped[int] = mapped_column(Integer, default=0)
    successful_executions: Mapped[int] = mapped_column(Integer, default=0)
    failed_executions: Mapped[int] = mapped_column(Integer, default=0)

    # JSONB metadata
    extra_metadata: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)

    # Relationships
    configs: Mapped[list["MCPServerConfig"]] = relationship(
        back_populates="server", cascade="all, delete"
    )
    tool_executions: Mapped[list["MCPToolExecution"]] = relationship(
        back_populates="server", cascade="all, delete"
    )

    __table_args__ = (
        Index("idx_mcp_servers_tenant_slug", "tenant_id", "slug", unique=True),
        Index("idx_mcp_servers_status", "status"),
        Index("idx_mcp_servers_category", "category"),
    )


class MCPServerConfig(Base, UUIDMixin, TimestampMixin):
    """Tenant-specific MCP server configuration."""

    __tablename__ = "mcp_server_configs"

    tenant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True
    )
    server_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("mcp_servers.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    agent_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("agents.id", ondelete="CASCADE"), nullable=True, index=True
    )

    # Configuration
    enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    config_overrides: Mapped[dict[str, Any] | None] = mapped_column(
        JSON, nullable=True
    )  # Override server config
    env_overrides: Mapped[dict[str, Any] | None] = mapped_column(
        JSON, nullable=True
    )  # Override env vars

    # Access permissions
    allowed_tools: Mapped[list[str] | None] = mapped_column(
        JSON, nullable=True
    )  # Whitelist of tools (null = all)
    denied_tools: Mapped[list[str] | None] = mapped_column(JSON, nullable=True)  # Blacklist of tools

    # Resource limits
    timeout_seconds: Mapped[int] = mapped_column(Integer, default=30)
    max_retries: Mapped[int] = mapped_column(Integer, default=3)
    rate_limit_per_minute: Mapped[int | None] = mapped_column(Integer, nullable=True)

    # JSONB metadata
    extra_metadata: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)

    # Relationships
    server: Mapped["MCPServer"] = relationship(back_populates="configs")

    __table_args__ = (
        Index("idx_mcp_configs_tenant_server", "tenant_id", "server_id"),
        Index("idx_mcp_configs_agent", "agent_id"),
    )


class MCPToolExecution(Base, UUIDMixin):
    """MCP tool execution log for monitoring and debugging."""

    __tablename__ = "mcp_tool_executions"

    tenant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True
    )
    server_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("mcp_servers.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    conversation_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("conversations.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )
    message_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("messages.id", ondelete="CASCADE"), nullable=True, index=True
    )
    agent_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("agents.id", ondelete="CASCADE"), nullable=True, index=True
    )

    # Tool execution details
    tool_name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    tool_input: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    tool_output: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)

    # Execution status
    status: Mapped[str] = mapped_column(
        String(50), nullable=False, index=True
    )  # success, error, timeout, rejected
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    error_code: Mapped[str | None] = mapped_column(String(100), nullable=True)

    # Performance metrics
    execution_time_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    server_response_time_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)

    # Retry information
    retry_count: Mapped[int] = mapped_column(Integer, default=0)
    is_retry: Mapped[bool] = mapped_column(Boolean, default=False)
    parent_execution_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)

    # JSONB metadata
    extra_metadata: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)

    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, index=True, server_default="now()"
    )
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # Relationships
    server: Mapped["MCPServer"] = relationship(back_populates="tool_executions")

    __table_args__ = (
        Index("idx_mcp_executions_tenant_server", "tenant_id", "server_id"),
        Index("idx_mcp_executions_tool", "tool_name"),
        Index("idx_mcp_executions_status", "status"),
        Index("idx_mcp_executions_started_at", "started_at", postgresql_using="btree"),
    )


class MCPServerRegistry(Base, UUIDMixin, TimestampMixin):
    """Public MCP server registry for marketplace/catalog."""

    __tablename__ = "mcp_server_registry"

    # Server information
    name: Mapped[str] = mapped_column(String(255), nullable=False, unique=True, index=True)
    slug: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    long_description: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Server metadata
    server_type: Mapped[str] = mapped_column(String(50), nullable=False)  # stdio, sse, websocket
    category: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    tags: Mapped[list[str] | None] = mapped_column(JSON, nullable=True)

    # Version and installation
    version: Mapped[str] = mapped_column(String(50), nullable=False, default="1.0.0")
    install_command: Mapped[str | None] = mapped_column(Text, nullable=True)
    configuration_schema: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)

    # Author and links
    author: Mapped[str] = mapped_column(String(255), nullable=False)
    repository_url: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    documentation_url: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    homepage_url: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    license: Mapped[str | None] = mapped_column(String(100), nullable=True)

    # Status and visibility
    status: Mapped[str] = mapped_column(
        String(50), nullable=False, default="pending", index=True
    )  # pending, approved, deprecated, rejected
    visibility: Mapped[str] = mapped_column(
        String(50), nullable=False, default="public"
    )  # public, private

    # Usage statistics
    install_count: Mapped[int] = mapped_column(Integer, default=0)
    usage_count: Mapped[int] = mapped_column(Integer, default=0)
    star_count: Mapped[int] = mapped_column(Integer, default=0)

    # Rating
    average_rating: Mapped[float | None] = mapped_column(Float, nullable=True)
    rating_count: Mapped[int] = mapped_column(Integer, default=0)

    # Featured/promoted
    is_featured: Mapped[bool] = mapped_column(Boolean, default=False)
    is_official: Mapped[bool] = mapped_column(Boolean, default=False)

    # JSONB metadata
    tool_definitions: Mapped[list[dict[str, Any]] | None] = mapped_column(JSON, nullable=True)
    resource_definitions: Mapped[list[dict[str, Any]] | None] = mapped_column(JSON, nullable=True)
    extra_metadata: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)

    # Timestamps
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    __table_args__ = (
        Index("idx_registry_category", "category"),
        Index("idx_registry_status", "status"),
        Index("idx_registry_featured", "is_featured"),
    )


# ============================================================================
# Workflow & Multi-Agent Orchestration Models
# ============================================================================


class Workflow(Base, UUIDMixin, TimestampMixin, SoftDeleteMixin):
    """Workflow definition model for multi-agent orchestration."""

    __tablename__ = "workflows"

    tenant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True
    )
    created_by: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    slug: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    version: Mapped[str] = mapped_column(String(50), nullable=False, default="1.0.0")

    # Workflow definition (stored as JSON)
    steps: Mapped[list[dict[str, Any]]] = mapped_column(
        JSON, nullable=False
    )  # Step definitions
    triggers: Mapped[list[dict[str, Any]] | None] = mapped_column(
        JSON, nullable=True
    )  # Trigger conditions

    # Configuration
    timeout_seconds: Mapped[int] = mapped_column(Integer, default=3600)
    max_retries: Mapped[int] = mapped_column(Integer, default=3)
    retry_strategy: Mapped[str] = mapped_column(
        String(50), default="exponential"
    )  # exponential, linear, none

    # Status
    status: Mapped[str] = mapped_column(
        String(50), nullable=False, default="draft", index=True
    )  # draft, active, archived

    # Metadata
    tags: Mapped[list[str] | None] = mapped_column(JSON, nullable=True)
    category: Mapped[str | None] = mapped_column(String(100), nullable=True)
    extra_metadata: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)

    # Statistics
    execution_count: Mapped[int] = mapped_column(Integer, default=0)
    success_count: Mapped[int] = mapped_column(Integer, default=0)
    failure_count: Mapped[int] = mapped_column(Integer, default=0)

    # Relationships
    executions: Mapped[list["WorkflowExecution"]] = relationship(
        back_populates="workflow", cascade="all, delete"
    )

    __table_args__ = (
        Index("idx_workflows_tenant_slug", "tenant_id", "slug", unique=True),
        Index("idx_workflows_status", "status"),
        Index("idx_workflows_category", "category"),
    )


class WorkflowExecution(Base, UUIDMixin):
    """Workflow execution instance model."""

    __tablename__ = "workflow_executions"

    tenant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True
    )
    workflow_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("workflows.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    triggered_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )

    # Execution context
    input_data: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    context: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)

    # State
    status: Mapped[str] = mapped_column(
        String(50), nullable=False, default="pending", index=True
    )  # pending, running, completed, failed, cancelled
    current_step: Mapped[str | None] = mapped_column(String(255), nullable=True)
    current_step_index: Mapped[int] = mapped_column(Integer, default=0)

    # Results
    output_data: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    error_step: Mapped[str | None] = mapped_column(String(255), nullable=True)

    # Timing
    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, index=True, server_default="now()"
    )
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    duration_seconds: Mapped[int | None] = mapped_column(Integer, nullable=True)

    # Metadata
    extra_metadata: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)

    # Relationships
    workflow: Mapped["Workflow"] = relationship(back_populates="executions")
    step_executions: Mapped[list["WorkflowStepExecution"]] = relationship(
        back_populates="workflow_execution", cascade="all, delete"
    )

    __table_args__ = (
        Index("idx_workflow_executions_tenant_workflow", "tenant_id", "workflow_id"),
        Index("idx_workflow_executions_status", "status"),
        Index("idx_workflow_executions_started_at", "started_at", postgresql_using="btree"),
    )


class WorkflowStepExecution(Base, UUIDMixin):
    """Individual step execution within a workflow."""

    __tablename__ = "workflow_step_executions"

    tenant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True
    )
    workflow_execution_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("workflow_executions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Step identification
    step_name: Mapped[str] = mapped_column(String(255), nullable=False)
    step_index: Mapped[int] = mapped_column(Integer, nullable=False)
    step_type: Mapped[str] = mapped_column(
        String(50), nullable=False
    )  # agent, http, mcp_tool, parallel, conditional

    # Agent reference (if step_type = agent)
    agent_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("agents.id", ondelete="SET NULL"), nullable=True, index=True
    )
    conversation_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("conversations.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    # Execution data
    input_data: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    output_data: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)

    # Status
    status: Mapped[str] = mapped_column(
        String(50), nullable=False, default="pending", index=True
    )  # pending, running, completed, failed, skipped

    # Error handling
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    retry_count: Mapped[int] = mapped_column(Integer, default=0)

    # Timing
    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, index=True, server_default="now()"
    )
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    duration_seconds: Mapped[int | None] = mapped_column(Integer, nullable=True)

    # Metadata
    extra_metadata: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)

    # Relationships
    workflow_execution: Mapped["WorkflowExecution"] = relationship(back_populates="step_executions")

    __table_args__ = (
        Index("idx_step_executions_workflow", "workflow_execution_id", "step_index"),
        Index("idx_step_executions_status", "status"),
        Index("idx_step_executions_agent", "agent_id"),
    )


class AgentTask(Base, UUIDMixin):
    """Task assignment and tracking for multi-agent coordination."""

    __tablename__ = "agent_tasks"

    tenant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True
    )

    # Assignment
    agent_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("agents.id", ondelete="CASCADE"), nullable=False, index=True
    )
    parent_task_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("agent_tasks.id", ondelete="CASCADE"), nullable=True
    )
    workflow_execution_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("workflow_executions.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )
    assigned_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("agents.id", ondelete="SET NULL"), nullable=True
    )

    # Task details
    task_type: Mapped[str] = mapped_column(
        String(50), nullable=False
    )  # execute, delegate, communicate
    instruction: Mapped[str] = mapped_column(Text, nullable=False)
    context: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)

    # Status
    status: Mapped[str] = mapped_column(
        String(50), nullable=False, default="pending", index=True
    )  # pending, assigned, in_progress, completed, failed
    priority: Mapped[int] = mapped_column(Integer, default=5)  # 1-10

    # Results
    result: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Timing
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, index=True, server_default="now()"
    )
    assigned_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    due_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # Metadata
    extra_metadata: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)

    # Relationships
    subtasks: Mapped[list["AgentTask"]] = relationship(
        back_populates="parent_task",
        foreign_keys=[parent_task_id],
        cascade="all, delete",
    )
    parent_task: Mapped["AgentTask | None"] = relationship(
        back_populates="subtasks", remote_side="AgentTask.id", foreign_keys=[parent_task_id]
    )

    __table_args__ = (
        Index("idx_agent_tasks_agent_status", "agent_id", "status"),
        Index("idx_agent_tasks_workflow", "workflow_execution_id"),
        Index("idx_agent_tasks_priority", "priority"),
        Index("idx_agent_tasks_due_at", "due_at", postgresql_using="btree"),
    )


class AgentMessage(Base, UUIDMixin):
    """Inter-agent communication and message passing."""

    __tablename__ = "agent_messages"

    tenant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True
    )

    # Communication
    from_agent_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("agents.id", ondelete="CASCADE"), nullable=False, index=True
    )
    to_agent_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("agents.id", ondelete="CASCADE"), nullable=True, index=True
    )  # Null for broadcast
    workflow_execution_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("workflow_executions.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )

    # Message
    message_type: Mapped[str] = mapped_column(
        String(50), nullable=False, index=True
    )  # request, response, notification, broadcast
    subject: Mapped[str | None] = mapped_column(String(255), nullable=True)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    data: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)

    # Response tracking
    requires_response: Mapped[bool] = mapped_column(Boolean, default=False)
    in_response_to: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("agent_messages.id", ondelete="SET NULL"), nullable=True
    )

    # Status
    status: Mapped[str] = mapped_column(
        String(50), nullable=False, default="sent", index=True
    )  # sent, delivered, read, processed

    # Timing
    sent_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, index=True, server_default="now()"
    )
    delivered_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    read_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    processed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # Metadata
    extra_metadata: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)

    # Relationships
    responses: Mapped[list["AgentMessage"]] = relationship(
        back_populates="parent_message",
        foreign_keys=[in_response_to],
        cascade="all, delete",
    )
    parent_message: Mapped["AgentMessage | None"] = relationship(
        back_populates="responses", remote_side="AgentMessage.id", foreign_keys=[in_response_to]
    )

    __table_args__ = (
        Index("idx_agent_messages_from_agent", "from_agent_id"),
        Index("idx_agent_messages_to_agent", "to_agent_id"),
        Index("idx_agent_messages_workflow", "workflow_execution_id"),
        Index("idx_agent_messages_type", "message_type"),
        Index("idx_agent_messages_sent_at", "sent_at", postgresql_using="btree"),
    )
