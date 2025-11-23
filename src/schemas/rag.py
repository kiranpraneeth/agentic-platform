"""RAG (Retrieval-Augmented Generation) schemas."""

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field


class CollectionCreate(BaseModel):
    """Collection creation schema."""

    name: str = Field(..., min_length=1, max_length=255)
    description: str | None = None
    embedding_model: str = Field(default="all-MiniLM-L6-v2")
    embedding_dimensions: int = Field(default=384, gt=0)
    chunk_size: int = Field(default=512, gt=0)
    chunk_overlap: int = Field(default=50, ge=0)
    visibility: str = Field(default="private")  # private, shared, public
    config: dict[str, Any] | None = None
    extra_metadata: dict[str, Any] | None = None


class CollectionUpdate(BaseModel):
    """Collection update schema."""

    name: str | None = Field(None, min_length=1, max_length=255)
    description: str | None = None
    chunk_size: int | None = Field(None, gt=0)
    chunk_overlap: int | None = Field(None, ge=0)
    visibility: str | None = None
    config: dict[str, Any] | None = None
    extra_metadata: dict[str, Any] | None = None


class CollectionResponse(BaseModel):
    """Collection response schema."""

    id: UUID
    tenant_id: UUID
    name: str
    description: str | None
    embedding_model: str
    embedding_dimensions: int
    chunk_size: int
    chunk_overlap: int
    visibility: str
    document_count: int
    chunk_count: int
    config: dict[str, Any] | None
    extra_metadata: dict[str, Any] | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class CollectionListResponse(BaseModel):
    """Collection list response schema."""

    data: list[CollectionResponse]
    pagination: dict[str, Any]


class DocumentUpload(BaseModel):
    """Document upload schema."""

    collection_id: UUID
    title: str = Field(..., min_length=1, max_length=500)
    source: str | None = None
    extra_metadata: dict[str, Any] | None = None


class DocumentResponse(BaseModel):
    """Document response schema."""

    id: UUID
    tenant_id: UUID
    collection_id: UUID
    title: str
    source: str | None
    content_type: str
    status: str  # pending, processing, completed, failed
    file_size_bytes: int | None
    file_hash: str | None
    storage_path: str | None
    chunk_count: int
    total_tokens: int | None
    processed_at: datetime | None
    error_message: str | None
    extra_metadata: dict[str, Any] | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class DocumentListResponse(BaseModel):
    """Document list response schema."""

    data: list[DocumentResponse]
    pagination: dict[str, Any]


class ChunkResponse(BaseModel):
    """Chunk response schema."""

    id: UUID
    document_id: UUID
    collection_id: UUID
    content: str
    sequence_number: int
    token_count: int | None
    page_number: int | None
    section: str | None
    score: float | None = None  # similarity score when retrieved
    extra_metadata: dict[str, Any] | None
    created_at: datetime

    model_config = {"from_attributes": True}


class RAGQueryRequest(BaseModel):
    """RAG query request schema."""

    query: str = Field(..., min_length=1)
    collection_id: UUID | None = None
    top_k: int = Field(default=5, gt=0, le=50)
    similarity_threshold: float | None = Field(None, ge=0.0, le=1.0)
    metadata_filter: dict[str, Any] | None = None
    include_content: bool = Field(default=True)


class RAGQueryResponse(BaseModel):
    """RAG query response schema."""

    query: str
    results: list[ChunkResponse]
    total_results: int
    retrieval_time_ms: int | None
    collection_id: UUID | None = None

    model_config = {"from_attributes": True}


class RAGContextRequest(BaseModel):
    """RAG context retrieval for agent execution."""

    query: str = Field(..., min_length=1)
    collection_ids: list[UUID] | None = None
    top_k: int = Field(default=5, gt=0, le=20)
    similarity_threshold: float = Field(default=0.7, ge=0.0, le=1.0)


class RAGContextResponse(BaseModel):
    """RAG context response for agent execution."""

    context: str  # Combined text from retrieved chunks
    sources: list[ChunkResponse]
    total_chunks: int
    retrieval_time_ms: int | None


class DocumentProcessingStatus(BaseModel):
    """Document processing status schema."""

    document_id: UUID
    status: str
    progress: float = Field(default=0.0, ge=0.0, le=100.0)
    chunks_processed: int
    total_chunks: int | None
    error_message: str | None = None
    started_at: datetime | None = None
    completed_at: datetime | None = None
