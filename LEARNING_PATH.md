# Agentic Platform Learning Path

This guide will help you understand the complete codebase, technologies, and architectural patterns used in building the Phase 1 MVP and Phase 2 enhancements. Follow this path to gain comprehensive knowledge of all concepts implemented.

## Implementation Status

### ✅ Phase 1: Foundation - Single Agent, Single Tenant (COMPLETED)
- Agent Runtime and execution environment
- Task Queue with Redis
- State Management with PostgreSQL
- API Gateway with REST endpoints
- LLM Integration (Anthropic Claude)
- JWT-based Authentication
- Multi-tenant database schema

### ✅ Phase 2: Multi-Agent + RAG + MCP + Workflows (COMPLETE - 100%)
- ✅ **RAG System** - Fully implemented and tested
  - Document processing pipeline
  - Vector embeddings with pgvector
  - Semantic search and retrieval
  - Collection and document management APIs
- ✅ **MCP (Model Context Protocol)** - Complete
  - ✅ Database schema (4 new models: MCPServer, MCPServerConfig, MCPToolExecution, MCPServerRegistry)
  - ✅ MCP client service with stdio-based JSON-RPC communication
  - ✅ Pydantic schemas for all MCP operations
  - ✅ Complete REST API endpoints (servers, configs, execution, discovery)
  - ✅ MCP server implementations (3 pre-built: Filesystem, Database, Calculator)
  - ✅ Base server framework for easy extension
  - ✅ Seed data script for quick setup
  - ✅ Comprehensive usage documentation with examples
- ✅ **Multi-Agent Orchestration & Workflows** - Complete
  - ✅ Database schema (5 new models: Workflow, WorkflowExecution, WorkflowStepExecution, AgentTask, AgentMessage)
  - ✅ Workflow engine service with full orchestration
  - ✅ Sequential and parallel execution support
  - ✅ Conditional branching with JSONPath expressions
  - ✅ Agent, MCP tool, and HTTP step types
  - ✅ Template variable resolution
  - ✅ Error handling and automatic retries
  - ✅ Complete API endpoints (18 endpoints)
  - ✅ Pydantic schemas (15 schemas)
  - ✅ 5 example workflow templates
  - ✅ Comprehensive usage documentation

### 📅 Phase 3: Production Readiness & Testing (Ready to Start)
### 📅 Phase 4: Multi-Region Deployment (Planned)

---

## Level 1: Foundation - Project Structure & Configuration

### Key Concepts

**Python Poetry for Dependency Management**
Poetry is a modern Python dependency and packaging tool that replaces pip and requirements.txt with a more robust solution. It uses `pyproject.toml` to declare dependencies with version constraints and automatically generates a `poetry.lock` file that pins exact versions for reproducible builds. Poetry also creates and manages virtual environments automatically, handles dependency resolution conflicts, and provides commands for publishing packages. This ensures that all developers and deployment environments use identical dependency versions, preventing the classic "works on my machine" problem.

**Environment Variables with Pydantic Settings**
Pydantic Settings extends Pydantic's validation capabilities to configuration management by automatically loading environment variables from .env files and validating them against type-annotated class fields. This provides runtime type checking for configuration values, automatic parsing of complex types (lists, dicts, URLs), and clear error messages when configuration is invalid or missing. The pattern separates configuration from code, supports multiple environments (development, staging, production), and prevents common bugs caused by misconfigured applications. Field validators can transform or validate values beyond simple type checking.

**Docker Compose for Multi-Service Orchestration**
Docker Compose defines and runs multi-container applications using a YAML configuration file. It allows you to declare all services (API, database, cache), their configurations, networks, volumes, and dependencies in a single file. When you run `docker-compose up`, it creates isolated networks for inter-service communication, manages startup order with health checks, mounts volumes for persistent data and hot-reload during development, and provides easy log aggregation. This eliminates the need to manually start multiple services and ensures consistent development environments across the team.

**Non-Root User in Docker for Security**
Running containers as root is a security risk because if an attacker compromises the container, they have root privileges. The Dockerfile creates a non-root user (`appuser`) and switches to it using the `USER` directive. This follows the principle of least privilege, limiting what an attacker can do if they exploit a vulnerability. The user still has access to application files but cannot modify system files or install packages. This is a Docker security best practice for production deployments.

### Files to Study

**pyproject.toml**
Contains all project metadata, dependencies with version constraints, development dependencies for testing and linting, and tool configurations for Black (code formatter), Ruff (linter), mypy (type checker), and pytest. The dependencies section shows all external packages used including FastAPI, SQLAlchemy, Anthropic SDK, and async drivers.

**docker-compose.yml**
Defines three services: PostgreSQL with pgvector extension for vector embeddings, Redis for caching and task queues, and the API service. Notice the `depends_on` configuration with health checks ensuring the database is ready before starting the API, the volume mounts for hot-reload during development, and environment variable passing.

**Dockerfile**
Shows the multi-stage build process: starting from Python 3.11 slim image, installing Poetry without creating a virtual environment (unnecessary in containers), copying only dependency files first for Docker layer caching optimization, then copying application code. The non-root user setup is at the end.

**.env.example**
Template for all required environment variables including database connection strings, Redis URL, JWT secrets, API keys for LLM providers, and configuration flags. Copy this to `.env` and fill in actual values for your environment.

