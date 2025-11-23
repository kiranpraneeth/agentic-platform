# Agentic Platform - Complete Codebase Deep Dive

> **Purpose**: Comprehensive concept-by-concept guide to understanding this codebase as if you wrote it yourself.
>
> **Audience**: Developers who want to deeply understand the architecture, patterns, and implementation choices.
>
> **Last Updated**: 2025-01-09

---

## Table of Contents

1. [Project Overview](#project-overview)
2. [Core Concepts](#core-concepts)
   - [Application Framework - FastAPI](#concept-1-application-framework---fastapi)
   - [Configuration Management](#concept-2-configuration-management)
   - [Database Architecture](#concept-3-database-architecture)
   - [Multi-Tenancy Design](#concept-4-multi-tenancy-design)
   - [Authentication & Security](#concept-5-authentication--security)
   - [Agent Execution Architecture](#concept-6-agent-execution-architecture)
   - [RAG Implementation](#concept-7-rag-implementation)
   - [API Design Patterns](#concept-8-api-design-patterns)
3. [Advanced Concepts](#advanced-concepts)
   - [Database Connection Pooling](#concept-9-database-connection-pooling)
   - [Embeddings & Vector Search](#concept-10-embeddings--vector-search)
   - [Document Processing](#concept-11-document-processing)
   - [JWT Deep Dive](#concept-12-jwt-deep-dive)
   - [Service Layer Pattern](#concept-13-service-layer-pattern)
4. [Production Readiness](#production-readiness)
5. [Migration Roadmap](#migration-roadmap)

---

## Project Overview

**Agentic Platform** is a multi-tenant AI agentic platform built with:
- **Language**: Python 3.11+
- **Framework**: FastAPI (async)
- **Database**: PostgreSQL 16 + pgvector
- **Cache/Queue**: Redis 7
- **LLM Providers**: Anthropic Claude, OpenAI (ready)
- **Deployment**: Docker Compose (MVP), Kubernetes (future)

**Current Phase**: Phase 1 MVP (single agent, multi-tenant ready)

**Repository Structure**:
```
agentic-platform/
├── src/
│   ├── api/v1/          # HTTP endpoints
│   ├── core/            # Config, security
│   ├── db/              # ORM models, session
│   ├── schemas/         # Pydantic models
│   └── services/        # Business logic
├── alembic/             # Database migrations
├── docs/                # Documentation
├── tests/               # Unit/integration tests
├── docker-compose.yml   # Multi-container setup
└── pyproject.toml       # Dependencies
```

**System Architecture Diagram**:

```mermaid
graph TB
    Client[Client Application]
    API[FastAPI<br/>API Layer]
    Auth[Auth<br/>Middleware]
    Service[Service Layer<br/>Business Logic]
    DB[(PostgreSQL<br/>+pgvector)]
    Redis[(Redis<br/>Cache/Queue)]
    LLM[Anthropic Claude<br/>LLM API]

    Client -->|HTTP/REST| API
    API --> Auth
    Auth --> Service
    Service --> DB
    Service --> Redis
    Service -->|Agent Execution| LLM

    style Client fill:#e1f5ff
    style API fill:#b3e5fc
    style Auth fill:#81d4fa
    style Service fill:#4fc3f7
    style DB fill:#ffe0b2
    style Redis fill:#ffcc80
    style LLM fill:#c8e6c9
```

---

## Core Concepts

### CONCEPT 1: Application Framework - FastAPI

**Location**: `src/main.py`

**What You Built**:
```python
app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="Multi-tenant AI agentic platform",
    lifespan=lifespan,
)
```

**Why FastAPI?**
- ✅ **Async Native**: ASGI-based, perfect for I/O-bound LLM calls
- ✅ **Auto-Generated Docs**: OpenAPI/Swagger UI at `/docs`
- ✅ **Type Safety**: Pydantic integration for validation
- ✅ **Performance**: Comparable to Node.js/Go for async workloads

**Alternatives Considered**:

| Framework | Pros | Cons | Use When |
|-----------|------|------|----------|
| **FastAPI** ✅ | Async-first, type-safe, fast | Newer ecosystem | Modern APIs |
| **Django + DRF** | Batteries-included, mature | WSGI (not async-first) | Traditional CRUD |
| **Flask** | Lightweight, flexible | No async native | Small projects |
| **Node.js + Express** | JavaScript ecosystem | Weak typing | Real-time apps |
| **Go + Gin** | Fast, compiled | Verbose, steep curve | High-performance |

**Key Implementation: Lifespan Context Manager**
```python
@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    # Startup logic here
    yield
    # Shutdown: cleanup database connections
    await engine.dispose()
```

**CORS Middleware** (Cross-Origin Resource Sharing):
```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,  # ["*"] in dev, specific domains in prod
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

---

### CONCEPT 2: Configuration Management

**Location**: `src/core/config.py`

**What You Built**:
```python
class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=True,
    )

    SECRET_KEY: str = Field(..., min_length=32)
    DATABASE_URL: PostgresDsn
    ANTHROPIC_API_KEY: str | None = None
```

**Why Pydantic Settings?**
- ✅ **Type Validation**: Automatic validation of environment variables
- ✅ **IDE Support**: Full autocomplete
- ✅ **Security**: Enforces minimum lengths, valid URLs
- ✅ **Defaults**: Sensible defaults with override capability

**Environment Variables** (`.env` file):
```bash
# Security
SECRET_KEY=your-secret-key-min-32-chars
JWT_SECRET=your-jwt-secret-min-32-chars

# Database
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/agentic_platform

# Redis
REDIS_URL=redis://localhost:6379

# LLM Providers
ANTHROPIC_API_KEY=sk-ant-...
OPENAI_API_KEY=sk-...

# Agent Settings
DEFAULT_AGENT_TIMEOUT=300
MAX_AGENT_ITERATIONS=10
```

**Custom Validation**:
```python
@field_validator("ALLOWED_ORIGINS", mode="after")
@classmethod
def parse_allowed_origins(cls, v: str) -> list[str]:
    if v:
        return [origin.strip() for origin in v.split(",")]
    return ["*"]
```

**Singleton Pattern**:
```python
settings = Settings()  # Created once, imported everywhere
```

---

### CONCEPT 3: Database Architecture

**Location**: `src/db/`

#### 3A: Base Mixins Pattern

**Location**: `src/db/base.py`

Instead of repeating fields, you created reusable mixins:

```python
class UUIDMixin:
    """UUID primary key mixin."""
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )

class TimestampMixin:
    """Timestamp tracking mixin."""
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default="now()"
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default="now()",
        onupdate=datetime.utcnow
    )

class SoftDeleteMixin:
    """Soft delete support."""
    deleted_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True
    )
```

**Why Mixins?**
- ✅ **DRY Principle**: Write once, use everywhere
- ✅ **Consistency**: All models have same UUID/timestamp pattern
- ✅ **Soft Deletes**: Never actually delete data (for audit trails)

**Usage**:
```python
class Tenant(Base, UUIDMixin, TimestampMixin, SoftDeleteMixin):
    __tablename__ = "tenants"
    name: Mapped[str] = mapped_column(String(255))
    # Automatically gets: id, created_at, updated_at, deleted_at
```

#### 3B: SQLAlchemy 2.0 Mapped Columns

**Modern Syntax**:
```python
# Old way (SQLAlchemy 1.x):
name = Column(String(255), nullable=False)

# New way (SQLAlchemy 2.0):
name: Mapped[str] = mapped_column(String(255), nullable=False)
```

**Benefits**:
- ✅ Type hints integrated with ORM
- ✅ MyPy can check types statically
- ✅ Better IDE autocomplete

#### 3C: Relationships and Foreign Keys

**One-to-Many Pattern**:
```python
class Tenant:
    # Tenant has many users
    users: Mapped[list["User"]] = relationship(
        back_populates="tenant",
        cascade="all, delete"
    )

class User:
    # User belongs to one tenant
    tenant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("tenants.id", ondelete="CASCADE"),
        index=True
    )
    tenant: Mapped["Tenant"] = relationship(back_populates="users")
```

**Key Concepts**:
- `cascade="all, delete"`: When tenant is deleted, delete all users (ORM-level)
- `ondelete="CASCADE"`: Database-level cascade delete
- `back_populates`: Bidirectional relationship
- `index=True`: Speed up queries by tenant_id

**Database Relationships Diagram**:

```mermaid
erDiagram
    Tenant ||--o{ User : has
    Tenant ||--o{ Agent : has
    Tenant ||--o{ Conversation : has
    User ||--o{ Conversation : creates
    Agent ||--o{ Conversation : uses
    Conversation ||--o{ Message : contains
    Agent ||--o{ ToolExecution : executes
    Message ||--o{ ToolExecution : triggers
    Tenant ||--o{ Collection : owns
    Collection ||--o{ Document : contains
    Document ||--o{ Chunk : splits_into

    Tenant {
        uuid id PK
        string name
        string slug UK
        string status
        string plan_type
        int max_agents
    }
    User {
        uuid id PK
        uuid tenant_id FK
        string email
        string role
        string status
    }
    Agent {
        uuid id PK
        uuid tenant_id FK
        string name
        string model_provider
        string model_name
        float temperature
    }
    Conversation {
        uuid id PK
        uuid tenant_id FK
        uuid agent_id FK
        uuid user_id FK
        string status
    }
    Message {
        uuid id PK
        uuid conversation_id FK
        string role
        text content
        int token_count
    }
```

#### 3D: Vector Embeddings with pgvector

**Location**: `src/db/models.py:463`

```python
from pgvector.sqlalchemy import Vector

class Chunk:
    embedding: Mapped[Any] = mapped_column(Vector(1536), nullable=True)
```

**HNSW Index for Fast Similarity Search**:
```python
Index(
    "idx_chunks_embedding_hnsw",
    "embedding",
    postgresql_using="hnsw",  # Hierarchical Navigable Small World
    postgresql_with={"m": 16, "ef_construction": 64},
    postgresql_ops={"embedding": "vector_cosine_ops"},
)
```

**What This Does**:
- `Vector(1536)`: Stores OpenAI embeddings (1536 dimensions)
- `HNSW`: Approximate nearest neighbor search (10-100x faster than exact search)
- `Cosine Similarity`: Measures semantic similarity between vectors

**Vector Store Alternatives**:

| Approach | Pros | Cons | Use When |
|----------|------|------|----------|
| **pgvector** ✅ | Native Postgres, transactional | Limited to ~1M vectors | Small-medium datasets |
| **Pinecone** | Managed, scales to billions | Cost, vendor lock-in | Large-scale production |
| **Weaviate** | Open-source vector DB | Separate infrastructure | Dedicated vector workloads |
| **Qdrant** | Fast, Rust-based | Learning curve | High-performance needs |

#### 3E: Composite Indexes

**Multi-Column Indexes**:
```python
__table_args__ = (
    Index("idx_users_tenant_email", "tenant_id", "email", unique=True),
    Index("idx_users_tenant_status", "tenant_id", "status"),
)
```

**Purpose**:
- **tenant + email uniqueness**: Each tenant can have user@example.com, but globally unique
- **tenant + status**: Fast filtering like `WHERE tenant_id = X AND status = 'active'`

---

### CONCEPT 4: Multi-Tenancy Design

**Location**: All models in `src/db/models.py`

**Pattern**: Row-Level Multi-Tenancy with `tenant_id` on every table

```python
class User:
    tenant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("tenants.id", ondelete="CASCADE"),
        index=True
    )

class Agent:
    tenant_id: Mapped[uuid.UUID] = mapped_column(...)

class Message:
    tenant_id: Mapped[uuid.UUID] = mapped_column(...)
```

**Query Pattern** (always filter by tenant_id):
```python
query = select(Agent).where(
    Agent.tenant_id == tenant.id,
    Agent.deleted_at.is_(None)
)
```

**Why This Approach?**
- ✅ **Data Isolation**: Tenant A cannot access Tenant B's data
- ✅ **Single Database**: Easier to manage than separate DBs per tenant
- ✅ **Scalable**: Can shard by tenant_id later

**Multi-Tenancy Alternatives**:

| Approach | Pros | Cons | Use When |
|----------|------|------|----------|
| **Row-level** ✅ | Simple, cost-effective | Risk of data leaks if query forgets tenant_id | Startups, SaaS |
| **Schema per tenant** | Better isolation | Complex migrations | Regulated industries |
| **Database per tenant** | Total isolation | High overhead, expensive | Enterprise customers |
| **Hybrid** | Flexibility | Complexity | Mixed customer tiers |

---

### CONCEPT 5: Authentication & Security

**Location**: `src/core/security.py`, `src/api/dependencies.py`

#### JWT Token Creation

```python
def create_access_token(subject: str | Any) -> str:
    expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode = {
        "exp": expire,
        "sub": str(subject),  # User ID
        "type": "access"
    }
    return jwt.encode(to_encode, settings.JWT_SECRET, algorithm="HS256")
```

**JWT Structure**:
```
header.payload.signature

Header: {"alg": "HS256", "typ": "JWT"}
Payload: {"sub": "user-uuid", "exp": 1735689600, "type": "access"}
Signature: HMACSHA256(header + payload, SECRET_KEY)
```

#### Dependency Injection Chain

```python
# Step 1: Get database session
async def get_db() -> AsyncSession:
    async with AsyncSessionLocal() as session:
        yield session

# Step 2: Get current user from JWT
async def get_current_user(
    authorization: str = Header(),
    db: AsyncSession = Depends(get_db),
) -> User:
    # Extract token from "Bearer <token>"
    scheme, token = authorization.split()

    # Decode and verify
    payload = jwt.decode(token, settings.JWT_SECRET, algorithms=["HS256"])
    user_id = payload.get("sub")

    # Fetch user
    user = await db.get(User, user_id)

    if user.status != "active":
        raise HTTPException(403)

    return user

# Step 3: Get tenant from user
async def get_current_tenant(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Tenant:
    tenant = await db.get(Tenant, current_user.tenant_id)

    if tenant.status != "active":
        raise HTTPException(403)

    return tenant
```

**Usage in Endpoints**:
```python
# Type aliases for cleaner code
CurrentUser = Annotated[User, Depends(get_current_user)]
CurrentTenant = Annotated[Tenant, Depends(get_current_tenant)]

@router.post("/agents")
async def create_agent(
    tenant: CurrentTenant,  # Automatically authenticated!
    user: CurrentUser,      # Automatically validated!
):
    # Both tenant and user are ready to use
```

**Execution Order**:
```
1. Request: POST /v1/agents with Authorization header
2. FastAPI sees: tenant: CurrentTenant
3. Calls get_current_tenant() → needs current_user
4. Calls get_current_user() → needs db
5. Calls get_db() → returns AsyncSession
6. Unwinds: db → user → tenant → endpoint
```

#### Password Hashing

```python
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Hash password
password_hash = pwd_context.hash("user_password")
# → "$2b$12$KIX..."

# Verify password
is_valid = pwd_context.verify("user_password", password_hash)
```

**Why bcrypt?**
- ✅ **Adaptive**: Can increase rounds as hardware improves
- ✅ **Salted**: Rainbow table attacks don't work
- ✅ **Slow**: ~100ms per hash (prevents brute force)

---

### CONCEPT 6: Agent Execution Architecture

**Location**: `src/services/agent_executor.py`

**What You Built**: Service layer that orchestrates LLM API calls and manages conversation state

```python
class AgentExecutor:
    def __init__(self, agent: Agent, db: AsyncSession):
        self.agent = agent
        self.db = db

        # Factory pattern: choose LLM provider
        if agent.model_provider == "anthropic":
            self.client = Anthropic(api_key=settings.ANTHROPIC_API_KEY)
        elif agent.model_provider == "openai":
            # OpenAI setup...
```

**Execution Flow**:

```mermaid
sequenceDiagram
    participant Client
    participant API as API Endpoint
    participant Executor as AgentExecutor
    participant DB as Database
    participant LLM as Anthropic Claude

    Client->>API: POST /agents/{id}/execute
    API->>Executor: execute(input_text)

    Executor->>DB: Get conversation history
    DB-->>Executor: Return messages

    Executor->>DB: Save user message
    DB-->>Executor: Message saved

    Executor->>LLM: Call messages.create()
    Note over Executor,LLM: Send system prompt<br/>+ conversation history<br/>+ user input
    LLM-->>Executor: Response + token usage

    Executor->>Executor: Calculate latency

    Executor->>DB: Save assistant message
    DB-->>Executor: Message saved

    Executor->>DB: Update conversation status
    DB-->>Executor: Updated

    Executor-->>API: Return AgentExecuteResponse
    API-->>Client: JSON response
```

**Code Walkthrough**:
```python
async def execute(
    self,
    input_text: str,
    conversation: Conversation,
) -> AgentExecuteResponse:
    start_time = time.time()

    # Get conversation history
    conversation_history = await self._get_conversation_history(conversation.id)

    # Save user message
    user_message = await self._save_message(
        conversation=conversation,
        role="user",
        content=input_text,
        sequence_number=len(conversation_history),
    )

    # Call LLM
    response = await self._execute_anthropic(input_text, conversation_history)

    # Calculate latency
    latency_ms = int((time.time() - start_time) * 1000)

    # Save assistant response
    assistant_message = await self._save_message(
        conversation=conversation,
        role="assistant",
        content=response["content"],
        token_count=response["token_usage"]["output_tokens"],
        latency_ms=latency_ms,
    )

    return AgentExecuteResponse(...)
```

**Anthropic API Integration**:
```python
async def _execute_anthropic(self, input_text: str, conversation_history):
    # Build messages list
    messages = [
        {"role": msg["role"], "content": msg["content"]}
        for msg in conversation_history
        if msg["role"] in ["user", "assistant"]
    ]
    messages.append({"role": "user", "content": input_text})

    # Call Claude API
    response = self.client.messages.create(
        model=self.agent.model_name,
        max_tokens=self.agent.max_tokens or 4096,
        temperature=self.agent.temperature or 0.7,
        system=self.agent.system_prompt,
        messages=messages,
    )

    # Extract text
    content = ""
    for block in response.content:
        if hasattr(block, "text"):
            content += block.text

    return {
        "content": content,
        "token_usage": {
            "input_tokens": response.usage.input_tokens,
            "output_tokens": response.usage.output_tokens,
        },
    }
```

**Key Patterns**:
1. **Separation of Concerns**: API layer → Service layer → Database layer
2. **Conversation State**: Store all messages for context
3. **Observability**: Track latency, token usage, model used
4. **Flexibility**: Easy to swap LLM providers

---

### CONCEPT 7: RAG Implementation

**Location**: `src/services/rag_service.py`, `src/services/document_processor.py`, `src/services/embedding_service.py`

**Architecture Flow**:

```mermaid
flowchart TD
    Upload[Upload Document<br/>PDF/DOCX/TXT/MD]
    Detect[Detect Content Type]
    Extract[Extract Text<br/>DocumentProcessor]
    Clean[Clean Text<br/>Remove whitespace]
    Chunk[Chunk Text<br/>size=512, overlap=50]
    Embed[Generate Embeddings<br/>EmbeddingService]
    Store[(Store in PostgreSQL<br/>with pgvector)]
    Search[Semantic Search<br/>Cosine Similarity]

    Upload --> Detect
    Detect --> Extract
    Extract --> Clean
    Clean --> Chunk
    Chunk -->|Batch| Embed
    Embed --> Store
    Store -.Query.-> Search

    style Upload fill:#e1f5ff
    style Extract fill:#b3e5fc
    style Chunk fill:#81d4fa
    style Embed fill:#4fc3f7
    style Store fill:#ffe0b2
    style Search fill:#c8e6c9
```

#### Document Upload Pipeline

**1. Create Collection**:
```python
async def create_collection(
    name: str,
    embedding_model: str = "text-embedding-3-small",
    chunk_size: int = 512,
    chunk_overlap: int = 50,
) -> Collection:
    collection = Collection(
        tenant_id=self.tenant_id,
        name=name,
        embedding_model=embedding_model,
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
    )
    self.db.add(collection)
    return collection
```

**2. Upload Document**:
```python
async def upload_document(
    collection_id: uuid.UUID,
    title: str,
    file_content: bytes,
    filename: str,
) -> Document:
    # Detect content type
    processor = DocumentProcessor()
    content_type = processor.get_content_type(filename)

    # Create document record
    document = Document(
        tenant_id=self.tenant_id,
        collection_id=collection_id,
        title=title,
        content_type=content_type,
        status="processing",
    )
    self.db.add(document)

    # Process document
    await self._process_document(document, file_content, collection)

    return document
```

**3. Process Document**:
```python
async def _process_document(document, file_content, collection):
    # Extract text
    processor = DocumentProcessor()
    text = processor.extract_text(file_content, filename)

    # Split into chunks
    chunks = processor.chunk_text(text, chunk_size=512, overlap=50)

    # Generate embeddings
    embedding_service = EmbeddingService()
    embeddings = await embedding_service.generate_embeddings(chunks)

    # Save chunks to database
    for i, (chunk_text, embedding) in enumerate(zip(chunks, embeddings)):
        chunk = Chunk(
            tenant_id=self.tenant_id,
            document_id=document.id,
            collection_id=collection.id,
            content=chunk_text,
            embedding=embedding,
            sequence_number=i,
        )
        self.db.add(chunk)

    # Update document
    document.status = "completed"
    document.chunk_count = len(chunks)
    await self.db.commit()
```

#### Chunking Strategy

**Why Chunk?**
- LLMs have token limits
- Smaller chunks = more precise retrieval
- Overlap ensures context isn't lost at boundaries

**Example**:
```
Document: "AI is transforming healthcare by enabling..."
Chunk Size: 512 tokens
Overlap: 50 tokens

Chunk 1: [0:512] "AI is transforming healthcare..."
Chunk 2: [462:974] "...enabling early disease detection..." (50 token overlap)
Chunk 3: [924:1436] "...through pattern recognition..."
```

**Chunking with Sentence Boundaries**:
```python
def _create_chunks(self, text: str):
    tokens = self.tokenizer.encode(text)
    chunks = []
    start = 0

    while start < total_tokens:
        end = min(start + self.chunk_size, total_tokens)
        chunk_tokens = tokens[start:end]
        chunk_text = self.tokenizer.decode(chunk_tokens)

        # Find sentence boundary
        if end < total_tokens:
            search_start = int(len(chunk_text) * 0.8)
            sentence_match = re.search(r"[.!?]\s+", chunk_text[search_start:])
            if sentence_match:
                split_pos = search_start + sentence_match.end()
                chunk_text = chunk_text[:split_pos].strip()

        chunks.append(chunk_text)
        start += self.chunk_size - self.chunk_overlap

    return chunks
```

#### Embedding Service

**Dual Provider Support**:
```python
class EmbeddingService:
    def __init__(self, model: str = "all-MiniLM-L6-v2", provider: str = "local"):
        if provider == "local":
            # Sentence Transformers (free, runs locally)
            from sentence_transformers import SentenceTransformer
            self._local_model = SentenceTransformer(model)
        elif provider == "openai":
            # OpenAI API (paid, higher quality)
            from openai import AsyncOpenAI
            self.client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
```

**Cost-Benefit Analysis**:

| Provider | Model | Cost/1M tokens | Dimensions | Quality | Latency |
|----------|-------|---------------|------------|---------|---------|
| **Local** | all-MiniLM-L6-v2 | $0 | 384 | Good | ~5ms |
| **Local** | all-mpnet-base-v2 | $0 | 768 | Better | ~15ms |
| **OpenAI** | text-embedding-3-small | $0.02 | 1536 | Best | ~100ms |
| **OpenAI** | text-embedding-3-large | $0.13 | 3072 | Excellent | ~150ms |

**Async Threading for CPU-Bound Operations**:
```python
# Run in thread pool to avoid blocking event loop
embedding = await asyncio.to_thread(
    self._local_model.encode,
    text,
    convert_to_numpy=False,
)
```

#### Semantic Search

```python
async def search(
    query_text: str,
    collection_id: uuid.UUID,
    top_k: int = 5,
) -> list[Chunk]:
    # Generate query embedding
    query_embedding = await embedding_service.embed(query_text)

    # Vector similarity search
    results = await db.execute(
        select(Chunk)
        .where(Chunk.collection_id == collection_id)
        .order_by(Chunk.embedding.cosine_distance(query_embedding))
        .limit(top_k)
    )

    return results.scalars().all()
```

---

### CONCEPT 8: API Design Patterns

#### Request/Response Schemas

**Location**: `src/schemas/`

```python
class AgentCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    slug: str = Field(..., pattern=r"^[a-z0-9-]+$")
    model_provider: str = Field(default="anthropic")
    temperature: float = Field(default=0.7, ge=0.0, le=2.0)

class AgentResponse(BaseModel):
    id: uuid.UUID
    name: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)  # Allow ORM objects
```

**Benefits**:
- ✅ Automatic validation
- ✅ Type coercion (e.g., "0.8" → 0.8)
- ✅ OpenAPI schema generation
- ✅ IDE autocomplete

#### Pagination Pattern

```python
@router.get("", response_model=AgentListResponse)
async def list_agents(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
):
    # Count total
    total = await db.scalar(select(func.count()).select_from(Agent))

    # Get page
    offset = (page - 1) * limit
    query = select(Agent).offset(offset).limit(limit)
    agents = (await db.execute(query)).scalars().all()

    return AgentListResponse(
        data=agents,
        pagination={
            "page": page,
            "limit": limit,
            "total": total,
            "total_pages": (total + limit - 1) // limit,
        },
    )
```

#### Error Handling

```python
@router.post("/agents")
async def create_agent(agent_data: AgentCreate):
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Agent with slug '{agent_data.slug}' already exists",
        )
```

**FastAPI automatically returns**:
```json
{
  "detail": "Agent with slug 'my-agent' already exists"
}
```

---

## Advanced Concepts

### CONCEPT 9: Database Connection Pooling

**Location**: `src/db/session.py`

**What You Built**:
```python
engine = create_async_engine(
    str(settings.DATABASE_URL).replace("postgresql://", "postgresql+asyncpg://"),
    pool_size=settings.DATABASE_POOL_SIZE,        # Default: 20
    max_overflow=settings.DATABASE_MAX_OVERFLOW,  # Default: 10
    echo=False,
)
```

**Why Connection Pooling?**

**Without Pool**:
```
Request 1 → Create Connection (50ms) → Query → Close
Request 2 → Create Connection (50ms) → Query → Close
# Overhead: 50ms per request
```

**With Pool**:
```
Startup: Create 20 connections
Request 1 → Borrow Connection #3 → Query → Return
Request 2 → Borrow Connection #7 → Query → Return
# Overhead: ~0ms
```

**Pool Configuration**:
```python
pool_size = 20        # Minimum persistent connections
max_overflow = 10     # Additional connections when pool exhausted
# Total max = 30 connections
```

**Session Factory**:
```python
AsyncSessionLocal = async_sessionmaker(
    engine,
    expire_on_commit=False,  # Don't expire objects after commit
    autocommit=False,        # Manual transaction control
    autoflush=False,         # Manual flush control
)
```

**Dependency with Auto-Rollback**:
```python
async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()  # Auto-commit on success
        except Exception:
            await session.rollback()  # Auto-rollback on error
            raise
        finally:
            await session.close()
```

**Async I/O Benefits**:
```python
# Sync (blocking): 20ms total
user = db.query(User).first()   # 10ms
agent = db.query(Agent).first() # 10ms

# Async (non-blocking): ~10ms total
user_task = db.execute(select(User))
agent_task = db.execute(select(Agent))
user = (await user_task).scalar()
agent = (await agent_task).scalar()  # Already done!
```

---

### CONCEPT 10: Embeddings & Vector Search

**Location**: `src/services/embedding_service.py`

**What Embeddings Are**:
```python
# Text → 1536-dimensional vector
text = "AI is transforming healthcare"
embedding = [0.023, -0.145, 0.892, ..., 0.234]  # 1536 numbers
```

**Conceptual Model**:
- Similar meanings → Close coordinates in 1536D space
- Different meanings → Distant coordinates

**Example**:
```
"cat"    → [0.8, 0.3, 0.1, ...]
"kitten" → [0.79, 0.31, 0.09, ...]  # Close
"car"    → [-0.5, 0.9, -0.3, ...]   # Far
```

**Dual Provider Strategy**:
```python
# Local (free, fast for small batches)
embedding_service = EmbeddingService(
    model="all-MiniLM-L6-v2",
    provider="local"
)

# OpenAI (paid, higher quality)
embedding_service = EmbeddingService(
    model="text-embedding-3-small",
    provider="openai"
)
```

**Async Threading for CPU Work**:
```python
# Prevents blocking event loop
embedding = await asyncio.to_thread(
    self._local_model.encode,
    text
)
```

**Batch Processing**:
```python
# Process 100 texts in one API call
for i in range(0, len(texts), 100):
    batch = texts[i:i+100]
    response = await self.client.embeddings.create(input=batch)
    embeddings.extend(response.data)
```

**Redis Caching**:
```python
# Cache key
text_hash = hashlib.sha256(text.encode()).hexdigest()
cache_key = f"embedding:{provider}:{model}:{text_hash}"

# Try cache
cached = await redis.get(cache_key)
if cached:
    return json.loads(cached)

# Generate and cache
embedding = await super().generate_embedding(text)
await redis.setex(cache_key, 7*24*3600, json.dumps(embedding))
```

**Vector Search**:
```python
# Cosine similarity search
results = await db.execute(
    select(Chunk)
    .where(Chunk.collection_id == collection_id)
    .order_by(Chunk.embedding.cosine_distance(query_embedding))
    .limit(5)
)
```

---

### CONCEPT 11: Document Processing

**Location**: `src/services/document_processor.py`

**Supported Formats**:
- PDF (pypdf)
- DOCX (python-docx)
- TXT (raw text)
- Markdown (markdown → html → text)
- HTML (BeautifulSoup)

**PDF Extraction**:
```python
async def _extract_pdf(self, file_content: bytes) -> str:
    pdf = PdfReader(BytesIO(file_content))
    text_parts = []

    for page_num, page in enumerate(pdf.pages, start=1):
        page_text = page.extract_text()
        text_parts.append(f"\n--- Page {page_num} ---\n{page_text}")

    return "\n".join(text_parts)
```

**Text Cleaning**:
```python
def _clean_text(self, text: str) -> str:
    # Normalize whitespace
    text = re.sub(r"\s+", " ", text)

    # Remove excessive newlines
    text = re.sub(r"\n{3,}", "\n\n", text)

    return text.strip()
```

**Chunking with Sentence Boundaries**:
```python
# Get chunk
chunk_tokens = tokens[start:end]
chunk_text = self.tokenizer.decode(chunk_tokens)

# Find sentence ending in last 20%
if end < total_tokens:
    search_start = int(len(chunk_text) * 0.8)
    sentence_match = re.search(r"[.!?]\s+", chunk_text[search_start:])
    if sentence_match:
        # Split at sentence boundary
        split_pos = search_start + sentence_match.end()
        chunk_text = chunk_text[:split_pos].strip()
```

**Chunking Strategies**:

1. **Fixed-Size with Overlap** (default):
   - Predictable sizes
   - May split semantics
   - Best for: General purpose

2. **Semantic Chunking**:
   - Respects paragraphs
   - Variable sizes
   - Best for: Structured documents

3. **Sentence-Based**:
   - Clean boundaries
   - May be too small
   - Best for: Q&A systems

---

### CONCEPT 12: JWT Deep Dive

**Location**: `src/core/security.py`, `src/api/dependencies.py`

**JWT Structure**:
```
header.payload.signature

Header:
{
  "alg": "HS256",
  "typ": "JWT"
}

Payload:
{
  "sub": "user-uuid",    # Subject (user ID)
  "exp": 1735689600,     # Expiration
  "type": "access"       # Token type
}

Signature:
HMACSHA256(
  base64(header) + "." + base64(payload),
  SECRET_KEY
)
```

**Access vs Refresh Tokens**:

| Token Type | Lifetime | Usage | Storage |
|------------|----------|-------|---------|
| **Access** | 24 hours | API requests | Memory |
| **Refresh** | 7 days | Get new access token | HttpOnly cookie |

**Token Refresh Flow**:
```
1. User logs in → Server returns {access_token, refresh_token}
2. Client stores both (access in memory, refresh in cookie)
3. Client makes API request with access_token
4. Access token expires → 401 error
5. Client sends refresh_token → Server validates
6. Server returns new access_token
7. Client continues with new token
```

**Dependency Injection Chain**:
```python
# Endpoint depends on tenant
@router.post("/agents")
async def create_agent(tenant: CurrentTenant):
    pass

# CurrentTenant depends on current_user
async def get_current_tenant(current_user: User):
    pass

# current_user depends on JWT validation
async def get_current_user(authorization: str, db: AsyncSession):
    # Decode token
    payload = jwt.decode(token, SECRET_KEY)
    user_id = payload["sub"]

    # Fetch user
    user = await db.get(User, user_id)

    # Validate status
    if user.status != "active":
        raise HTTPException(403)

    return user
```

**Password Security**:
```python
# Hashing (bcrypt)
password_hash = pwd_context.hash("password")
# → "$2b$12$..."

# Verification
is_valid = pwd_context.verify("password", password_hash)

# Why bcrypt?
# - Adaptive (can increase cost)
# - Salted (unique hash per password)
# - Slow (~100ms prevents brute force)
```

---

### CONCEPT 13: Service Layer Pattern

**Why Service Layer?**

**❌ Bad: Logic in Endpoints**
```python
@router.post("/agents/execute")
async def execute_agent(agent_id: UUID, db: AsyncSession):
    # Fetch agent
    agent = await db.get(Agent, agent_id)

    # Initialize LLM
    client = Anthropic(api_key=settings.ANTHROPIC_API_KEY)

    # Build messages
    messages = [...]

    # Call LLM
    response = client.messages.create(...)

    # Problems:
    # - Hard to test
    # - Can't reuse logic
    # - Mixed concerns
```

**✅ Good: Service Layer**
```python
# API Layer
@router.post("/agents/execute")
async def execute_agent(agent_id: UUID, db: AsyncSession):
    agent = await db.get(Agent, agent_id)
    executor = AgentExecutor(agent, db)
    response = await executor.execute(input_text)
    return response

# Service Layer
class AgentExecutor:
    async def execute(self, input_text):
        # All business logic here

# Benefits:
# - Testable
# - Reusable
# - Clear separation
# - Easy to maintain
```

**Layered Architecture**:
```
┌─────────────────────────────┐
│  API Layer (FastAPI)        │ ← HTTP concerns
├─────────────────────────────┤
│  Service Layer (Business)   │ ← Core logic
├─────────────────────────────┤
│  Data Layer (SQLAlchemy)    │ ← Database
├─────────────────────────────┤
│  Infrastructure (Postgres)  │ ← Storage
└─────────────────────────────┘
```

**Service Composition**:
```python
class AgentExecutor:
    def __init__(self, agent: Agent, db: AsyncSession):
        self.agent = agent
        self.db = db
        self.embedding_service = EmbeddingService()
        self.rag_service = RAGService(db, agent.tenant_id)

    async def execute_with_rag(self, input_text: str):
        # Compose multiple services
        query_embedding = await self.embedding_service.generate_embedding(input_text)
        context = await self.rag_service.search(query_embedding)
        response = await self._execute_anthropic(context, input_text)
        return response
```

---

## Production Readiness

### What You Have ✅

- ✅ Async FastAPI with connection pooling
- ✅ Multi-tenant data model
- ✅ JWT authentication
- ✅ Service layer architecture
- ✅ RAG with pgvector
- ✅ Docker containerization
- ✅ Database migrations

### What to Add for Production

**High Priority**:

1. **Logging & Observability**
   ```python
   import structlog

   logger = structlog.get_logger()
   logger.info("agent_executed", agent_id=str(agent.id), latency_ms=latency)
   ```

2. **Rate Limiting**
   ```python
   from slowapi import Limiter

   limiter = Limiter(key_func=lambda: current_tenant.id)

   @limiter.limit("100/minute")
   @router.post("/agents/execute")
   async def execute_agent():
       pass
   ```

3. **Error Tracking**
   ```python
   import sentry_sdk

   sentry_sdk.init(
       dsn=settings.SENTRY_DSN,
       environment=settings.ENVIRONMENT,
   )
   ```

4. **Health Checks**
   ```python
   @app.get("/health/ready")
   async def readiness_check(db: AsyncSession = Depends(get_db)):
       # Check database
       await db.execute(text("SELECT 1"))

       # Check Redis
       await redis.ping()

       return {"status": "ready"}
   ```

**Medium Priority**:

5. **Background Jobs** (Celery + Redis)
   - For long-running agent executions
   - Document processing
   - Scheduled tasks

6. **Caching Layer**
   - Redis for API responses
   - LLM response caching
   - Embedding caching (already implemented)

7. **Request ID Tracing**
   ```python
   @app.middleware("http")
   async def add_request_id(request: Request, call_next):
       request_id = str(uuid.uuid4())
       request.state.request_id = request_id
       response = await call_next(request)
       response.headers["X-Request-ID"] = request_id
       return response
   ```

8. **Metrics** (Prometheus + Grafana)
   - Request latency
   - Token usage per tenant
   - Error rates
   - Database query performance

**Nice to Have**:

9. **API Documentation**
   - Improve OpenAPI descriptions
   - Add examples to schemas
   - Create Postman collection

10. **Integration Tests**
    ```python
    @pytest.mark.asyncio
    async def test_agent_execution():
        # Create test agent
        agent = await create_test_agent()

        # Execute
        response = await client.post(
            f"/v1/agents/{agent.id}/execute",
            json={"input": "Hello"}
        )

        assert response.status_code == 200
    ```

11. **Load Testing** (Locust)
    ```python
    class AgentUser(HttpUser):
        @task
        def execute_agent(self):
            self.client.post(
                "/v1/agents/test-agent/execute",
                json={"input": "Hello"}
            )
    ```

---

## Migration Roadmap

### Phase 1: MVP (Current) ✅

**Status**: Complete

**Features**:
- Single agent execution
- Multi-tenant data model (not enforced)
- Basic RAG support
- Docker Compose deployment

### Phase 2: Multi-Agent Orchestration

**Goal**: Multiple agents working together

**Architecture**:
```
User → Orchestrator → Agent A (Research)
                   ↓→ Agent B (Analysis)
                   ↓→ Agent C (Writing)
                   ↓
                Aggregator → Response
```

**Implementation**:
- **Workflow Engine**: Temporal or Apache Airflow
- **Message Bus**: RabbitMQ or Kafka
- **Agent Registry**: Track available agents
- **Coordination**: Graph-based workflow definitions

**Example Workflow**:
```python
# workflow.py
class ResearchWorkflow:
    async def run(self, query: str):
        # Step 1: Research agent gathers info
        research = await research_agent.execute(query)

        # Step 2: Analysis agent processes
        analysis = await analysis_agent.execute(research)

        # Step 3: Writing agent creates report
        report = await writing_agent.execute(analysis)

        return report
```

### Phase 3: True Multi-Tenancy

**Goal**: Enforce resource quotas and isolation

**Features**:
- Resource quotas (max_agents, max_requests_per_day)
- Rate limiting per tenant
- Billing integration (track token usage)
- Tenant admin portal

**Implementation**:
```python
# Rate limiting by tenant
@limiter.limit(lambda: f"{current_tenant.max_requests_per_day}/day")
@router.post("/agents/execute")
async def execute_agent():
    pass

# Usage tracking
@router.post("/agents/execute")
async def execute_agent():
    response = await executor.execute()

    # Track usage
    await usage_service.record(
        tenant_id=tenant.id,
        tokens_used=response.token_usage.total_tokens,
        cost=calculate_cost(response.token_usage)
    )

    return response
```

### Phase 4: Multi-Region

**Goal**: Global deployment with data locality

**Architecture**:
```
Global DNS → Route to nearest region
              ↓
       ┌──────┴──────┐
       │             │
   US Region     EU Region
   (read/write)  (read/write)
       │             │
       └─────┬───────┘
             │
    Data Replication
```

**Technologies**:
- **Database**: CockroachDB or Aurora Global
- **Load Balancing**: GeoDNS
- **Data Compliance**: Store EU data in EU only
- **Orchestration**: Multi-region Kubernetes

**Implementation Considerations**:
- Eventual consistency
- Cross-region latency
- Data residency requirements
- Failover strategy

---

## Key Design Decisions

### Decision 1: FastAPI over Django

**Rationale**: Async-first architecture for I/O-bound LLM calls

**Trade-offs**:
- ✅ Better performance for async workloads
- ✅ Modern type hints and validation
- ❌ Less mature ecosystem
- ❌ No built-in admin panel

### Decision 2: PostgreSQL + pgvector over Separate Vector DB

**Rationale**: Simplify infrastructure for MVP

**Trade-offs**:
- ✅ Single database to manage
- ✅ ACID transactions for metadata + vectors
- ✅ Cost-effective for <1M vectors
- ❌ Not optimized for billions of vectors
- ❌ Limited vector search features

**Migration Path**: When to move to Pinecone/Weaviate:
- >1M documents
- Need for advanced filtering
- Sub-10ms search latency required

### Decision 3: Row-Level Multi-Tenancy

**Rationale**: Balance isolation with simplicity

**Trade-offs**:
- ✅ Easy to implement
- ✅ Cost-effective (single DB)
- ✅ Simple migrations
- ❌ Risk of data leaks (must filter by tenant_id)
- ❌ Can't customize per tenant easily

**Mitigation**:
- Comprehensive tests
- Database views with RLS
- Query auditing

### Decision 4: Service Layer Pattern

**Rationale**: Separate business logic from HTTP concerns

**Trade-offs**:
- ✅ Testable (mock service, not HTTP)
- ✅ Reusable (CLI, webhooks, background jobs)
- ✅ Clear separation of concerns
- ❌ More files/classes
- ❌ Extra abstraction layer

### Decision 5: JWT over Session Cookies

**Rationale**: Stateless auth for scalability

**Trade-offs**:
- ✅ No session storage needed
- ✅ Works across multiple servers
- ✅ Can include claims (tenant_id, role)
- ❌ Cannot revoke until expiration
- ❌ Larger request size (token in header)

**Mitigation**:
- Short access token lifetime (24h)
- Long refresh token for convenience
- Token blacklist (Redis) for immediate revocation

---

## Appendix: Common Patterns

### Pattern 1: Dependency Injection

```python
# Define dependencies
async def get_db() -> AsyncSession:
    async with AsyncSessionLocal() as session:
        yield session

async def get_current_user(
    authorization: str = Header(),
    db: AsyncSession = Depends(get_db)
) -> User:
    return user

# Use in endpoints
@router.post("/agents")
async def create_agent(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    pass
```

### Pattern 2: Pydantic Validation

```python
class AgentCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    temperature: float = Field(default=0.7, ge=0.0, le=2.0)

    @model_validator(mode="after")
    def validate_model_config(self):
        if self.model_provider == "anthropic":
            assert self.model_name.startswith("claude-")
        return self
```

### Pattern 3: Async Context Managers

```python
@asynccontextmanager
async def database_transaction(db: AsyncSession):
    try:
        yield db
        await db.commit()
    except Exception:
        await db.rollback()
        raise
    finally:
        await db.close()

# Usage
async with database_transaction(db) as session:
    session.add(user)
```

### Pattern 4: Factory Pattern

```python
class LLMClientFactory:
    @staticmethod
    def create(provider: str):
        if provider == "anthropic":
            return Anthropic(api_key=settings.ANTHROPIC_API_KEY)
        elif provider == "openai":
            return OpenAI(api_key=settings.OPENAI_API_KEY)
        else:
            raise ValueError(f"Unknown provider: {provider}")
```

### Pattern 5: Repository Pattern

```python
class AgentRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_id(self, agent_id: UUID) -> Agent:
        return await self.db.get(Agent, agent_id)

    async def list_by_tenant(self, tenant_id: UUID) -> list[Agent]:
        result = await self.db.execute(
            select(Agent).where(Agent.tenant_id == tenant_id)
        )
        return result.scalars().all()
```

---

## Conclusion

This codebase demonstrates:

1. **Modern Python Patterns**: Async/await, type hints, Pydantic
2. **Production Architecture**: Service layers, dependency injection, connection pooling
3. **Scalability**: Multi-tenancy, connection pooling, async I/O
4. **AI/ML Integration**: LLM APIs, RAG, vector search
5. **DevOps Readiness**: Docker, migrations, health checks

**Next Steps**:
1. Add observability (logging, metrics, tracing)
2. Implement rate limiting and resource quotas
3. Build background job system for long tasks
4. Add comprehensive tests
5. Deploy to production (Kubernetes)

**Learning Resources**:
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [SQLAlchemy 2.0 Documentation](https://docs.sqlalchemy.org/en/20/)
- [Anthropic Claude API](https://docs.anthropic.com/)
- [pgvector Documentation](https://github.com/pgvector/pgvector)

---

*Generated: 2025-01-09*
*Version: 1.0*
