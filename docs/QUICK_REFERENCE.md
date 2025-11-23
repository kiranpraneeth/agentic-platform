# Agentic Platform - Quick Reference Guide

> **Purpose**: Fast lookup for common patterns and code snippets
>
> **Audience**: Developers who need quick answers without reading the full deep dive
>
> **Last Updated**: 2025-01-09

---

## Table of Contents

1. [Tech Stack at a Glance](#tech-stack-at-a-glance)
2. [Common Commands](#common-commands)
3. [Code Patterns](#code-patterns)
4. [Database Queries](#database-queries)
5. [API Endpoints](#api-endpoints)
6. [Configuration](#configuration)
7. [Troubleshooting](#troubleshooting)

---

## Tech Stack at a Glance

| Component | Technology | Version | Purpose |
|-----------|------------|---------|---------|
| **Language** | Python | 3.11+ | Core language |
| **Framework** | FastAPI | 0.109+ | Async web framework |
| **Database** | PostgreSQL | 16 | Primary data store |
| **Vector Store** | pgvector | - | Embeddings/RAG |
| **Cache/Queue** | Redis | 7 | Caching & background jobs |
| **ORM** | SQLAlchemy | 2.0+ | Database ORM |
| **Migrations** | Alembic | 1.13+ | Schema versioning |
| **Validation** | Pydantic | 2.5+ | Request/response validation |
| **LLM** | Anthropic Claude | - | AI agent runtime |
| **Embeddings** | Sentence Transformers / OpenAI | - | Text vectorization |
| **Container** | Docker | - | Deployment |

---

## Common Commands

### Development

```bash
# Install dependencies
make install
# OR
poetry install

# Run development server (hot reload)
make dev
# OR
poetry run uvicorn src.main:app --reload --port 8000

# Run tests
make test
# OR
poetry run pytest

# Lint code
make lint
# OR
poetry run ruff check src/
poetry run mypy src/

# Format code
make format
# OR
poetry run black src/
```

### Docker

```bash
# Start all services (Postgres, Redis, API)
make docker-up
# OR
docker-compose up -d

# View logs
make docker-logs
# OR
docker-compose logs -f api

# Stop all services
make docker-down
# OR
docker-compose down

# Rebuild containers
docker-compose up -d --build
```

### Database

```bash
# Run migrations
make migrate
# OR
alembic upgrade head

# Create new migration
alembic revision --autogenerate -m "description"

# Rollback one migration
alembic downgrade -1

# View migration history
alembic history

# Seed development data
make seed
# OR
python scripts/seed_dev_data.py
```

### Access Points

```bash
# API Base URL
http://localhost:8000

# Swagger UI (interactive docs)
http://localhost:8000/docs

# ReDoc (alternative docs)
http://localhost:8000/redoc

# Health check
curl http://localhost:8000/health

# OpenAPI schema
http://localhost:8000/v1/openapi.json
```

---

## Code Patterns

### 1. Create a New API Endpoint

**Location**: `src/api/v1/your_module.py`

```python
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.dependencies import CurrentUser, CurrentTenant
from src.db.session import get_db
from src.schemas.your_schema import YourRequest, YourResponse

router = APIRouter()

@router.post("/your-endpoint", response_model=YourResponse)
async def your_endpoint(
    request: YourRequest,
    tenant: CurrentTenant,  # Auto-authenticated
    user: CurrentUser,      # Auto-authenticated
    db: AsyncSession = Depends(get_db),
):
    # Your logic here
    return YourResponse(...)
```

**Register router** in `src/api/v1/__init__.py`:
```python
from src.api.v1 import your_module

api_router.include_router(
    your_module.router,
    prefix="/your-prefix",
    tags=["Your Tag"]
)
```

### 2. Create a Database Model

**Location**: `src/db/models.py`

```python
from src.db.base import Base, UUIDMixin, TimestampMixin

class YourModel(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "your_table"

    tenant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("tenants.id", ondelete="CASCADE"),
        index=True
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Relationships
    tenant: Mapped["Tenant"] = relationship(back_populates="your_models")

    # Indexes
    __table_args__ = (
        Index("idx_your_table_tenant", "tenant_id"),
    )
```

**Create migration**:
```bash
alembic revision --autogenerate -m "add your_table"
alembic upgrade head
```

### 3. Create a Pydantic Schema

**Location**: `src/schemas/your_schema.py`

```python
from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime
import uuid

class YourCreate(BaseModel):
    """Request schema for creation"""
    name: str = Field(..., min_length=1, max_length=255)
    description: str | None = None

class YourUpdate(BaseModel):
    """Request schema for updates"""
    name: str | None = None
    description: str | None = None

class YourResponse(BaseModel):
    """Response schema"""
    id: uuid.UUID
    name: str
    description: str | None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)  # Allow ORM objects
```

### 4. Create a Service Class

**Location**: `src/services/your_service.py`

```python
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import uuid

from src.db.models import YourModel

class YourService:
    """Service for your business logic"""

    def __init__(self, db: AsyncSession, tenant_id: uuid.UUID):
        self.db = db
        self.tenant_id = tenant_id

    async def create(self, name: str, description: str | None = None) -> YourModel:
        """Create a new record"""
        record = YourModel(
            tenant_id=self.tenant_id,
            name=name,
            description=description
        )
        self.db.add(record)
        await self.db.flush()
        await self.db.refresh(record)
        return record

    async def get_by_id(self, record_id: uuid.UUID) -> YourModel | None:
        """Get record by ID"""
        result = await self.db.execute(
            select(YourModel).where(
                YourModel.id == record_id,
                YourModel.tenant_id == self.tenant_id
            )
        )
        return result.scalar_one_or_none()

    async def list_all(self) -> list[YourModel]:
        """List all records for tenant"""
        result = await self.db.execute(
            select(YourModel)
            .where(YourModel.tenant_id == self.tenant_id)
            .order_by(YourModel.created_at.desc())
        )
        return result.scalars().all()
```

### 5. Add Authentication to Endpoint

```python
from src.api.dependencies import CurrentUser, CurrentTenant

@router.post("/protected-endpoint")
async def protected_endpoint(
    tenant: CurrentTenant,  # Requires valid JWT, active tenant
    user: CurrentUser,      # Requires valid JWT, active user
):
    # Access user properties
    print(f"User: {user.email}, Role: {user.role}")
    print(f"Tenant: {tenant.name}, Plan: {tenant.plan_type}")

    return {"message": "Authenticated!"}
```

**Making authenticated requests**:
```bash
# Login first
curl -X POST http://localhost:8000/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "user@example.com", "password": "password"}'

# Response: {"access_token": "eyJ..."}

# Use token in subsequent requests
curl -X POST http://localhost:8000/v1/protected-endpoint \
  -H "Authorization: Bearer eyJ..."
```

### 6. Execute an Agent

```python
from src.services.agent_executor import AgentExecutor
from src.db.models import Agent, Conversation

# Get agent
agent = await db.get(Agent, agent_id)

# Create or get conversation
conversation = Conversation(
    tenant_id=tenant.id,
    agent_id=agent.id,
    user_id=user.id
)
db.add(conversation)
await db.flush()

# Execute
executor = AgentExecutor(agent, db)
response = await executor.execute(
    input_text="Hello, what can you help me with?",
    conversation=conversation
)

print(response.response)  # Agent's response
print(response.token_usage)  # Token usage stats
print(response.latency_ms)  # Response latency
```

### 7. Upload and Search Documents (RAG)

```python
from src.services.rag_service import RAGService
from src.services.embedding_service import EmbeddingService

# Create RAG service
rag_service = RAGService(db, tenant_id=tenant.id)

# Create collection
collection = await rag_service.create_collection(
    name="My Knowledge Base",
    embedding_model="text-embedding-3-small",
    chunk_size=512,
    chunk_overlap=50
)

# Upload document
with open("document.pdf", "rb") as f:
    document = await rag_service.upload_document(
        collection_id=collection.id,
        title="My Document",
        file_content=f.read(),
        filename="document.pdf"
    )

# Search
embedding_service = EmbeddingService()
query_embedding = await embedding_service.generate_embedding("search query")

results = await rag_service.search(
    collection_id=collection.id,
    query_embedding=query_embedding,
    top_k=5
)

for chunk in results:
    print(f"Content: {chunk.content}")
    print(f"Document: {chunk.document.title}")
    print(f"Score: {chunk.similarity_score}")
```

---

## Database Queries

### Common SQLAlchemy Patterns

**Select with filter**:
```python
from sqlalchemy import select

# Single record
result = await db.execute(
    select(Agent).where(Agent.id == agent_id)
)
agent = result.scalar_one_or_none()

# Multiple records
result = await db.execute(
    select(Agent)
    .where(Agent.tenant_id == tenant_id)
    .where(Agent.status == "active")
    .order_by(Agent.created_at.desc())
    .limit(10)
)
agents = result.scalars().all()
```

**Join tables**:
```python
from sqlalchemy.orm import selectinload

# Eager loading (avoids N+1 queries)
result = await db.execute(
    select(Conversation)
    .options(selectinload(Conversation.messages))
    .where(Conversation.id == conversation_id)
)
conversation = result.scalar_one()
# conversation.messages is already loaded
```

**Count records**:
```python
from sqlalchemy import func, select

count = await db.scalar(
    select(func.count()).select_from(Agent).where(Agent.tenant_id == tenant_id)
)
```

**Aggregations**:
```python
from sqlalchemy import func

# Group by and count
result = await db.execute(
    select(Agent.status, func.count(Agent.id))
    .where(Agent.tenant_id == tenant_id)
    .group_by(Agent.status)
)
status_counts = result.all()  # [(status, count), ...]
```

**Insert**:
```python
agent = Agent(
    tenant_id=tenant_id,
    name="My Agent",
    slug="my-agent"
)
db.add(agent)
await db.flush()  # Generates ID but doesn't commit
await db.refresh(agent)  # Load generated fields
```

**Update**:
```python
agent = await db.get(Agent, agent_id)
agent.name = "Updated Name"
agent.status = "inactive"
await db.commit()
```

**Soft Delete**:
```python
agent = await db.get(Agent, agent_id)
agent.deleted_at = datetime.utcnow()
await db.commit()

# Query excludes soft-deleted by default
result = await db.execute(
    select(Agent).where(Agent.deleted_at.is_(None))
)
```

**Vector Search** (pgvector):
```python
from pgvector.sqlalchemy import Vector

# Cosine similarity search
result = await db.execute(
    select(Chunk)
    .where(Chunk.collection_id == collection_id)
    .order_by(Chunk.embedding.cosine_distance(query_embedding))
    .limit(5)
)
similar_chunks = result.scalars().all()
```

---

## API Endpoints

### Authentication

**Login**:
```bash
POST /v1/auth/login
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "password"
}

# Response:
{
  "access_token": "eyJ...",
  "token_type": "bearer"
}
```

### Agents

**Create Agent**:
```bash
POST /v1/agents
Authorization: Bearer {token}
Content-Type: application/json

{
  "name": "My Agent",
  "slug": "my-agent",
  "model_provider": "anthropic",
  "model_name": "claude-sonnet-4-5",
  "system_prompt": "You are a helpful assistant.",
  "temperature": 0.7
}
```

**List Agents**:
```bash
GET /v1/agents?page=1&limit=20&status=active
Authorization: Bearer {token}
```

**Get Agent**:
```bash
GET /v1/agents/{agent_id}
Authorization: Bearer {token}
```

**Execute Agent**:
```bash
POST /v1/agents/{agent_id}/execute
Authorization: Bearer {token}
Content-Type: application/json

{
  "input": "What is the weather today?",
  "conversation_id": "uuid-optional",
  "context": {"key": "value"}
}

# Response:
{
  "conversation_id": "uuid",
  "message_id": "uuid",
  "response": "I don't have access to real-time weather...",
  "token_usage": {
    "input_tokens": 50,
    "output_tokens": 100,
    "total_tokens": 150
  },
  "latency_ms": 1234
}
```

### Conversations

**List Conversations**:
```bash
GET /v1/conversations?agent_id={agent_id}
Authorization: Bearer {token}
```

**Get Conversation**:
```bash
GET /v1/conversations/{conversation_id}
Authorization: Bearer {token}

# Response includes all messages
```

### RAG

**Create Collection**:
```bash
POST /v1/rag/collections
Authorization: Bearer {token}
Content-Type: application/json

{
  "name": "My Knowledge Base",
  "description": "Company documentation",
  "embedding_model": "text-embedding-3-small",
  "chunk_size": 512,
  "chunk_overlap": 50
}
```

**Upload Document**:
```bash
POST /v1/rag/documents/upload
Authorization: Bearer {token}
Content-Type: multipart/form-data

collection_id: uuid
title: "My Document"
file: @document.pdf
```

**Search Documents**:
```bash
POST /v1/rag/search
Authorization: Bearer {token}
Content-Type: application/json

{
  "collection_id": "uuid",
  "query": "What is the company policy on remote work?",
  "top_k": 5
}

# Response:
{
  "results": [
    {
      "chunk_id": "uuid",
      "content": "...",
      "document_title": "HR Handbook",
      "page_number": 15,
      "similarity_score": 0.89
    }
  ]
}
```

---

## Configuration

### Environment Variables

**Required** (`.env` file):
```bash
# Security
SECRET_KEY=your-secret-key-min-32-chars-here
JWT_SECRET=your-jwt-secret-min-32-chars-here

# Database
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/agentic_platform

# Redis
REDIS_URL=redis://localhost:6379

# LLM Provider (at least one required)
ANTHROPIC_API_KEY=sk-ant-api03-...
OPENAI_API_KEY=sk-...
```

**Optional**:
```bash
# API
PROJECT_NAME="Agentic Platform"
VERSION="0.1.0"
API_V1_STR="/v1"
ALLOWED_ORIGINS="http://localhost:3000,https://yourdomain.com"

# Database Pool
DATABASE_POOL_SIZE=20
DATABASE_MAX_OVERFLOW=10

# Redis Pool
REDIS_POOL_SIZE=10

# Agent Settings
DEFAULT_AGENT_TIMEOUT=300
MAX_AGENT_ITERATIONS=10

# JWT
ACCESS_TOKEN_EXPIRE_MINUTES=1440  # 24 hours
REFRESH_TOKEN_EXPIRE_MINUTES=10080  # 7 days

# Logging
LOG_LEVEL=INFO
```

### Accessing Settings in Code

```python
from src.core.config import settings

# Use anywhere
api_key = settings.ANTHROPIC_API_KEY
db_url = settings.DATABASE_URL
timeout = settings.DEFAULT_AGENT_TIMEOUT
```

---

## Troubleshooting

### Database Connection Issues

**Problem**: `sqlalchemy.exc.OperationalError: could not connect to server`

**Solutions**:
```bash
# Check if Postgres is running
docker-compose ps

# View Postgres logs
docker-compose logs postgres

# Restart Postgres
docker-compose restart postgres

# Check connection from terminal
psql postgresql://postgres:postgres@localhost:5432/agentic_platform
```

### Migration Errors

**Problem**: `Target database is not up to date`

**Solution**:
```bash
# Check current version
alembic current

# View pending migrations
alembic history

# Upgrade to latest
alembic upgrade head
```

**Problem**: `Can't locate revision identified by 'xxxxx'`

**Solution**:
```bash
# Stamp database with current version (careful!)
alembic stamp head

# Or recreate migrations
rm alembic/versions/*.py
alembic revision --autogenerate -m "initial"
alembic upgrade head
```

### Authentication Issues

**Problem**: `401 Unauthorized`

**Debug**:
```python
# Check token expiration
from jose import jwt
from src.core.config import settings

token = "eyJ..."
payload = jwt.decode(token, settings.JWT_SECRET, algorithms=["HS256"])
print(payload)  # Check 'exp' timestamp

# Check user status
user = await db.get(User, user_id)
print(user.status)  # Should be 'active'

# Check tenant status
tenant = await db.get(Tenant, user.tenant_id)
print(tenant.status)  # Should be 'active'
```

### LLM API Errors

**Problem**: `anthropic.APIError: 401 Unauthorized`

**Solution**:
```bash
# Check API key is set
echo $ANTHROPIC_API_KEY

# Test API key manually
curl https://api.anthropic.com/v1/messages \
  -H "x-api-key: $ANTHROPIC_API_KEY" \
  -H "anthropic-version: 2023-06-01" \
  -H "content-type: application/json" \
  -d '{"model":"claude-3-5-sonnet-20241022","max_tokens":10,"messages":[{"role":"user","content":"Hi"}]}'
```

**Problem**: `Rate limit exceeded`

**Solution**:
```python
# Add retry logic
from tenacity import retry, stop_after_attempt, wait_exponential

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=4, max=10)
)
async def call_llm():
    return await client.messages.create(...)
```

### Performance Issues

**Slow database queries**:
```bash
# Enable query logging
# In src/db/session.py:
engine = create_async_engine(
    DATABASE_URL,
    echo=True  # Logs all SQL queries
)

# Add indexes for slow queries
# In models.py:
__table_args__ = (
    Index("idx_your_slow_query", "column1", "column2"),
)
```

**High memory usage**:
```python
# Limit batch sizes
chunk_size = 100  # Instead of processing all at once

# Use pagination for large queries
query = select(Model).limit(100).offset(page * 100)

# Clear session periodically
await db.execute(text("SELECT pg_stat_reset()"))
```

### Docker Issues

**Problem**: `Port already in use`

**Solution**:
```bash
# Find what's using the port
lsof -i :8000

# Kill the process
kill -9 <PID>

# Or use different port in docker-compose.yml
ports:
  - "8001:8000"
```

**Problem**: `Out of disk space`

**Solution**:
```bash
# Clean up Docker
docker system prune -a --volumes

# Remove old images
docker image prune -a

# Check disk usage
docker system df
```

---

## Quick Debugging

### Enable Debug Mode

```python
# src/main.py
app = FastAPI(
    debug=True,  # Enables detailed error messages
)

# Or via environment
export DEBUG=true
```

### View Logs

```bash
# API logs
docker-compose logs -f api

# Database logs
docker-compose logs -f postgres

# Redis logs
docker-compose logs -f redis

# All logs
docker-compose logs -f
```

### Interactive Debugging

```python
# Add breakpoint
import pdb; pdb.set_trace()

# Or use ipdb (install: pip install ipdb)
import ipdb; ipdb.set_trace()

# Continue execution: c
# Step into function: s
# Step over: n
# Print variable: p variable_name
```

### Test API with curl

```bash
# Health check
curl http://localhost:8000/health

# Test endpoint with auth
TOKEN="your-token-here"
curl http://localhost:8000/v1/agents \
  -H "Authorization: Bearer $TOKEN"

# POST with JSON body
curl -X POST http://localhost:8000/v1/agents \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"name": "Test", "slug": "test"}'
```

---

## Useful SQL Queries

```sql
-- Check database size
SELECT pg_size_pretty(pg_database_size('agentic_platform'));

-- List all tables
SELECT tablename FROM pg_tables WHERE schemaname = 'public';

-- Count records in all tables
SELECT
    schemaname,
    tablename,
    n_live_tup AS row_count
FROM pg_stat_user_tables
ORDER BY n_live_tup DESC;

-- Check for missing indexes
SELECT
    schemaname,
    tablename,
    attname,
    n_distinct,
    correlation
FROM pg_stats
WHERE schemaname = 'public'
    AND n_distinct > 100
    AND correlation < 0.1;

-- View slow queries
SELECT
    query,
    calls,
    total_time / calls AS avg_time,
    total_time
FROM pg_stat_statements
ORDER BY avg_time DESC
LIMIT 10;

-- Check vector index efficiency
SELECT
    indexrelname,
    idx_scan,
    idx_tup_read,
    idx_tup_fetch
FROM pg_stat_user_indexes
WHERE indexrelname LIKE '%embedding%';
```

---

## Cheat Sheet

### FastAPI Decorators

```python
@router.get("/")          # GET request
@router.post("/")         # POST request
@router.put("/{id}")      # PUT request
@router.patch("/{id}")    # PATCH request
@router.delete("/{id}")   # DELETE request

# Response model
@router.get("/", response_model=Schema)

# Status code
@router.post("/", status_code=201)

# Dependencies
@router.get("/", dependencies=[Depends(require_admin)])
```

### Pydantic Validators

```python
from pydantic import Field, field_validator, model_validator

class Schema(BaseModel):
    # Field constraints
    name: str = Field(..., min_length=1, max_length=255)
    age: int = Field(..., ge=0, le=150)
    email: str = Field(..., pattern=r"^[\w\.-]+@[\w\.-]+\.\w+$")

    # Field validator
    @field_validator("name")
    @classmethod
    def validate_name(cls, v):
        if not v.strip():
            raise ValueError("Name cannot be empty")
        return v.strip()

    # Model validator
    @model_validator(mode="after")
    def validate_model(self):
        if self.start_date > self.end_date:
            raise ValueError("Start date must be before end date")
        return self
```

### SQLAlchemy Types

```python
from sqlalchemy import String, Integer, Float, Boolean, Text, JSON, DateTime
from sqlalchemy.dialects.postgresql import UUID
from pgvector.sqlalchemy import Vector

# Common column types
id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True)
name: Mapped[str] = mapped_column(String(255))
description: Mapped[str | None] = mapped_column(Text, nullable=True)
count: Mapped[int] = mapped_column(Integer, default=0)
price: Mapped[float] = mapped_column(Float)
active: Mapped[bool] = mapped_column(Boolean, default=True)
metadata: Mapped[dict] = mapped_column(JSON)
created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
embedding: Mapped[Any] = mapped_column(Vector(1536))
```

---

**Need more details?** See [CODEBASE_DEEP_DIVE.md](./CODEBASE_DEEP_DIVE.md) for comprehensive explanations.

---

*Generated: 2025-01-09*
*Version: 1.0*