**Makefile**
Provides shortcuts for common development tasks like starting/stopping Docker services, running migrations, seeding data, and accessing logs. Study the commands to understand the typical development workflow.

---

## Level 2: Database Layer - Models, Sessions & Migrations

### Key Concepts

**SQLAlchemy 2.0 Async with Declarative Models**
SQLAlchemy 2.0 introduced first-class support for async/await, allowing database operations to be non-blocking. The declarative base pattern uses Python classes to define database tables, where class attributes with `Mapped[]` type hints become table columns. The `mapped_column()` function specifies column properties like type, constraints, defaults, and indexes. Relationships between tables are defined using `relationship()` with back_populates for bidirectional navigation. This ORM approach provides type safety, automatic query generation, and migration support while keeping database schema in Python code instead of raw SQL.

**Mixin Pattern for Code Reuse**
Mixins are classes that provide reusable functionality to multiple model classes through multiple inheritance. Our codebase uses three mixins: `UUIDMixin` adds a UUID primary key to avoid sequential IDs (security) and support distributed systems, `TimestampMixin` adds created_at and updated_at fields with automatic server-side defaults and update triggers, and `SoftDeleteMixin` adds deleted_at for soft deletes allowing data recovery and audit trails. Models inherit from these mixins to get standard fields without code duplication, ensuring consistency across all tables.

**Multi-Tenant Architecture with Tenant Isolation**
Multi-tenancy allows a single application instance to serve multiple organizations (tenants) with data isolation. Every table except `tenants` has a `tenant_id` foreign key column with an index for query performance. All queries must filter by `tenant_id` to prevent data leakage between tenants. The API layer extracts the current tenant from the authenticated user and enforces this filter. This architecture scales efficiently (one database for all tenants) while maintaining strong data isolation for security and compliance. Composite indexes on (tenant_id, other_columns) optimize common queries.

**Alembic for Database Migrations**
Alembic is a database migration tool that tracks schema changes over time using versioned migration files. Each migration has an upgrade() function to apply changes and a downgrade() function to revert them. Alembic can auto-generate migrations by comparing the current database schema to your SQLAlchemy models, detecting added/removed tables and columns. The async configuration in `env.py` uses `run_async()` to work with async engines. Migrations are stored in version control and applied sequentially to ensure all environments have identical schemas.

**Connection Pooling for Performance**
Database connection pooling maintains a pool of reusable database connections instead of creating a new connection for each request. Creating connections is expensive (TCP handshake, authentication, session setup), so reusing them dramatically improves performance. SQLAlchemy's async engine configures pool_size (number of persistent connections) and max_overflow (additional connections under high load). The `get_db()` dependency function retrieves a connection from the pool, yields it to the request handler, commits on success, rolls back on error, and returns it to the pool.

**Soft Delete Pattern for Data Recovery**
Soft delete marks records as deleted using a `deleted_at` timestamp instead of physically removing them from the database. This preserves data for audit trails, allows recovery from accidental deletions, maintains referential integrity (foreign keys remain valid), and supports compliance requirements. Queries must filter `where(deleted_at.is_(None))` to exclude soft-deleted records. Hard deletes can be performed later during data archival processes. The pattern trades some storage space for operational safety and audit capabilities.

**Reserved Words Conflict (metadata → extra_metadata)**
SQLAlchemy reserves the word `metadata` for its internal MetaData object that stores table definitions. Attempting to use `metadata` as a column name causes conflicts. The solution was renaming all metadata columns to `extra_metadata` across models, schemas, and seed data. This is a common pitfall when migrating from other ORMs or designing schemas. Always check framework reserved words when naming fields.

### Files to Study

**src/db/base.py**
Contains the SQLAlchemy declarative base class and three mixins (UUIDMixin, TimestampMixin, SoftDeleteMixin) that provide reusable functionality. Study how `mapped_column()` defines columns with type hints, defaults, and constraints. Notice the use of `server_default` for database-level defaults and `func.now()` for timestamp handling.

**src/db/models.py**
Defines all 8 database models representing the complete schema: Tenant, User, Agent, Conversation, Message, ToolExecution, ApiKey, and AuditLog. Each model inherits from Base and appropriate mixins. Study the foreign key relationships, composite indexes for multi-tenant queries, JSON columns for flexible metadata storage, and the use of Enum types for status fields.

**src/db/session.py**
Creates the async SQLAlchemy engine with asyncpg driver and connection pool configuration. The `AsyncSessionLocal` factory creates database sessions. The `get_db()` dependency function manages session lifecycle: creating a session, yielding it to request handlers, committing on success, rolling back on exceptions, and ensuring cleanup. This pattern prevents connection leaks.

**alembic/env.py**
Configures Alembic for async migrations by importing all models (so Alembic knows the target schema), creating an async engine, and using `run_async()` to execute migrations. The `run_migrations_online()` function handles the actual migration application. Study how it loads the database URL from settings.

