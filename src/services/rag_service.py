"""RAG service for document management and vector search."""

import time
import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.db.models import Collection, Document, Chunk, RAGQuery
from src.services.document_processor import DocumentProcessor
from src.services.embedding_service import EmbeddingService, get_default_embedding_service


class RAGService:
    """Service for RAG operations."""

    def __init__(self, db: AsyncSession, tenant_id: uuid.UUID):
        """Initialize RAG service.

        Args:
            db: Database session
            tenant_id: Tenant ID for multi-tenant isolation
        """
        self.db = db
        self.tenant_id = tenant_id

    async def create_collection(
        self,
        name: str,
        description: str | None = None,
        embedding_model: str = "text-embedding-3-small",
        embedding_dimensions: int = 1536,
        chunk_size: int = 512,
        chunk_overlap: int = 50,
        visibility: str = "private",
        config: dict[str, Any] | None = None,
        extra_metadata: dict[str, Any] | None = None,
    ) -> Collection:
        """Create a new collection.

        Args:
            name: Collection name
            description: Collection description
            embedding_model: Embedding model to use
            embedding_dimensions: Vector dimensions
            chunk_size: Chunk size in tokens
            chunk_overlap: Overlap between chunks
            visibility: Collection visibility (private, shared, public)
            config: Additional configuration
            extra_metadata: Extra metadata

        Returns:
            Created collection
        """
        collection = Collection(
            tenant_id=self.tenant_id,
            name=name,
            description=description,
            embedding_model=embedding_model,
            embedding_dimensions=embedding_dimensions,
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            visibility=visibility,
            config=config,
            extra_metadata=extra_metadata,
        )

        self.db.add(collection)
        await self.db.flush()
        await self.db.refresh(collection)

        return collection

    async def upload_document(
        self,
        collection_id: uuid.UUID,
        title: str,
        file_content: bytes,
        filename: str,
        source: str | None = None,
        extra_metadata: dict[str, Any] | None = None,
    ) -> Document:
        """Upload and process a document.

        Args:
            collection_id: Collection ID
            title: Document title
            file_content: File content bytes
            filename: Original filename
            source: Source URL or path
            extra_metadata: Extra metadata

        Returns:
            Created document
        """
        # Get collection
        collection = await self.db.get(Collection, collection_id)
        if not collection or collection.tenant_id != self.tenant_id:
            raise ValueError("Collection not found")

        # Determine content type
        processor = DocumentProcessor(
            chunk_size=collection.chunk_size,
            chunk_overlap=collection.chunk_overlap,
        )
        content_type = processor.get_content_type(filename)
        file_hash = processor.calculate_file_hash(file_content)

        # Create document record
        document = Document(
            tenant_id=self.tenant_id,
            collection_id=collection_id,
            title=title,
            source=source or filename,
            content_type=content_type,
            status="processing",
            file_size_bytes=len(file_content),
            file_hash=file_hash,
            extra_metadata=extra_metadata,
        )

        self.db.add(document)
        await self.db.flush()
        await self.db.refresh(document)

        # Process document asynchronously (in background, but for now we'll do it sync)
        try:
            await self._process_document(document, file_content, filename, collection)
        except Exception as e:
            document.status = "failed"
            document.error_message = str(e)
            await self.db.flush()
            raise

        return document

    async def _process_document(
        self,
        document: Document,
        file_content: bytes,
        filename: str,
        collection: Collection,
    ) -> None:
        """Process document: extract text, chunk, and generate embeddings.

        Args:
            document: Document record
            file_content: File content bytes
            filename: Original filename
            collection: Collection
        """
        # Initialize services
        processor = DocumentProcessor(
            chunk_size=collection.chunk_size,
            chunk_overlap=collection.chunk_overlap,
        )

        # Determine provider based on model name
        provider = "openai" if collection.embedding_model.startswith("text-embedding-") else "local"
        embedding_service = EmbeddingService(model=collection.embedding_model, provider=provider)

        # Extract and chunk
        full_text, chunks = await processor.process_file(
            file_content, document.content_type, filename
        )

        # Generate embeddings for all chunks
        chunk_texts = [chunk["content"] for chunk in chunks]
        embeddings = await embedding_service.generate_embeddings_batch(chunk_texts)

        # Store chunks with embeddings
        chunk_records = []
        for chunk_data, embedding in zip(chunks, embeddings):
            chunk = Chunk(
                tenant_id=self.tenant_id,
                document_id=document.id,
                collection_id=collection.id,
                content=chunk_data["content"],
                embedding=embedding,
                sequence_number=chunk_data["sequence_number"],
                token_count=chunk_data["token_count"],
                start_char=chunk_data.get("start_char"),
                end_char=chunk_data.get("end_char"),
            )
            chunk_records.append(chunk)
            self.db.add(chunk)

        # Update document
        document.status = "completed"
        document.chunk_count = len(chunks)
        document.total_tokens = sum(chunk["token_count"] for chunk in chunks)
        document.processed_at = datetime.utcnow()

        # Update collection counts
        collection.document_count += 1
        collection.chunk_count += len(chunks)

        await self.db.flush()

    async def query(
        self,
        query: str,
        collection_id: uuid.UUID | None = None,
        top_k: int = 5,
        similarity_threshold: float | None = None,
        metadata_filter: dict[str, Any] | None = None,
        conversation_id: uuid.UUID | None = None,
    ) -> tuple[list[Chunk], int]:
        """Perform semantic search across chunks.

        Args:
            query: Search query
            collection_id: Optional collection to search in
            top_k: Number of results to return
            similarity_threshold: Minimum similarity score
            metadata_filter: Metadata filters
            conversation_id: Optional conversation ID for logging

        Returns:
            Tuple of (chunks with similarity scores, retrieval time in ms)
        """
        start_time = time.time()

        # Generate query embedding - use default service which auto-detects provider
        embedding_service = get_default_embedding_service()
        query_embedding = await embedding_service.generate_query_embedding(query)

        # Build query
        # Vector similarity using cosine distance (1 - cosine_similarity)
        # pgvector's <=> operator returns cosine distance
        similarity_expr = Chunk.embedding.cosine_distance(query_embedding)

        query_stmt = select(Chunk).where(
            Chunk.tenant_id == self.tenant_id
        )

        if collection_id:
            query_stmt = query_stmt.where(Chunk.collection_id == collection_id)

        # Add similarity threshold if provided
        if similarity_threshold is not None:
            # Convert threshold to distance (1 - threshold)
            max_distance = 1.0 - similarity_threshold
            query_stmt = query_stmt.where(similarity_expr <= max_distance)

        # Order by similarity and limit
        query_stmt = query_stmt.order_by(similarity_expr).limit(top_k)

        # Execute query
        result = await self.db.execute(query_stmt)
        chunks = list(result.scalars().all())

        # Calculate similarity scores (1 - distance)
        # Note: We'll add score as a runtime attribute
        # The distance is already calculated in the SQL query via cosine_distance
        # We need to compute it manually from the embeddings
        import numpy as np

        for chunk in chunks:
            # Convert pgvector to numpy array if needed
            chunk_vec = np.array(chunk.embedding) if not isinstance(chunk.embedding, np.ndarray) else chunk.embedding
            query_vec = np.array(query_embedding) if not isinstance(query_embedding, np.ndarray) else query_embedding

            # Calculate cosine similarity manually
            dot_product = np.dot(chunk_vec, query_vec)
            norm_chunk = np.linalg.norm(chunk_vec)
            norm_query = np.linalg.norm(query_vec)

            # Cosine similarity (ranges from -1 to 1, higher is more similar)
            cosine_sim = dot_product / (norm_chunk * norm_query) if (norm_chunk > 0 and norm_query > 0) else 0.0
            chunk.score = float(cosine_sim)  # type: ignore

        retrieval_time_ms = int((time.time() - start_time) * 1000)

        # Log query
        rag_query = RAGQuery(
            tenant_id=self.tenant_id,
            collection_id=collection_id,
            conversation_id=conversation_id,
            query_text=query,
            query_embedding=query_embedding,
            top_k=top_k,
            similarity_threshold=similarity_threshold,
            metadata_filter=metadata_filter,
            result_count=len(chunks),
            results=[
                {
                    "chunk_id": str(chunk.id),
                    "document_id": str(chunk.document_id),
                    "score": chunk.score,  # type: ignore
                }
                for chunk in chunks
            ],
            retrieval_time_ms=retrieval_time_ms,
        )
        self.db.add(rag_query)
        await self.db.flush()

        return chunks, retrieval_time_ms

    async def get_context_for_agent(
        self,
        query: str,
        collection_ids: list[uuid.UUID] | None = None,
        top_k: int = 5,
        similarity_threshold: float = 0.7,
    ) -> tuple[str, list[Chunk], int]:
        """Get formatted context for agent execution.

        Args:
            query: Search query
            collection_ids: List of collection IDs to search
            top_k: Number of chunks to retrieve
            similarity_threshold: Minimum similarity score

        Returns:
            Tuple of (formatted context string, source chunks, retrieval time)
        """
        all_chunks = []
        total_time = 0

        if collection_ids:
            for collection_id in collection_ids:
                chunks, time_ms = await self.query(
                    query=query,
                    collection_id=collection_id,
                    top_k=top_k,
                    similarity_threshold=similarity_threshold,
                )
                all_chunks.extend(chunks)
                total_time += time_ms
        else:
            all_chunks, total_time = await self.query(
                query=query,
                top_k=top_k,
                similarity_threshold=similarity_threshold,
            )

        # Sort by score and take top_k
        all_chunks.sort(key=lambda c: c.score, reverse=True)  # type: ignore
        all_chunks = all_chunks[:top_k]

        # Format context
        context_parts = []
        for i, chunk in enumerate(all_chunks, 1):
            context_parts.append(
                f"[Source {i}]\n{chunk.content}\n"
            )

        context = "\n\n".join(context_parts)

        return context, all_chunks, total_time

    async def get_collection(self, collection_id: uuid.UUID) -> Collection | None:
        """Get collection by ID.

        Args:
            collection_id: Collection ID

        Returns:
            Collection or None
        """
        result = await self.db.execute(
            select(Collection).where(
                and_(
                    Collection.id == collection_id,
                    Collection.tenant_id == self.tenant_id,
                    Collection.deleted_at.is_(None),
                )
            )
        )
        return result.scalar_one_or_none()

    async def list_collections(
        self, skip: int = 0, limit: int = 20
    ) -> tuple[list[Collection], int]:
        """List collections for tenant.

        Args:
            skip: Number of records to skip
            limit: Number of records to return

        Returns:
            Tuple of (collections, total count)
        """
        # Get total count
        count_stmt = select(func.count()).select_from(Collection).where(
            and_(
                Collection.tenant_id == self.tenant_id,
                Collection.deleted_at.is_(None),
            )
        )
        total = await self.db.scalar(count_stmt) or 0

        # Get collections
        stmt = (
            select(Collection)
            .where(
                and_(
                    Collection.tenant_id == self.tenant_id,
                    Collection.deleted_at.is_(None),
                )
            )
            .order_by(Collection.created_at.desc())
            .offset(skip)
            .limit(limit)
        )

        result = await self.db.execute(stmt)
        collections = list(result.scalars().all())

        return collections, total

    async def list_documents(
        self, collection_id: uuid.UUID, skip: int = 0, limit: int = 20
    ) -> tuple[list[Document], int]:
        """List documents in a collection.

        Args:
            collection_id: Collection ID
            skip: Number of records to skip
            limit: Number of records to return

        Returns:
            Tuple of (documents, total count)
        """
        # Get total count
        count_stmt = select(func.count()).select_from(Document).where(
            and_(
                Document.collection_id == collection_id,
                Document.tenant_id == self.tenant_id,
                Document.deleted_at.is_(None),
            )
        )
        total = await self.db.scalar(count_stmt) or 0

        # Get documents
        stmt = (
            select(Document)
            .where(
                and_(
                    Document.collection_id == collection_id,
                    Document.tenant_id == self.tenant_id,
                    Document.deleted_at.is_(None),
                )
            )
            .order_by(Document.created_at.desc())
            .offset(skip)
            .limit(limit)
        )

        result = await self.db.execute(stmt)
        documents = list(result.scalars().all())

        return documents, total

    async def delete_collection(self, collection_id: uuid.UUID) -> bool:
        """Soft delete a collection.

        Args:
            collection_id: Collection ID

        Returns:
            True if deleted, False if not found
        """
        collection = await self.get_collection(collection_id)
        if not collection:
            return False

        collection.deleted_at = datetime.utcnow()
        await self.db.flush()
        return True
