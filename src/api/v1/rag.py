"""RAG API endpoints."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.dependencies import CurrentTenant, CurrentUser
from src.db.models import Tenant, User
from src.db.session import get_db
from src.schemas.rag import (
    CollectionCreate,
    CollectionListResponse,
    CollectionResponse,
    CollectionUpdate,
    DocumentListResponse,
    DocumentResponse,
    DocumentUpload,
    RAGContextRequest,
    RAGContextResponse,
    RAGQueryRequest,
    RAGQueryResponse,
)
from src.services.rag_service import RAGService

router = APIRouter()


@router.post("/collections", response_model=CollectionResponse, status_code=status.HTTP_201_CREATED)
async def create_collection(
    collection: CollectionCreate,
    tenant: CurrentTenant,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> CollectionResponse:
    """Create a new knowledge base collection."""
    rag_service = RAGService(db, tenant.id)

    new_collection = await rag_service.create_collection(
        name=collection.name,
        description=collection.description,
        embedding_model=collection.embedding_model,
        embedding_dimensions=collection.embedding_dimensions,
        chunk_size=collection.chunk_size,
        chunk_overlap=collection.chunk_overlap,
        visibility=collection.visibility,
        config=collection.config,
        extra_metadata=collection.extra_metadata,
    )

    await db.commit()
    await db.refresh(new_collection)

    return CollectionResponse.model_validate(new_collection)


@router.get("/collections", response_model=CollectionListResponse)
async def list_collections(
    tenant: CurrentTenant,
    db: Annotated[AsyncSession, Depends(get_db)],
    skip: int = 0,
    limit: int = 20,
) -> CollectionListResponse:
    """List all collections for the tenant."""
    rag_service = RAGService(db, tenant.id)

    collections, total = await rag_service.list_collections(skip=skip, limit=limit)

    return CollectionListResponse(
        data=[CollectionResponse.model_validate(c) for c in collections],
        pagination={
            "skip": skip,
            "limit": limit,
            "total": total,
            "has_more": skip + len(collections) < total,
        },
    )


@router.get("/collections/{collection_id}", response_model=CollectionResponse)
async def get_collection(
    collection_id: UUID,
    tenant: CurrentTenant,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> CollectionResponse:
    """Get a specific collection by ID."""
    rag_service = RAGService(db, tenant.id)

    collection = await rag_service.get_collection(collection_id)
    if not collection:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Collection not found",
        )

    return CollectionResponse.model_validate(collection)


@router.delete("/collections/{collection_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_collection(
    collection_id: UUID,
    tenant: CurrentTenant,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> None:
    """Delete a collection (soft delete)."""
    rag_service = RAGService(db, tenant.id)

    deleted = await rag_service.delete_collection(collection_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Collection not found",
        )

    await db.commit()


@router.post(
    "/collections/{collection_id}/documents",
    response_model=DocumentResponse,
    status_code=status.HTTP_201_CREATED,
)
async def upload_document(
    collection_id: UUID,
    tenant: CurrentTenant,
    db: Annotated[AsyncSession, Depends(get_db)],
    file: UploadFile = File(...),
    title: str = Form(...),
    source: str | None = Form(None),
) -> DocumentResponse:
    """Upload and process a document to a collection."""
    rag_service = RAGService(db, tenant.id)

    # Verify collection exists
    collection = await rag_service.get_collection(collection_id)
    if not collection:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Collection not found",
        )

    # Read file content
    file_content = await file.read()

    # Upload and process document
    try:
        document = await rag_service.upload_document(
            collection_id=collection_id,
            title=title,
            file_content=file_content,
            filename=file.filename or "unknown",
            source=source,
        )

        await db.commit()
        await db.refresh(document)

        return DocumentResponse.model_validate(document)

    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process document: {str(e)}",
        )


@router.get("/collections/{collection_id}/documents", response_model=DocumentListResponse)
async def list_documents(
    collection_id: UUID,
    tenant: CurrentTenant,
    db: Annotated[AsyncSession, Depends(get_db)],
    skip: int = 0,
    limit: int = 20,
) -> DocumentListResponse:
    """List all documents in a collection."""
    rag_service = RAGService(db, tenant.id)

    # Verify collection exists
    collection = await rag_service.get_collection(collection_id)
    if not collection:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Collection not found",
        )

    documents, total = await rag_service.list_documents(
        collection_id=collection_id,
        skip=skip,
        limit=limit,
    )

    return DocumentListResponse(
        data=[DocumentResponse.model_validate(d) for d in documents],
        pagination={
            "skip": skip,
            "limit": limit,
            "total": total,
            "has_more": skip + len(documents) < total,
        },
    )


@router.post("/query", response_model=RAGQueryResponse)
async def query_knowledge_base(
    query_request: RAGQueryRequest,
    tenant: CurrentTenant,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> RAGQueryResponse:
    """Perform semantic search across knowledge base."""
    rag_service = RAGService(db, tenant.id)

    # Verify collection if specified
    if query_request.collection_id:
        collection = await rag_service.get_collection(query_request.collection_id)
        if not collection:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Collection not found",
            )

    # Perform query
    chunks, retrieval_time = await rag_service.query(
        query=query_request.query,
        collection_id=query_request.collection_id,
        top_k=query_request.top_k,
        similarity_threshold=query_request.similarity_threshold,
        metadata_filter=query_request.metadata_filter,
    )

    await db.commit()

    # Build response
    from src.schemas.rag import ChunkResponse

    chunk_responses = []
    for chunk in chunks:
        chunk_response = ChunkResponse(
            id=chunk.id,
            document_id=chunk.document_id,
            collection_id=chunk.collection_id,
            content=chunk.content if query_request.include_content else "",
            sequence_number=chunk.sequence_number,
            token_count=chunk.token_count,
            page_number=chunk.page_number,
            section=chunk.section,
            score=getattr(chunk, "score", None),
            extra_metadata=chunk.extra_metadata,
            created_at=chunk.created_at,
        )
        chunk_responses.append(chunk_response)

    return RAGQueryResponse(
        query=query_request.query,
        results=chunk_responses,
        total_results=len(chunks),
        retrieval_time_ms=retrieval_time,
        collection_id=query_request.collection_id,
    )


@router.post("/context", response_model=RAGContextResponse)
async def get_context_for_agent(
    context_request: RAGContextRequest,
    tenant: CurrentTenant,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> RAGContextResponse:
    """Get formatted context for agent execution."""
    rag_service = RAGService(db, tenant.id)

    # Verify collections if specified
    if context_request.collection_ids:
        for collection_id in context_request.collection_ids:
            collection = await rag_service.get_collection(collection_id)
            if not collection:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Collection {collection_id} not found",
                )

    # Get context
    context, chunks, retrieval_time = await rag_service.get_context_for_agent(
        query=context_request.query,
        collection_ids=context_request.collection_ids,
        top_k=context_request.top_k,
        similarity_threshold=context_request.similarity_threshold,
    )

    await db.commit()

    # Build response
    from src.schemas.rag import ChunkResponse

    chunk_responses = []
    for chunk in chunks:
        chunk_response = ChunkResponse(
            id=chunk.id,
            document_id=chunk.document_id,
            collection_id=chunk.collection_id,
            content=chunk.content,
            sequence_number=chunk.sequence_number,
            token_count=chunk.token_count,
            page_number=chunk.page_number,
            section=chunk.section,
            score=getattr(chunk, "score", None),
            extra_metadata=chunk.extra_metadata,
            created_at=chunk.created_at,
        )
        chunk_responses.append(chunk_response)

    return RAGContextResponse(
        context=context,
        sources=chunk_responses,
        total_chunks=len(chunks),
        retrieval_time_ms=retrieval_time,
    )
