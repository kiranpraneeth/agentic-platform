# Architecture Decision Records (ADR)

> **Purpose**: Document key architectural decisions, their context, and rationale
>
> **Format**: Based on Michael Nygard's ADR template
>
> **Last Updated**: 2025-01-09

---

## Table of Contents

1. [ADR-001: Use FastAPI for Web Framework](#adr-001-use-fastapi-for-web-framework)
2. [ADR-002: Use PostgreSQL with pgvector for Vector Storage](#adr-002-use-postgresql-with-pgvector-for-vector-storage)
3. [ADR-003: Implement Row-Level Multi-Tenancy](#adr-003-implement-row-level-multi-tenancy)
4. [ADR-004: Use JWT for Authentication](#adr-004-use-jwt-for-authentication)
5. [ADR-005: Implement Service Layer Pattern](#adr-005-implement-service-layer-pattern)
6. [ADR-006: Use SQLAlchemy 2.0 Async ORM](#adr-006-use-sqlalchemy-20-async-orm)
7. [ADR-007: Support Multiple Embedding Providers](#adr-007-support-multiple-embedding-providers)
8. [ADR-008: Use Alembic for Database Migrations](#adr-008-use-alembic-for-database-migrations)
9. [ADR-009: Implement Soft Deletes](#adr-009-implement-soft-deletes)
10. [ADR-010: Use Docker Compose for Development](#adr-010-use-docker-compose-for-development)

---

## ADR-001: Use FastAPI for Web Framework

**Status**: Accepted

**Date**: 2025-01-05

### Context

We need a web framework for building a REST API that:
- Handles high I/O workload (LLM API calls, database queries)
- Provides automatic API documentation
- Supports modern Python type hints
- Has strong async/await support
- Enables fast development iteration

**Options Considered**:
1. **FastAPI** - Modern async framework with Pydantic integration
2. **Django + DRF** - Mature, batteries-included framework
3. **Flask** - Lightweight, flexible microframework
4. **Node.js + Express** - JavaScript ecosystem, proven async

### Decision

We chose **FastAPI** for the following reasons:

**Strengths**:
- ✅ **Async-first architecture**: Native ASGI support, perfect for I/O-bound LLM operations
- ✅ **Automatic documentation**: OpenAPI/Swagger UI generated from code
- ✅ **Type safety**: Pydantic integration for request/response validation
- ✅ **Performance**: Among the fastest Python frameworks (comparable to Node.js)
- ✅ **Developer experience**: Excellent IDE support, auto-completion
- ✅ **Modern Python**: Uses Python 3.10+ features (type hints, async/await)

**Weaknesses**:
- ❌ Newer ecosystem (less mature than Django/Flask)
- ❌ No built-in admin panel (unlike Django)
- ❌ Smaller community compared to Django

### Consequences

**Positive**:
- Fast API development with automatic validation
- Built-in OpenAPI documentation reduces documentation overhead
- Async architecture handles concurrent LLM calls efficiently
- Type hints catch errors at development time

**Negative**:
- Team needs to learn async/await patterns
- Fewer third-party packages compared to Django
- Need to build admin functionality from scratch

**Mitigation**:
- Provide async/await training to team
- Use well-tested libraries (SQLAlchemy, Pydantic)
- Consider adding third-party admin panel if needed (e.g., FastAPI Admin)

### References

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Async Python Performance Comparison](https://www.techempower.com/benchmarks/)

---

## ADR-002: Use PostgreSQL with pgvector for Vector Storage

**Status**: Accepted

**Date**: 2025-01-05

### Context

We need to store and search vector embeddings for RAG (Retrieval-Augmented Generation). Requirements:
- Store 1536-dimensional vectors (OpenAI embeddings)
- Support fast similarity search (cosine distance)
- Handle up to 100,000 documents initially (scalable to 1M+)
- Maintain ACID properties for metadata and vectors together
- Keep infrastructure simple for MVP

**Options Considered**:
1. **PostgreSQL + pgvector** - SQL database with vector extension
2. **Pinecone** - Managed vector database (SaaS)
3. **Weaviate** - Open-source vector database
4. **Qdrant** - High-performance vector search engine
5. **Separate SQL + Vector DB** - PostgreSQL for metadata, Pinecone for vectors

### Decision

We chose **PostgreSQL with pgvector** for the following reasons:

**Strengths**:
- ✅ **Single database**: No need to manage separate vector store
- ✅ **ACID transactions**: Metadata and vectors in same transaction
- ✅ **Mature infrastructure**: PostgreSQL is battle-tested
- ✅ **Cost-effective**: No additional SaaS fees for MVP
- ✅ **Good performance**: HNSW index provides fast approximate search (<100ms for 100k vectors)
- ✅ **SQL queries**: Can join vectors with metadata easily

**Weaknesses**:
- ❌ Performance degrades beyond ~1M vectors
- ❌ Limited vector-specific features (no hybrid search, etc.)
- ❌ Not optimized specifically for vector workloads

### Consequences

**Positive**:
- Simplified infrastructure (one database to manage)
- Transactional consistency between documents and embeddings
- Lower operational costs during MVP phase
- Standard SQL backup/restore procedures apply

**Negative**:
- May need to migrate to dedicated vector DB at scale
- Performance ceiling at ~1M vectors
- Less flexible than specialized vector databases

**Migration Path**:

When to migrate to dedicated vector DB:
- Document count exceeds 1 million
- Search latency exceeds 100ms consistently
- Need for advanced features (hybrid search, filters)
- Multi-region deployment requires vector replication

**Recommended migration target**: Pinecone or Weaviate (based on scale needs)

### References

- [pgvector GitHub](https://github.com/pgvector/pgvector)
- [Vector Database Comparison](https://blog.det.life/why-you-shouldnt-invest-in-vector-databases-c0cd3f59d23c)

---

## ADR-003: Implement Row-Level Multi-Tenancy

**Status**: Accepted

**Date**: 2025-01-05

### Context

We need to support multiple tenants (organizations) sharing the same application. Requirements:
- Data isolation between tenants
- Cost-effective for 100-1000 tenants
- Simple to implement and maintain
- Allows per-tenant customization if needed
- Standard compliance (data residency may be needed later)

**Options Considered**:
1. **Row-level isolation** - Single database, tenant_id column on all tables
2. **Schema-per-tenant** - One PostgreSQL schema per tenant
3. **Database-per-tenant** - Separate database for each tenant
4. **Hybrid approach** - Different strategies for different tenant tiers

### Decision

We chose **Row-level multi-tenancy** for the following reasons:

**Strengths**:
- ✅ **Simple implementation**: Just add tenant_id to all tables
- ✅ **Cost-effective**: Single database instance for all tenants
- ✅ **Easy migrations**: One schema update applies to all tenants
- ✅ **Resource efficiency**: Shared connection pool, cache, indexes
- ✅ **Query flexibility**: Can aggregate across tenants for analytics

**Weaknesses**:
- ❌ **Data leak risk**: Must remember to filter by tenant_id in every query
- ❌ **Performance**: Large tenant can impact others (noisy neighbor)
- ❌ **Limited customization**: Hard to customize schema per tenant

### Consequences

**Positive**:
- Fast MVP development
- Simple deployment (single database)
- Low operational overhead
- Easy to add analytics/reporting across tenants

**Negative**:
- Risk of accidental cross-tenant data access
- Performance isolation limited
- Difficult to move specific tenant to dedicated infrastructure

**Mitigation Strategies**:

1. **Mandatory tenant_id filtering**:
   ```python
   # Always filter by tenant_id
   query = select(Agent).where(
       Agent.tenant_id == current_tenant.id,
       Agent.id == agent_id
   )
   ```

2. **Database-level Row-Level Security** (future):
   ```sql
   CREATE POLICY tenant_isolation ON agents
       USING (tenant_id = current_setting('app.current_tenant_id')::uuid);
   ```

3. **Automated testing**:
   ```python
   # Test that queries don't leak across tenants
   @pytest.mark.asyncio
   async def test_tenant_isolation():
       tenant_a_agent = await create_agent(tenant_a)
       tenant_b_agents = await list_agents(tenant_b)
       assert tenant_a_agent not in tenant_b_agents
   ```

4. **Query auditing**: Log all queries to detect missing tenant_id filters

5. **Resource quotas**: Implement per-tenant rate limiting and usage caps

**Migration Path**:

When to migrate to schema-per-tenant or database-per-tenant:
- Large enterprise customer requires dedicated infrastructure
- Regulatory requirement for data isolation (HIPAA, GDPR)
- Need per-tenant schema customization
- Specific tenant causing performance issues

### References

- [Multi-Tenant Database Patterns](https://docs.microsoft.com/en-us/azure/architecture/guide/multitenant/approaches/tenant-isolation)
- [PostgreSQL Row-Level Security](https://www.postgresql.org/docs/current/ddl-rowsecurity.html)

---

## ADR-004: Use JWT for Authentication

**Status**: Accepted

**Date**: 2025-01-05

### Context

We need an authentication mechanism that:
- Works in stateless microservices architecture
- Scales horizontally (multiple API servers)
- Supports both web and mobile clients
- Includes user and tenant information in token
- Allows token refresh without re-authentication

**Options Considered**:
1. **JWT (JSON Web Tokens)** - Stateless tokens signed by server
2. **Session cookies** - Server-side session storage
3. **OAuth 2.0** - Delegated authorization framework
4. **API Keys** - Simple token-based auth

### Decision

We chose **JWT** for the following reasons:

**Strengths**:
- ✅ **Stateless**: No server-side session storage needed
- ✅ **Scalable**: Works across multiple API servers without shared state
- ✅ **Self-contained**: Token includes all necessary claims (user_id, tenant_id, role)
- ✅ **Standard**: Well-documented, widely supported
- ✅ **Flexible**: Can add custom claims as needed

**Weaknesses**:
- ❌ **Cannot revoke**: Token valid until expiration
- ❌ **Larger payload**: Token included in every request header
- ❌ **Security risk**: If leaked, valid until expiration

### Consequences

**Positive**:
- Simple horizontal scaling (no session replication needed)
- Fast authentication (no database lookup per request)
- Works seamlessly with mobile apps and SPAs
- Can include tenant context in token

**Negative**:
- Cannot immediately revoke compromised tokens
- Larger HTTP request size (~200-500 bytes per request)
- Need to implement token refresh mechanism

**Mitigation Strategies**:

1. **Short-lived access tokens** (24 hours):
   ```python
   ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24  # 24 hours
   ```

2. **Refresh tokens** (7 days):
   ```python
   REFRESH_TOKEN_EXPIRE_MINUTES = 60 * 24 * 7  # 7 days
   ```

3. **Token blacklist** (Redis):
   ```python
   # For immediate revocation if needed
   async def revoke_token(token_jti: str):
       await redis.setex(
           f"blacklist:{token_jti}",
           ACCESS_TOKEN_EXPIRE_MINUTES * 60,
           "revoked"
       )
   ```

4. **Token validation**:
   ```python
   # Check token type, expiration, user status
   async def get_current_user(token: str):
       payload = jwt.decode(token, SECRET_KEY)
       user = await db.get(User, payload["sub"])
       if user.status != "active":
           raise HTTPException(403)
       return user
   ```

5. **Secure storage**:
   - Access token: Memory only (cleared on page refresh)
   - Refresh token: HttpOnly cookie (not accessible to JavaScript)

### Token Structure

```json
{
  "header": {
    "alg": "HS256",
    "typ": "JWT"
  },
  "payload": {
    "sub": "user-uuid",
    "exp": 1735689600,
    "type": "access",
    "tenant_id": "tenant-uuid",
    "role": "user"
  },
  "signature": "..."
}
```

### References

- [JWT.io](https://jwt.io/)
- [JWT Best Practices](https://tools.ietf.org/html/rfc8725)

---

## ADR-005: Implement Service Layer Pattern

**Status**: Accepted

**Date**: 2025-01-06

### Context

We need to organize business logic in a way that:
- Keeps API endpoints thin (routing only)
- Makes code testable without HTTP layer
- Allows reuse of logic across different entry points (API, CLI, background jobs)
- Maintains clear separation of concerns
- Supports future microservices architecture

**Options Considered**:
1. **Service Layer** - Separate classes for business logic
2. **Fat Models** - Business logic in ORM models (Django style)
3. **Handlers/Controllers** - Logic in API route handlers
4. **Domain-Driven Design (DDD)** - Full DDD with repositories, aggregates, etc.

### Decision

We chose **Service Layer pattern** for the following reasons:

**Strengths**:
- ✅ **Testability**: Can test business logic without HTTP layer
- ✅ **Reusability**: Same logic callable from API, CLI, background jobs
- ✅ **Separation of concerns**: API layer handles HTTP, service layer handles business logic
- ✅ **Clear architecture**: Easy to understand code organization
- ✅ **Future-proof**: Can extract services into microservices later

**Weaknesses**:
- ❌ **More files**: Additional layer compared to fat controllers
- ❌ **Potential over-engineering**: Simple CRUD may not need services
- ❌ **Abstraction overhead**: Extra function calls

### Consequences

**Positive**:
- API endpoints become simple routing + validation
- Business logic is testable with unit tests (no HTTP mocking)
- Easy to add CLI commands, background jobs using same logic
- Clear dependency injection points

**Negative**:
- More initial boilerplate code
- Developers must understand layered architecture
- May be overkill for very simple endpoints

**Implementation Guidelines**:

1. **API Layer** - HTTP concerns only:
   ```python
   @router.post("/agents/execute")
   async def execute_agent(
       agent_id: UUID,
       request: ExecuteRequest,
       tenant: CurrentTenant,
       db: AsyncSession = Depends(get_db),
   ):
       # 1. Get agent
       agent = await db.get(Agent, agent_id)

       # 2. Delegate to service
       executor = AgentExecutor(agent, db)
       response = await executor.execute(request.input)

       # 3. Return response
       return response
   ```

2. **Service Layer** - Business logic:
   ```python
   class AgentExecutor:
       def __init__(self, agent: Agent, db: AsyncSession):
           self.agent = agent
           self.db = db
           self.llm_client = self._init_llm_client()

       async def execute(self, input_text: str) -> AgentResponse:
           # All business logic here
           conversation_history = await self._get_history()
           llm_response = await self._call_llm(input_text, conversation_history)
           await self._save_response(llm_response)
           return llm_response
   ```

3. **Data Layer** - Database operations:
   ```python
   # ORM models handle only database mapping
   class Agent(Base):
       __tablename__ = "agents"
       id: Mapped[uuid.UUID] = mapped_column(UUID, primary_key=True)
       name: Mapped[str] = mapped_column(String(255))
   ```

**When to Use Services**:
- ✅ Complex business logic (agent execution, RAG)
- ✅ Multiple steps or external API calls
- ✅ Logic reused across endpoints
- ❌ Simple CRUD (can be inline in endpoint)
- ❌ Single database query with no logic

### References

- [Patterns of Enterprise Application Architecture](https://martinfowler.com/eaaCatalog/serviceLayer.html)
- [Clean Architecture](https://blog.cleancoder.com/uncle-bob/2012/08/13/the-clean-architecture.html)

---

## ADR-006: Use SQLAlchemy 2.0 Async ORM

**Status**: Accepted

**Date**: 2025-01-06

### Context

We need an ORM that:
- Supports async/await (non-blocking I/O)
- Provides type safety with Python type hints
- Works well with FastAPI's async architecture
- Offers migrations support
- Has good PostgreSQL support

**Options Considered**:
1. **SQLAlchemy 2.0 Async** - Modern async ORM with type hints
2. **SQLAlchemy 1.4 + asyncpg** - Older version with async support
3. **Tortoise ORM** - Async-first ORM inspired by Django
4. **Prisma Python** - Type-safe database client
5. **Raw asyncpg** - Direct PostgreSQL driver (no ORM)

### Decision

We chose **SQLAlchemy 2.0 Async** for the following reasons:

**Strengths**:
- ✅ **Async native**: Built-in async/await support with asyncpg driver
- ✅ **Type safety**: New `Mapped[T]` syntax integrates with mypy
- ✅ **Mature**: SQLAlchemy is the most popular Python ORM
- ✅ **Flexible**: Supports both ORM and Core (SQL builder)
- ✅ **PostgreSQL features**: Excellent support for JSON, arrays, pgvector
- ✅ **Migrations**: Works seamlessly with Alembic

**Weaknesses**:
- ❌ **Complexity**: Learning curve for advanced features
- ❌ **Verbose**: More code compared to Django ORM
- ❌ **N+1 queries**: Must explicitly use `selectinload` to avoid

### Consequences

**Positive**:
- Non-blocking database queries (important for concurrent LLM calls)
- Type hints catch errors at development time
- Excellent PostgreSQL support (JSON, vectors, full-text search)
- Can drop down to raw SQL when needed

**Negative**:
- Requires understanding of async patterns
- More verbose than simpler ORMs
- Need to be careful about N+1 query problems

**Best Practices**:

1. **Always use async session**:
   ```python
   async def get_db():
       async with AsyncSessionLocal() as session:
           yield session
   ```

2. **Use type hints**:
   ```python
   class Agent(Base):
       name: Mapped[str] = mapped_column(String(255))
       # NOT: name = Column(String(255))
   ```

3. **Eager load relationships**:
   ```python
   # Good: Eager loading
   result = await db.execute(
       select(Conversation)
       .options(selectinload(Conversation.messages))
       .where(Conversation.id == conv_id)
   )

   # Bad: N+1 queries
   conversation = await db.get(Conversation, conv_id)
   for message in conversation.messages:  # Separate query per message!
       print(message.content)
   ```

4. **Use connection pooling**:
   ```python
   engine = create_async_engine(
       DATABASE_URL,
       pool_size=20,
       max_overflow=10
   )
   ```

### References

- [SQLAlchemy 2.0 Documentation](https://docs.sqlalchemy.org/en/20/)
- [SQLAlchemy Async Guide](https://docs.sqlalchemy.org/en/20/orm/extensions/asyncio.html)

---

## ADR-007: Support Multiple Embedding Providers

**Status**: Accepted

**Date**: 2025-01-07

### Context

We need to generate text embeddings for RAG. Requirements:
- Quality embeddings for semantic search
- Cost-effective for development and small deployments
- Fast generation (low latency)
- Option to run offline (no API dependency)
- Ability to upgrade quality without code changes

**Options Considered**:
1. **OpenAI only** - Use OpenAI text-embedding-3-small
2. **Local only** - Use sentence-transformers (all-MiniLM-L6-v2)
3. **Dual provider** - Support both OpenAI and local models
4. **Multiple providers** - Add Cohere, Voyage, etc.

### Decision

We chose **Dual provider (OpenAI + Local)** for the following reasons:

**Strengths**:
- ✅ **Development flexibility**: Use local models during development (free)
- ✅ **Production quality**: Use OpenAI for better results in production
- ✅ **Offline support**: Can run without internet (local models)
- ✅ **Cost control**: Choose based on budget
- ✅ **Easy migration**: Change provider with config, not code

**Weaknesses**:
- ❌ **Compatibility**: Different models have different dimensions
- ❌ **Consistency**: Can't mix embeddings from different models in same collection
- ❌ **Complexity**: Need to maintain both integrations

### Consequences

**Positive**:
- Developers can work offline with local models
- Can start free (local) and upgrade to paid (OpenAI) later
- Easy to A/B test embedding quality
- No vendor lock-in

**Negative**:
- Must manage model compatibility (dimensions)
- Cannot change embedding model after data is indexed
- Need to support both code paths

**Implementation**:

```python
class EmbeddingService:
    def __init__(self, model: str = "all-MiniLM-L6-v2", provider: str = "local"):
        if provider == "local":
            from sentence_transformers import SentenceTransformer
            self._local_model = SentenceTransformer(model)
        elif provider == "openai":
            from openai import AsyncOpenAI
            self.client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)

    async def generate_embedding(self, text: str) -> list[float]:
        if self.provider == "local":
            embedding = await asyncio.to_thread(
                self._local_model.encode, text
            )
            return embedding.tolist()
        elif self.provider == "openai":
            response = await self.client.embeddings.create(
                model=self.model, input=text
            )
            return response.data[0].embedding
```

**Cost Comparison**:

| Provider | Model | Dimensions | Cost/1M tokens | Quality | Offline |
|----------|-------|-----------|---------------|---------|---------|
| **Local** | all-MiniLM-L6-v2 | 384 | $0 | Good | ✅ |
| **Local** | all-mpnet-base-v2 | 768 | $0 | Better | ✅ |
| **OpenAI** | text-embedding-3-small | 1536 | $0.02 | Best | ❌ |
| **OpenAI** | text-embedding-3-large | 3072 | $0.13 | Excellent | ❌ |

**Migration Path**:

To change embedding model:
1. Create new collection with new model
2. Re-process all documents
3. Update queries to use new collection
4. Delete old collection (after validation)

**Important**: Never change embedding model on existing collection (embeddings are not comparable)

### References

- [Sentence Transformers](https://www.sbert.net/)
- [OpenAI Embeddings Guide](https://platform.openai.com/docs/guides/embeddings)
- [Embedding Model Comparison](https://huggingface.co/spaces/mteb/leaderboard)

---

## ADR-008: Use Alembic for Database Migrations

**Status**: Accepted

**Date**: 2025-01-06

### Context

We need a database migration system that:
- Versions database schema changes
- Supports rollbacks (up and down migrations)
- Works with SQLAlchemy models
- Handles team collaboration (merge conflicts)
- Supports production deployments (zero-downtime)

**Options Considered**:
1. **Alembic** - SQLAlchemy's official migration tool
2. **Django migrations** - Built into Django
3. **Flyway** - Java-based migration tool
4. **Manual SQL scripts** - Hand-written migration files

### Decision

We chose **Alembic** for the following reasons:

**Strengths**:
- ✅ **SQLAlchemy native**: Works seamlessly with our ORM
- ✅ **Auto-generate**: Can detect model changes and generate migrations
- ✅ **Version control**: Migration files checked into Git
- ✅ **Rollback support**: Up and down migrations
- ✅ **Team-friendly**: Handles multiple branches with merge migrations

**Weaknesses**:
- ❌ **Python only**: Not useful if we add non-Python services
- ❌ **Auto-generate limitations**: May miss complex changes
- ❌ **Learning curve**: Requires understanding of Alembic concepts

### Consequences

**Positive**:
- Schema changes tracked in version control
- Easy collaboration (migrations are code)
- Automated deployment (run migrations before code deploy)
- Rollback capability for failed deployments

**Negative**:
- Must review auto-generated migrations (may be incorrect)
- Merge conflicts when multiple developers change schema
- Production migrations require careful planning

**Best Practices**:

1. **Always review auto-generated migrations**:
   ```bash
   # Generate migration
   alembic revision --autogenerate -m "add user_role"

   # Review the generated file
   cat alembic/versions/xxx_add_user_role.py

   # Test migration
   alembic upgrade head
   alembic downgrade -1  # Test rollback
   ```

2. **Add data migrations when needed**:
   ```python
   def upgrade():
       # Schema change
       op.add_column('users', sa.Column('role', sa.String(50)))

       # Data migration
       op.execute("UPDATE users SET role = 'user' WHERE role IS NULL")

       # Make non-nullable
       op.alter_column('users', 'role', nullable=False)
   ```

3. **Use descriptive names**:
   ```bash
   # Good
   alembic revision -m "add_email_verification_to_users"

   # Bad
   alembic revision -m "update_users"
   ```

4. **Test rollback before deploying**:
   ```bash
   # On staging
   alembic upgrade head    # Apply migration
   alembic downgrade -1    # Test rollback
   alembic upgrade head    # Re-apply
   ```

**Production Deployment Process**:

```bash
# 1. Backup database
pg_dump agentic_platform > backup.sql

# 2. Run migrations
alembic upgrade head

# 3. Deploy new code
docker-compose up -d --build

# 4. If issues occur, rollback
alembic downgrade -1
# Deploy old code
```

### References

- [Alembic Documentation](https://alembic.sqlalchemy.org/)
- [Database Migration Best Practices](https://www.brunton-spall.co.uk/post/2014/05/06/database-migrations-done-right/)

---

## ADR-009: Implement Soft Deletes

**Status**: Accepted

**Date**: 2025-01-06

### Context

We need a deletion strategy that:
- Preserves data for audit trails
- Allows "undo" functionality
- Maintains referential integrity
- Supports compliance requirements (data retention)
- Doesn't break existing functionality

**Options Considered**:
1. **Soft delete** - Add deleted_at timestamp, filter out in queries
2. **Hard delete** - Actually remove records from database
3. **Archive tables** - Move deleted records to separate tables
4. **Hybrid** - Soft delete for X days, then hard delete

### Decision

We chose **Soft delete** for the following reasons:

**Strengths**:
- ✅ **Audit trail**: Can see who deleted what and when
- ✅ **Undo capability**: Can restore deleted records
- ✅ **Compliance**: Meets data retention requirements
- ✅ **Referential integrity**: Foreign keys still valid
- ✅ **Analytics**: Can analyze deleted data

**Weaknesses**:
- ❌ **Database bloat**: Deleted records still take space
- ❌ **Query complexity**: Must filter deleted_at IS NULL everywhere
- ❌ **Unique constraints**: Must include deleted_at in unique indexes

### Consequences

**Positive**:
- Accidental deletions can be recovered
- Complete audit history of all operations
- Compliance with data retention policies
- Can analyze reasons for deletions

**Negative**:
- Database grows larger over time
- Must remember to filter deleted records in every query
- Unique constraints become more complex

**Implementation**:

1. **Mixin for soft deletes**:
   ```python
   class SoftDeleteMixin:
       deleted_at: Mapped[datetime | None] = mapped_column(
           DateTime(timezone=True),
           nullable=True
       )
   ```

2. **Always filter deleted records**:
   ```python
   # Good
   result = await db.execute(
       select(Agent).where(
           Agent.tenant_id == tenant_id,
           Agent.deleted_at.is_(None)
       )
   )

   # Bad (includes deleted)
   result = await db.execute(
       select(Agent).where(Agent.tenant_id == tenant_id)
   )
   ```

3. **Soft delete operation**:
   ```python
   @router.delete("/agents/{agent_id}")
   async def delete_agent(agent_id: UUID, db: AsyncSession):
       agent = await db.get(Agent, agent_id)
       agent.deleted_at = datetime.utcnow()
       await db.commit()
   ```

4. **Restore operation**:
   ```python
   @router.post("/agents/{agent_id}/restore")
   async def restore_agent(agent_id: UUID, db: AsyncSession):
       agent = await db.get(Agent, agent_id)
       agent.deleted_at = None
       await db.commit()
   ```

5. **Hard delete (admin only)**:
   ```python
   @router.delete("/admin/agents/{agent_id}/purge")
   async def purge_agent(agent_id: UUID, db: AsyncSession):
       agent = await db.get(Agent, agent_id)
       await db.delete(agent)  # Actually remove from database
       await db.commit()
   ```

**Maintenance**:

Archive old soft-deleted records:
```sql
-- Archive records deleted > 90 days ago
INSERT INTO agents_archive
SELECT * FROM agents
WHERE deleted_at < NOW() - INTERVAL '90 days';

DELETE FROM agents
WHERE deleted_at < NOW() - INTERVAL '90 days';
```

**Unique Constraints**:

Include deleted_at in unique constraints:
```python
__table_args__ = (
    # Allows same slug if one is deleted
    Index("idx_agents_tenant_slug", "tenant_id", "slug", "deleted_at", unique=True),
)
```

### References

- [Soft Delete Pattern](https://www.jamesserra.com/archive/2015/04/soft-deletes/)
- [PostgreSQL Soft Deletes](https://brandur.org/soft-deletion)

---

## ADR-010: Use Docker Compose for Development

**Status**: Accepted

**Date**: 2025-01-06

### Context

We need a local development environment that:
- Runs all services (API, Postgres, Redis)
- Is easy to set up for new developers
- Matches production environment
- Supports rapid iteration
- Works on macOS, Linux, and Windows

**Options Considered**:
1. **Docker Compose** - Multi-container orchestration
2. **Minikube** - Local Kubernetes cluster
3. **Manual setup** - Install Postgres, Redis locally
4. **Vagrant** - Virtual machine with services

### Decision

We chose **Docker Compose** for the following reasons:

**Strengths**:
- ✅ **Simple setup**: One command to start all services
- ✅ **Consistent**: Same environment for all developers
- ✅ **Isolated**: Doesn't conflict with other local services
- ✅ **Declarative**: Configuration as code (docker-compose.yml)
- ✅ **Fast iteration**: Hot reload for code changes

**Weaknesses**:
- ❌ **Not production**: Production uses Kubernetes (different orchestration)
- ❌ **Resource heavy**: Runs all services locally
- ❌ **Networking complexity**: Learning curve for Docker networking

### Consequences

**Positive**:
- New developers onboard in minutes
- Consistent development environment across team
- Easy to add new services (just update docker-compose.yml)
- Can test multi-service interactions locally

**Negative**:
- Development environment differs from production (Kubernetes)
- Requires Docker installed (not always available on corporate machines)
- Can be slow on older machines

**Configuration**:

```yaml
version: '3.8'

services:
  postgres:
    image: postgres:16
    environment:
      POSTGRES_DB: agentic_platform
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: postgres
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"

  redis:
    image: redis:7-alpine
    volumes:
      - redis_data:/data
    ports:
      - "6379:6379"

  api:
    build: .
    ports:
      - "8000:8000"
    depends_on:
      - postgres
      - redis
    environment:
      DATABASE_URL: postgresql+asyncpg://postgres:postgres@postgres:5432/agentic_platform
      REDIS_URL: redis://redis:6379
    volumes:
      - ./src:/app/src  # Hot reload

volumes:
  postgres_data:
  redis_data:
```

**Usage**:

```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f api

# Stop all services
docker-compose down

# Rebuild after dependency changes
docker-compose up -d --build

# Run migrations
docker-compose exec api alembic upgrade head

# Run tests
docker-compose exec api pytest
```

**Production Deployment**:

For production, migrate to Kubernetes:
```yaml
# kubernetes/deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: api
spec:
  replicas: 3
  template:
    spec:
      containers:
      - name: api
        image: your-registry/agentic-platform:latest
```

### References

- [Docker Compose Documentation](https://docs.docker.com/compose/)
- [Local Development with Docker](https://www.docker.com/blog/containerized-python-development-part-1/)

---

## Summary of Decisions

| ADR | Decision | Status | Impact |
|-----|----------|--------|--------|
| 001 | FastAPI | Accepted | High - Core framework |
| 002 | PostgreSQL + pgvector | Accepted | High - Data storage strategy |
| 003 | Row-Level Multi-Tenancy | Accepted | High - Architecture pattern |
| 004 | JWT Authentication | Accepted | Medium - Security approach |
| 005 | Service Layer Pattern | Accepted | Medium - Code organization |
| 006 | SQLAlchemy 2.0 Async | Accepted | High - Data access layer |
| 007 | Multi-Provider Embeddings | Accepted | Medium - AI integration |
| 008 | Alembic Migrations | Accepted | Medium - Database evolution |
| 009 | Soft Deletes | Accepted | Low - Data retention |
| 010 | Docker Compose Dev | Accepted | Low - Developer experience |

---

## Future ADRs

**Pending Decisions**:
1. Background job system (Celery vs Temporal)
2. Caching strategy (Redis usage patterns)
3. Observability stack (Prometheus + Grafana vs Datadog)
4. Multi-region deployment strategy
5. Rate limiting implementation
6. WebSocket support for streaming responses

---

*Generated: 2025-01-09*
*Version: 1.0*