**alembic/versions/** (migration files)
The initial migration file shows the generated SQL DDL for creating all tables with their columns, constraints, indexes, and relationships. Review this to understand how SQLAlchemy models translate to actual PostgreSQL schema.

---

## Level 3: API Layer - FastAPI, Routing & Dependencies

### Key Concepts

**FastAPI Framework with Async Request Handlers**
FastAPI is a modern Python web framework built on Starlette (ASGI server) and Pydantic (validation). It uses Python type hints to automatically generate OpenAPI documentation, validate request/response data, serialize/deserialize JSON, and provide editor autocomplete. Async route handlers (`async def`) allow the server to handle multiple requests concurrently without blocking on I/O operations like database queries or external API calls. FastAPI automatically runs sync functions in a thread pool, but async handlers are more efficient for I/O-bound operations. The framework handles common web tasks like CORS, middleware, exception handling, and dependency injection.

**Dependency Injection Pattern**
FastAPI's Depends() system provides dependency injection, a pattern where functions declare their dependencies as parameters and the framework automatically resolves them. Dependencies can be database sessions, authenticated users, configuration objects, or service instances. Dependencies can depend on other dependencies, creating a dependency graph. This pattern promotes code reuse, testability (dependencies can be mocked), and separation of concerns. Common dependencies like `get_db()` for database sessions and `get_current_user()` for authentication are declared once and reused across all routes.

**JWT (JSON Web Tokens) for Stateless Authentication**
JWT is a self-contained token format that encodes user identity and claims in a JSON payload, signs it with a secret key, and base64-encodes the result. The server doesn't need to store session data (stateless) because the token contains all necessary information. When a user logs in, the server generates a JWT with the user ID as the subject (`sub` claim) and an expiration time (`exp` claim). On subsequent requests, the client sends the token in the Authorization header, the server verifies the signature and expiration, and extracts the user ID to authenticate the request. JWTs scale well because there's no server-side session storage, but they can't be invalidated before expiration (use refresh tokens for that).

**Password Hashing with bcrypt**
Storing plaintext passwords is a critical security vulnerability. Password hashing uses one-way cryptographic functions to convert passwords into irreversible hashes. bcrypt is specifically designed for password hashing with adaptive complexity (adjustable work factor) and built-in salt to prevent rainbow table attacks. When a user registers, their password is hashed and the hash is stored. During login, the provided password is hashed with the same algorithm and compared to the stored hash. Even if the database is compromised, attackers can't recover plaintext passwords. The work factor can be increased over time as computing power grows.

**APIRouter for Modular Route Organization**
APIRouter allows grouping related endpoints into modules (agents, conversations, auth) with common prefixes and tags. Each router is defined in its own file, then included in the main application with `app.include_router()`. This keeps the codebase organized as it grows, allows teams to work on different features independently, and enables selective mounting of routes (e.g., admin routes only in certain environments). Routers can have common dependencies, middleware, or response models applied to all their routes.

**Pydantic Schemas for Request/Response Validation**
Pydantic models (schemas) define the shape of request and response data with type hints and validation rules. FastAPI automatically validates incoming request bodies against the schema, returning a 422 error with detailed validation messages if the data is invalid. Field validators can enforce business rules (e.g., min/max length, regex patterns, custom logic). Response models ensure the API returns consistent data structures and automatically generate OpenAPI documentation. The `model_config = {"from_attributes": True}` setting allows creating Pydantic models from SQLAlchemy ORM objects by accessing attributes instead of dict keys.

**CORS (Cross-Origin Resource Sharing) Middleware**
Web browsers enforce the same-origin policy, preventing JavaScript from making requests to different origins (domain, protocol, or port) than the page was loaded from. CORS relaxes this restriction by using HTTP headers to allow specific origins. The CORSMiddleware intercepts preflight OPTIONS requests and adds appropriate headers. The `ALLOWED_ORIGINS` setting controls which frontend URLs can access the API. Setting it to `["*"]` allows all origins (useful for development, dangerous for production). Specific origins should be listed in production to prevent unauthorized access from malicious websites.

### Files to Study

**src/main.py**
The application entry point that creates the FastAPI app instance, configures CORS middleware with allowed origins, includes all API routers with the `/api/v1` prefix, and defines a health check endpoint. The `lifespan` context manager handles startup/shutdown events.

**src/api/v1/router.py**
Aggregates all version 1 API routers (auth, agents, conversations) and includes them in a single router that's mounted in main.py. This allows versioning the API by creating v2 routers alongside v1.

**src/api/v1/auth.py**
Implements the login endpoint that accepts email/password, queries the database for the user, verifies the password hash, generates a JWT access token, and returns it with user information. Study how database queries use async/await and error handling returns appropriate HTTP status codes.

**src/api/v1/agents.py**
Full CRUD implementation for agents: create, list with pagination, get by ID, update, delete (soft delete), and execute. Every query filters by `tenant_id` to enforce multi-tenant isolation. The execute endpoint creates or retrieves a conversation, initializes the AgentExecutor service, and returns the agent's response.

**src/api/v1/conversations.py**
Endpoints to list conversations with pagination, get a specific conversation with all messages (using selectinload to avoid N+1 queries), and delete conversations. Notice how relationships are eagerly loaded to prevent additional database queries.

**src/api/dependencies.py**
Defines reusable dependencies: `get_current_user()` extracts and validates the JWT token from the Authorization header, decodes it, fetches the user from the database, and returns the user object. `get_current_tenant()` retrieves the user's tenant. These are used throughout the API to ensure only authenticated requests with valid tenants can access resources.

**src/core/security.py**
Contains security utilities: `create_access_token()` generates JWTs with expiration times, `decode_token()` verifies and parses JWTs, `verify_password()` compares plaintext passwords with bcrypt hashes, and `get_password_hash()` hashes passwords for storage. Study the JWT payload structure and signing algorithm.

**src/core/config.py**
Pydantic Settings class that loads configuration from environment variables with type validation. Field validators transform raw strings into appropriate types (e.g., parsing comma-separated ALLOWED_ORIGINS). The settings instance is imported throughout the application to access configuration values.

---

## Level 4: Business Logic - Agent Execution & Services

### Key Concepts

**Service Layer Pattern for Business Logic**
The service layer separates business logic from API route handlers, keeping controllers thin and focused on HTTP concerns (request parsing, response formatting). Services contain the core application logic: orchestrating database operations, calling external APIs, implementing business rules, and coordinating between different domain models. This pattern improves testability (services can be tested without HTTP), reusability (multiple routes can use the same service), and maintainability (business logic is centralized). Services receive dependencies like database sessions through dependency injection.

**Anthropic Claude API Integration**
The Anthropic SDK provides a Python client for Claude LLMs. The client is initialized with an API key and uses async methods for non-blocking requests. The `messages.create()` method accepts parameters like model name (claude-sonnet-4-5), system prompt (instructions for the AI), messages (conversation history), max_tokens (response length limit), and temperature (randomness). The API returns the assistant's response with token usage metrics. Error handling catches API errors like authentication failures and rate limits. Streaming responses can be enabled for real-time output.

**Conversation History Management**
LLMs are stateless, so context must be maintained by sending the full conversation history with each request. The `_get_conversation_history()` method retrieves all messages for a conversation from the database and formats them as a list of role/content dictionaries. The order matters (chronological), and the format matches the API's expected structure. This allows the AI to reference previous messages and maintain coherent multi-turn conversations. Token limits constrain how much history can be sent, requiring truncation strategies for long conversations.

**Message Persistence and Token Tracking**
Every user input and AI response is saved to the database as a Message record with role (user/assistant), content (text), conversation_id (relationship), token_count (for usage tracking), and tool_calls (if any). Persisting messages enables conversation history retrieval, audit trails, debugging, analytics, and training data collection. Token usage tracking helps monitor API costs and optimize prompts. The `token_count` field stores the actual tokens consumed (from the API response) rather than estimates.

**Error Handling and Fallbacks**
Robust error handling prevents the entire application from crashing due to external service failures. The executor wraps API calls in try/except blocks, catching specific exceptions like `anthropic.AuthenticationError` for invalid API keys and `anthropic.RateLimitError` for quota exhaustion. Generic exception handlers catch unexpected errors. Errors are logged with context (agent ID, conversation ID) for debugging. Fallback strategies could include retrying with exponential backoff, using cached responses, or returning user-friendly error messages instead of exposing internal details.

### Files to Study

**src/services/agent_executor.py**
The core business logic for executing agents. Study the class structure with initialization taking agent and database session, the `execute()` method orchestrating the full flow (fetch history, save user message, call LLM, save response), the `_execute_anthropic()` method formatting the API request and handling the response, and helper methods for conversation history retrieval and message persistence.

**src/schemas/agent.py**
AgentExecuteRequest defines the input schema for agent execution: input text, optional conversation_id (for continuing conversations), optional context (additional data), stream flag (for streaming responses), and max_iterations override. AgentExecuteResponse defines the output: conversation_id, message_id, response text, tool_calls, token_usage, latency_ms, and timestamp.

**src/schemas/conversation.py**
ConversationResponse and MessageResponse schemas define the structure for retrieving conversation history. Notice the nested messages list with `model_config = {"from_attributes": True}` allowing SQLAlchemy models to be converted to Pydantic models.

---

## Level 5: Advanced Topics - Testing, Database Operations & Production Readiness

### Key Concepts

**Async/Await and Event Loop in Python**
Python's async/await enables concurrent execution of I/O-bound operations without threading complexity. When a function encounters an `await` statement (e.g., awaiting a database query), it yields control to the event loop, which can run other coroutines while waiting. This is particularly effective for web servers handling many concurrent requests that spend most of their time waiting for databases or external APIs. Unlike threads, async is single-threaded and avoids race conditions and context switching overhead. However, CPU-bound operations still block the event loop and should be offloaded to thread/process pools. Libraries must support async (asyncpg, httpx) or be run in executors.

**PostgreSQL with pgvector Extension**
pgvector adds vector similarity search capabilities to PostgreSQL, enabling storage and querying of high-dimensional embeddings (from models like OpenAI's text-embedding-ada-002). Vectors are stored as a new column type (`vector(1536)` for 1536-dimensional embeddings). Indexes like HNSW or IVFFlat enable fast approximate nearest neighbor search using distance metrics (cosine, L2, inner product). This supports RAG (Retrieval-Augmented Generation) where relevant documents are retrieved based on semantic similarity and provided as context to LLMs. Keeping vectors in PostgreSQL avoids maintaining separate vector databases and enables SQL joins between vectors and structured data.

**Redis for Caching and Task Queues**
Redis is an in-memory data store used for caching frequently accessed data (reducing database load), session storage (faster than database queries), distributed locking (coordinating between multiple servers), and task queues (with libraries like Celery). Caching agent responses or conversation history can dramatically reduce LLM API costs. Redis supports various data structures (strings, hashes, lists, sets) with atomic operations and TTL (time-to-live) for automatic expiration. The trade-off is data volatility (in-memory storage) and the need for cache invalidation strategies.

**Database Indexing for Query Performance**
Indexes are auxiliary data structures that speed up queries by allowing the database to locate rows without scanning the entire table. Our schema includes indexes on foreign keys (tenant_id, agent_id, conversation_id) because these are used in WHERE clauses and JOIN conditions frequently. Composite indexes on (tenant_id, other_column) optimize multi-tenant queries that filter by tenant first. Indexes trade write performance and storage space for read performance. Over-indexing slows down writes and wastes space, so indexes should target actual query patterns. EXPLAIN ANALYZE shows query plans and whether indexes are being used.

**Pagination for Large Result Sets**
Returning all results from large tables causes memory issues and slow response times. Pagination returns a subset of results (e.g., 20 items per page) using LIMIT and OFFSET in SQL. The response includes metadata like total count, current page, page size, and whether there are more pages. Offset-based pagination is simple but inefficient for large offsets (database must skip many rows). Cursor-based pagination using unique keys (e.g., last seen ID or timestamp) is more efficient and handles insertions/deletions better. Our implementation uses offset-based for simplicity, suitable for small to medium datasets.

**Soft Delete Considerations**
Soft deletes require updating all queries to filter out deleted records with `where(deleted_at.is_(None))`. Forgetting this filter leaks deleted data. Unique constraints become problematic (deleted usernames should be reusable, but the unique constraint includes deleted rows). Solutions include composite unique constraints with (column, deleted_at) or marking deleted rows with tombstone values. Soft deletes increase table size and slow down queries (more rows to filter), requiring periodic archival of old deleted records. Foreign key relationships must handle deleted parents (cascade soft deletes or allow nulls).

**Seeding Development Data**
Development databases need realistic test data for manual testing and development. Seed scripts create initial records: a demo tenant, admin user with known credentials, sample agents, and test conversations. Seeds should be idempotent (safe to run multiple times) by checking for existence before creating records or using UPSERT operations. Production databases should never be seeded automatically (security risk). Seed data helps developers quickly test features without manually creating data through the UI.

**Health Checks for Service Monitoring**
Health check endpoints allow monitoring systems and orchestrators (Kubernetes, Docker Compose) to verify services are running and healthy. A basic health check returns 200 OK if the server is responding. Advanced health checks test dependencies: database connectivity, external API availability, disk space, memory usage. Docker Compose uses health checks in `depends_on` to ensure services start in order (database ready before API). Load balancers use health checks to route traffic only to healthy instances. Failing health checks trigger alerts or automatic restarts.

### Files to Study

**scripts/seed_dev_data.py**
Creates development data including a demo tenant, admin user with hashed password, and a customer support agent with system prompt and capabilities. Study how it connects to the database asynchronously, creates records with relationships, and commits the transaction. Notice the use of password hashing and the structure of agent configuration.

**tests/** (if implemented)
Test files would show pytest fixtures for database sessions, test clients, authentication, and example test cases for API endpoints. Look for patterns like test database isolation, mocking external APIs, and assertion patterns.

**docker-compose.yml (services configuration)**
Study the health check configurations for PostgreSQL using `pg_isready` command and how the API service depends on PostgreSQL being healthy before starting. Notice volume mounts for code hot-reload during development and environment variable passing.

**src/db/models.py (indexes and relationships)**
Review the `__table_args__` sections showing composite indexes for multi-tenant queries, unique constraints, and check constraints. Study the `relationship()` definitions with `back_populates` for bidirectional navigation and cascade delete configurations.

---

## Level 6: RAG System - Document Processing & Vector Search

### Key Concepts

**Retrieval-Augmented Generation (RAG)**
RAG is a pattern that enhances LLM responses by retrieving relevant information from external knowledge bases and providing it as context. Instead of relying solely on the LLM's training data, RAG systems fetch relevant documents, chunk them into manageable pieces, convert them to vector embeddings, perform semantic similarity search against user queries, and inject the retrieved context into the LLM prompt. This grounds responses in factual data, reduces hallucinations, enables access to private/recent information, and allows updating knowledge without retraining models. RAG is essential for building AI assistants that need domain-specific knowledge.

**Vector Embeddings for Semantic Search**
Traditional keyword search fails to capture semantic meaning ("cheap car" won't match "affordable vehicle"). Embedding models (like OpenAI's text-embedding-3-small) convert text into high-dimensional vectors (arrays of numbers) where semantically similar texts have vectors close together in vector space. The distance between vectors (cosine similarity, L2 distance) measures semantic similarity. This enables searching by meaning rather than exact keywords, finding conceptually related documents, and supporting multilingual search with cross-lingual embeddings. Embeddings capture context, synonyms, and conceptual relationships that keyword matching misses.

**Document Chunking Strategies**
Large documents exceed LLM context windows and make retrieval less precise. Chunking splits documents into smaller pieces while preserving semantic coherence. Fixed-size chunking divides text into equal token/character lengths with overlap to avoid splitting important context across boundaries. Semantic chunking splits by natural boundaries (paragraphs, sections, sentences) preserving topical coherence. Recursive chunking handles hierarchical documents (markdown headings, code structure). Metadata preservation tags chunks with source document, page numbers, sections for provenance tracking. Chunk size trades granularity (smaller chunks = more precise retrieval but less context) against relevance (larger chunks = more context but may be less relevant).

**pgvector for PostgreSQL Vector Search**
pgvector extends PostgreSQL with vector data types and similarity search operators, eliminating the need for separate vector databases. The `vector(N)` type stores N-dimensional embeddings. Operators like `<=>` (cosine distance), `<->` (L2 distance), and `<#>` (inner product) enable similarity queries. Indexes (HNSW for high recall, IVFFlat for speed) make nearest-neighbor search fast even with millions of vectors. Integration with relational data allows joining vector similarity results with structured metadata, enforcing multi-tenant isolation, and using PostgreSQL's ACID guarantees and backup tools. This simplifies architecture and reduces operational complexity.

**Hybrid Search (Vector + Keyword)**
Pure vector search can miss exact matches (product codes, names) while pure keyword search misses semantic variations. Hybrid search combines both: perform vector similarity search for semantic relevance, perform full-text search for keyword matches, merge results with weighted ranking (e.g., 70% semantic + 30% keyword), and re-rank using a cross-encoder model for optimal results. This provides the best of both worlds: semantic understanding and exact matching. Implementation can use PostgreSQL's full-text search (tsvector) alongside pgvector or external search engines like Elasticsearch.

**Multi-Tenant RAG Isolation**
In multi-tenant RAG systems, each tenant's documents must be strictly isolated. Every collection, document, and chunk includes tenant_id with indexed filters ensuring queries never leak data across tenants. Row-level security in PostgreSQL can enforce isolation at the database level. Embeddings must be scoped per tenant to prevent cross-contamination. Shared collections (public knowledge bases) require explicit visibility controls. Multi-tenant RAG scales efficiently (single vector index for all tenants) while maintaining security through query filters.

**Document Processing Pipeline**
The pipeline handles diverse file formats (PDF, DOCX, TXT, MD, HTML, JSON, CSV) by extracting text using format-specific libraries (PyPDF for PDFs, python-docx for Word documents, BeautifulSoup for HTML). Content cleaning removes formatting artifacts, normalizes whitespace, handles special characters. Metadata extraction captures document properties (author, title, creation date) and structural information (headings, page numbers). Chunking applies the configured strategy. Embedding generation batches chunks to the embedding API with rate limiting and retries. Storage saves chunks, embeddings, and metadata to PostgreSQL. Status tracking monitors progress (processing, completed, failed) for async processing and error recovery.

**Embedding Service with Caching**
Embedding API calls are expensive (cost and latency). The embedding service batches multiple chunks into single API calls reducing request overhead and staying within rate limits. Content hashing (SHA-256) identifies identical text to avoid re-embedding duplicates. Cache storage uses Redis or database with hash as key. Model versioning tracks which embedding model generated each embedding, supporting migrations to newer models. Fallback models handle primary API failures. Async processing prevents blocking during uploads. Cost tracking monitors embedding API usage per tenant for billing.

### Files to Study

**src/db/models.py (RAG models)**
Defines five new models for RAG: `KnowledgeCollection` (groups of documents with embedding config), `Document` (uploaded files with metadata), `DocumentChunk` (text segments with embeddings), `RAGQuery` (query log for analytics), and `RAGSource` (tracks which chunks were used in responses). Study the `vector()` column type for embeddings, composite indexes on (tenant_id, collection_id), and relationship mappings between models.

**src/services/document_processor.py**
Implements the document processing pipeline with support for multiple file formats. The `DocumentProcessor` class detects file types using content type and magic bytes, extracts text using format-specific parsers, cleans and normalizes content, applies chunking strategies (fixed-size with overlap, semantic by paragraphs, sentence-based), counts tokens using tiktoken, and handles errors gracefully with detailed logging. Study the chunking algorithms and how overlap preserves context.

**src/services/embedding_service.py**
The `EmbeddingService` class generates vector embeddings using OpenAI's API with configurable models (text-embedding-3-small, text-embedding-3-large). Features include batch processing to optimize API usage, content hashing for deduplication, retry logic with exponential backoff for transient failures, error handling for API failures, and dimension validation ensuring embeddings match expected size. Study the async API calls and batch size optimization.

**src/services/rag_service.py**
The `RAGService` orchestrates all RAG operations: creating collections with embedding configuration, uploading documents (coordinating processor and embedding service), performing semantic search using pgvector's cosine similarity, filtering by metadata and similarity thresholds, formatting context for agent consumption (cited sources with metadata), and tracking queries for analytics. Study the vector similarity query construction using SQLAlchemy and pgvector operators.

**src/api/v1/rag.py**
REST API endpoints for RAG system: collection CRUD (`POST/GET/DELETE /collections`), document upload (`POST /collections/{id}/documents`), document listing (`GET /collections/{id}/documents`), semantic query (`POST /query`), and agent context (`POST /context`). Study the request/response schemas, authentication requirements, pagination implementation, and error handling. The `/context` endpoint formats results specifically for LLM consumption.

**src/schemas/rag.py**
Pydantic models defining RAG API contracts: `CollectionCreate` (name, description, embedding model, chunking config), `DocumentUpload` (file, title, source metadata), `RAGQueryRequest` (query text, collection filter, top_k, similarity threshold), `RAGQueryResponse` (results with scores, sources, retrieval time), and `RAGContextResponse` (formatted context string for LLM, source citations). Study the validation rules and default values.

### RAG Testing Guide

**1. Create a Knowledge Collection**
```bash
curl -X POST http://localhost:8000/v1/rag/collections \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Product Documentation",
    "description": "Technical product documentation",
    "embedding_model": "text-embedding-3-small",
    "chunk_size": 512,
    "chunk_overlap": 50
  }'
```

**2. Upload Documents**
```bash
curl -X POST http://localhost:8000/v1/rag/collections/{collection_id}/documents \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -F "file=@document.pdf" \
  -F "title=User Guide" \
  -F "source=docs.example.com"
```

**3. Query the Knowledge Base**
```bash
curl -X POST http://localhost:8000/v1/rag/query \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "How do I reset my password?",
    "collection_id": "COLLECTION_UUID",
    "top_k": 5,
    "similarity_threshold": 0.7,
    "include_content": true
  }'
```

**4. Get Context for Agent**
```bash
curl -X POST http://localhost:8000/v1/rag/context \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "What are the platform features?",
    "collection_ids": ["COLLECTION_UUID"],
    "top_k": 3
  }'
```

### Common RAG Issues and Solutions

**Issue: No results returned from queries**
- Cause: Similarity threshold too high, embeddings not generated (missing API key), empty collection
- Solution: Lower threshold to 0.3-0.5, verify OPENAI_API_KEY in .env, check document processing status

**Issue: Poor retrieval quality**
- Cause: Chunk size too large/small, no overlap, wrong embedding model
- Solution: Experiment with chunk size (256-1024 tokens), use 10-20% overlap, try different embedding models

**Issue: Slow query performance**
- Cause: No vector index, large result set, inefficient chunking
- Solution: Create HNSW index on embedding column, reduce top_k, optimize chunk count

**Issue: Out of memory during document upload**
- Cause: Large files processed synchronously, too many chunks in memory
- Solution: Implement streaming file processing, batch chunk insertion, use background tasks

---

## Recommended Learning Sequence

### Phase 1: Environment Setup (1-2 hours)
1. Install Docker Desktop and Poetry
2. Clone the repository and copy `.env.example` to `.env`
3. Fill in environment variables (database password, JWT secret, Anthropic API key)
4. Run `docker-compose up` and verify all services start
5. Run `make migrate` to apply database migrations
6. Run `make seed` to create development data
7. Test the health endpoint with `curl http://localhost:8000/health`

### Phase 2: Database Deep Dive (2-3 hours)
1. Read `src/db/base.py` to understand mixins and base classes
2. Study each model in `src/db/models.py`, paying attention to relationships and indexes
3. Connect to PostgreSQL with `docker-compose exec postgres psql -U postgres -d platform`
4. Run `\dt` to list tables and `\d agents` to see table structure
5. Examine the generated migration in `alembic/versions/`
6. Understand the multi-tenant isolation by querying with and without tenant_id filters

### Phase 3: API Layer Exploration (3-4 hours)
1. Open the auto-generated API docs at `http://localhost:8000/docs`
2. Test the login endpoint to get a JWT token
3. Use the token to authenticate other requests in the Swagger UI
4. Read `src/api/v1/auth.py` to understand login flow and JWT creation
5. Study `src/api/dependencies.py` to see how authentication and tenant extraction work
6. Read `src/api/v1/agents.py` endpoint by endpoint, correlating with the Swagger UI
7. Test creating, listing, updating, and deleting agents through the API

### Phase 4: Agent Execution Flow (2-3 hours)
1. Read `src/services/agent_executor.py` completely
2. Trace the execution flow: execute() → _get_conversation_history() → _execute_anthropic() → _save_message()
3. Use the API to execute an agent and observe the response structure
4. Check the database to see the created conversation and messages
5. Execute another message in the same conversation and verify history is preserved
6. Study the Anthropic API documentation to understand the request/response format
7. Experiment with different system prompts and temperature settings

### Phase 5: Advanced Concepts (2-3 hours)
1. Read about async/await in Python's official documentation
2. Study SQLAlchemy 2.0 async documentation and relationship patterns
3. Learn about JWT security considerations and token expiration strategies
4. Research multi-tenant architecture patterns and isolation strategies
5. Read about database indexing strategies and when to use composite indexes
6. Understand soft delete trade-offs and alternative patterns
7. Study Redis use cases and caching strategies

### Phase 6: RAG System Deep Dive (3-4 hours)
1. Study the RAG models in `src/db/models.py` (KnowledgeCollection, Document, DocumentChunk)
2. Read `src/services/document_processor.py` to understand chunking strategies
3. Understand embedding generation in `src/services/embedding_service.py`
4. Study semantic search implementation in `src/services/rag_service.py`
5. Test the RAG APIs using the examples in the testing guide
6. Create a collection and upload sample documents
7. Perform queries and observe how context is formatted for agents
8. Experiment with different chunk sizes and similarity thresholds

### Phase 6.5: MCP (Model Context Protocol) Deep Dive (2-3 hours)
1. Study the MCP models in `src/db/models.py` (MCPServer, MCPServerConfig, MCPToolExecution, MCPServerRegistry)
2. Read `src/services/mcp_client.py` to understand:
   - JSON-RPC communication over stdio
   - Server process management and lifecycle
   - Tool discovery and execution
   - Error handling and retries
3. Review `src/schemas/mcp.py` for all request/response schemas
4. Explore `src/api/v1/mcp.py` endpoints:
   - Server CRUD operations
   - Server configuration management
   - Tool execution API
   - Discovery and health check endpoints
5. Understand the MCP protocol flow:
   - Server initialization and capability discovery
   - Tool listing and schema validation
   - Tool execution with input/output handling
   - Connection management and health monitoring
6. Review `docs/mcp-implementation.md` for:
   - MCP architecture and design decisions
   - Pre-built server specifications
   - Multi-tenant considerations
   - Security and sandboxing requirements

### Phase 7: Code Modifications (3-4 hours)
1. Add a new field to the Agent model and create a migration
2. Update the schemas to include the new field
3. Modify the API endpoints to handle the new field
4. Create a new API endpoint for a custom agent operation
5. Integrate RAG context into agent execution
6. Add a new model for storing feedback on agent responses
7. Implement hybrid search combining vector and keyword search

### Total Estimated Time: 20-25 hours

This learning path takes you from zero to full understanding of the codebase and the technologies used. Each phase builds on the previous one, ensuring you have the necessary context before diving deeper.

---

## Key Files Quick Reference

### Configuration
- `pyproject.toml` - Dependencies and tool configuration
- `docker-compose.yml` - Multi-service orchestration
- `Dockerfile` - Container build instructions
- `.env.example` - Environment variable template
- `Makefile` - Development command shortcuts

### Database
- `src/db/base.py` - Base classes and mixins
- `src/db/models.py` - All database models (16 total: 8 core + 5 RAG + 4 MCP)
- `src/db/session.py` - Database connection and session management
- `alembic/env.py` - Migration configuration
- `alembic/versions/` - Migration history

### API
- `src/main.py` - Application entry point
- `src/api/v1/router.py` - Router aggregation
- `src/api/v1/auth.py` - Authentication endpoints
- `src/api/v1/agents.py` - Agent CRUD and execution
- `src/api/v1/conversations.py` - Conversation retrieval
- `src/api/v1/rag.py` - RAG collection and document endpoints
- `src/api/v1/mcp.py` - MCP server, config, and execution endpoints
- `src/api/dependencies.py` - Reusable dependencies

### Core
- `src/core/config.py` - Configuration management
- `src/core/security.py` - Authentication and password utilities

### Schemas
- `src/schemas/agent.py` - Agent request/response models
- `src/schemas/auth.py` - Authentication models
- `src/schemas/conversation.py` - Conversation models
- `src/schemas/rag.py` - RAG collection, document, and query models
- `src/schemas/mcp.py` - MCP server, config, execution, and registry models

### Services
- `src/services/agent_executor.py` - Agent execution business logic
- `src/services/rag_service.py` - RAG orchestration and semantic search
- `src/services/document_processor.py` - Document parsing and chunking
- `src/services/embedding_service.py` - Vector embedding generation
- `src/services/mcp_client.py` - MCP client and server process management

### Scripts
- `scripts/seed_dev_data.py` - Development data creation

---

## Common Development Tasks

### Starting the Development Environment
```bash
docker-compose up
# or for detached mode
docker-compose up -d
```

### Viewing Logs
```bash
docker-compose logs -f api
docker-compose logs -f postgres
```

### Running Migrations
```bash
# Create a new migration after model changes
docker-compose exec api alembic revision --autogenerate -m "description"

# Apply migrations
docker-compose exec api alembic upgrade head
```

### Accessing the Database
```bash
docker-compose exec postgres psql -U postgres -d platform
```

### Seeding Development Data
```bash
docker-compose exec api python scripts/seed_dev_data.py
```

### Running Code Formatters
```bash
docker-compose exec api black src/
docker-compose exec api ruff check src/ --fix
```

### Testing API Endpoints
```bash
# Login
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@demo.com","password":"admin123"}'

# List agents (replace TOKEN with JWT from login)
curl http://localhost:8000/api/v1/agents \
  -H "Authorization: Bearer TOKEN"
```

---

## Next Steps After Learning

Once you've completed this learning path, you'll be ready to:

### Phase 2 Completion:
1. ✅ ~~Implement RAG (Retrieval-Augmented Generation) with pgvector~~ - **COMPLETED**
2. 🚧 **MCP (Model Context Protocol) Implementation** - **PHASE 1/3 COMPLETE**
   - ✅ MCP Foundation (database, client, API) - **DONE**
   - ⏳ Build pre-built MCP servers (Filesystem, Database, Web Search)
   - ⏳ Integrate MCP tools with agent execution
   - ⏳ Create MCP server marketplace/registry
3. Build multi-agent orchestration system
4. Create workflow engine for agent coordination
5. Add inter-agent communication via message bus

### Platform Enhancements:
6. Integrate RAG context into agent execution automatically
7. Implement streaming responses for real-time agent output
8. Add support for tool calling and external integrations
9. Implement hybrid search (vector + keyword) for RAG
10. Build a frontend UI for the platform

### Production Readiness:
11. Add comprehensive test coverage (unit, integration, e2e)
12. Implement observability with logging, metrics, and tracing
13. Deploy to production with Kubernetes or cloud services
14. Add support for other LLM providers (OpenAI, Cohere, etc.)
15. Implement conversation summarization for token efficiency
16. Build analytics dashboards for agent performance
17. Add rate limiting and quota management per tenant
18. Implement data retention and archival policies

### Advanced Features:
19. Fine-tuning embeddings for domain-specific search
20. Implementing re-ranking models for better retrieval
21. Adding conversational memory compression
22. Building agent marketplace and sharing
23. Implementing A/B testing for prompts and configurations

Happy learning!
