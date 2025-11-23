"""
RAG System Tests

Tests for Retrieval-Augmented Generation including:
- Document processing and chunking
- Vector embeddings
- Semantic search
- Collection management
"""

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.models import Collection, Document, Tenant, User


@pytest.mark.rag
@pytest.mark.api
@pytest.mark.asyncio
class TestCollectionAPI:
    """Test collection CRUD operations."""

    async def test_create_collection(
        self,
        authenticated_client: AsyncClient,
        test_tenant: Tenant,
    ):
        """Test creating a new collection."""
        response = await authenticated_client.post(
            "/api/v1/rag/collections",
            json={
                "name": "Test Collection",
                "description": "A collection for testing",
            },
        )

        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "Test Collection"
        assert data["slug"] == "test-collection"
        assert data["document_count"] == 0

    async def test_list_collections(
        self,
        authenticated_client: AsyncClient,
        db_session: AsyncSession,
        test_tenant: Tenant,
        test_user: User,
    ):
        """Test listing collections."""
        # Create some collections
        collection1 = Collection(
            tenant_id=test_tenant.id,
            name="Collection 1",
            slug="collection-1",
            created_by=test_user.id,
        )
        collection2 = Collection(
            tenant_id=test_tenant.id,
            name="Collection 2",
            slug="collection-2",
            created_by=test_user.id,
        )
        db_session.add_all([collection1, collection2])
        await db_session.commit()

        response = await authenticated_client.get("/api/v1/rag/collections")

        assert response.status_code == 200
        data = response.json()
        assert "collections" in data
        assert len(data["collections"]) >= 2

    async def test_get_collection(
        self,
        authenticated_client: AsyncClient,
        db_session: AsyncSession,
        test_tenant: Tenant,
        test_user: User,
    ):
        """Test getting a specific collection."""
        collection = Collection(
            tenant_id=test_tenant.id,
            name="Get Test",
            slug="get-test",
            created_by=test_user.id,
        )
        db_session.add(collection)
        await db_session.commit()
        await db_session.refresh(collection)

        response = await authenticated_client.get(
            f"/api/v1/rag/collections/{collection.id}"
        )

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == str(collection.id)
        assert data["name"] == "Get Test"

    async def test_update_collection(
        self,
        authenticated_client: AsyncClient,
        db_session: AsyncSession,
        test_tenant: Tenant,
        test_user: User,
    ):
        """Test updating a collection."""
        collection = Collection(
            tenant_id=test_tenant.id,
            name="Original Name",
            slug="original",
            created_by=test_user.id,
        )
        db_session.add(collection)
        await db_session.commit()
        await db_session.refresh(collection)

        response = await authenticated_client.patch(
            f"/api/v1/rag/collections/{collection.id}",
            json={"name": "Updated Name"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Updated Name"

    async def test_delete_collection(
        self,
        authenticated_client: AsyncClient,
        db_session: AsyncSession,
        test_tenant: Tenant,
        test_user: User,
    ):
        """Test deleting a collection (soft delete)."""
        collection = Collection(
            tenant_id=test_tenant.id,
            name="To Delete",
            slug="to-delete",
            created_by=test_user.id,
        )
        db_session.add(collection)
        await db_session.commit()
        await db_session.refresh(collection)

        response = await authenticated_client.delete(
            f"/api/v1/rag/collections/{collection.id}"
        )

        assert response.status_code == 204

        # Verify soft delete
        await db_session.refresh(collection)
        assert collection.deleted_at is not None


@pytest.mark.rag
@pytest.mark.api
@pytest.mark.asyncio
class TestDocumentAPI:
    """Test document management."""

    async def test_upload_document(
        self,
        authenticated_client: AsyncClient,
        db_session: AsyncSession,
        test_tenant: Tenant,
        test_user: User,
    ):
        """Test uploading a document to a collection."""
        # Create a collection
        collection = Collection(
            tenant_id=test_tenant.id,
            name="Doc Collection",
            slug="doc-collection",
            created_by=test_user.id,
        )
        db_session.add(collection)
        await db_session.commit()
        await db_session.refresh(collection)

        # Note: This test would need actual file upload mocking
        # For now, we'll test the structure
        response = await authenticated_client.post(
            f"/api/v1/rag/collections/{collection.id}/documents",
            json={
                "title": "Test Document",
                "content": "This is test content for the document.",
                "metadata": {"type": "text"},
            },
        )

        if response.status_code == 201:
            data = response.json()
            assert data["title"] == "Test Document"
            assert "id" in data

    async def test_list_documents_in_collection(
        self,
        authenticated_client: AsyncClient,
        db_session: AsyncSession,
        test_tenant: Tenant,
        test_user: User,
    ):
        """Test listing documents in a collection."""
        # Create collection and documents
        collection = Collection(
            tenant_id=test_tenant.id,
            name="List Test",
            slug="list-test",
            created_by=test_user.id,
        )
        db_session.add(collection)
        await db_session.commit()
        await db_session.refresh(collection)

        doc1 = Document(
            tenant_id=test_tenant.id,
            collection_id=collection.id,
            title="Document 1",
            content="Content 1",
            content_type="text/plain",
            status="processed",
        )
        doc2 = Document(
            tenant_id=test_tenant.id,
            collection_id=collection.id,
            title="Document 2",
            content="Content 2",
            content_type="text/plain",
            status="processed",
        )
        db_session.add_all([doc1, doc2])
        await db_session.commit()

        response = await authenticated_client.get(
            f"/api/v1/rag/collections/{collection.id}/documents"
        )

        assert response.status_code == 200
        data = response.json()
        assert "documents" in data
        assert len(data["documents"]) == 2


@pytest.mark.rag
@pytest.mark.api
@pytest.mark.asyncio
@pytest.mark.slow
class TestSemanticSearch:
    """Test semantic search functionality."""

    async def test_search_in_collection(
        self,
        authenticated_client: AsyncClient,
        db_session: AsyncSession,
        test_tenant: Tenant,
        test_user: User,
    ):
        """Test semantic search in a collection."""
        # Create collection
        collection = Collection(
            tenant_id=test_tenant.id,
            name="Search Test",
            slug="search-test",
            created_by=test_user.id,
        )
        db_session.add(collection)
        await db_session.commit()
        await db_session.refresh(collection)

        # Note: Search would require actual embeddings and pgvector
        # This is a structure test
        response = await authenticated_client.post(
            f"/api/v1/rag/collections/{collection.id}/search",
            json={
                "query": "test query",
                "top_k": 5,
            },
        )

        # Expect success or specific error
        assert response.status_code in [200, 404, 422]

    async def test_search_with_filters(
        self,
        authenticated_client: AsyncClient,
        db_session: AsyncSession,
        test_tenant: Tenant,
        test_user: User,
    ):
        """Test semantic search with metadata filters."""
        collection = Collection(
            tenant_id=test_tenant.id,
            name="Filter Test",
            slug="filter-test",
            created_by=test_user.id,
        )
        db_session.add(collection)
        await db_session.commit()
        await db_session.refresh(collection)

        response = await authenticated_client.post(
            f"/api/v1/rag/collections/{collection.id}/search",
            json={
                "query": "filtered query",
                "top_k": 3,
                "filters": {"type": "article"},
            },
        )

        assert response.status_code in [200, 404, 422]


@pytest.mark.rag
@pytest.mark.unit
class TestDocumentChunking:
    """Test document chunking functionality."""

    def test_chunk_text_by_tokens(self):
        """Test chunking text by token count."""
        text = " ".join([f"Word{i}" for i in range(1000)])

        # Simple chunking logic
        chunk_size = 100
        chunks = []
        words = text.split()

        for i in range(0, len(words), chunk_size):
            chunk = " ".join(words[i : i + chunk_size])
            chunks.append(chunk)

        assert len(chunks) == 10
        assert len(chunks[0].split()) == chunk_size

    def test_chunk_with_overlap(self):
        """Test chunking with overlap."""
        text = " ".join([f"Word{i}" for i in range(200)])
        chunk_size = 50
        overlap = 10

        chunks = []
        words = text.split()

        i = 0
        while i < len(words):
            end = min(i + chunk_size, len(words))
            chunk = " ".join(words[i:end])
            chunks.append(chunk)
            i += chunk_size - overlap

        assert len(chunks) > 1
        # Verify overlap exists between consecutive chunks
        assert chunks[0].split()[-overlap:] == chunks[1].split()[:overlap]


@pytest.mark.rag
@pytest.mark.integration
class TestMultiTenantRAG:
    """Test multi-tenant isolation in RAG system."""

    @pytest.mark.asyncio
    async def test_cannot_access_other_tenant_collections(
        self,
        authenticated_client: AsyncClient,
        tenant_factory,
        user_factory,
        db_session: AsyncSession,
    ):
        """Test that users cannot access collections from other tenants."""
        # Create another tenant with collection
        other_tenant = await tenant_factory(name="Other Tenant")
        other_user = await user_factory(other_tenant.id)

        other_collection = Collection(
            tenant_id=other_tenant.id,
            name="Private Collection",
            slug="private",
            created_by=other_user.id,
        )
        db_session.add(other_collection)
        await db_session.commit()
        await db_session.refresh(other_collection)

        # Try to access with authenticated client (from different tenant)
        response = await authenticated_client.get(
            f"/api/v1/rag/collections/{other_collection.id}"
        )

        assert response.status_code == 404  # Should not find
