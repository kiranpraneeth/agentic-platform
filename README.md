# Agentic Platform - Production Ready

Multi-tenant AI agentic platform with RAG, MCP, and workflow orchestration. Built with FastAPI, PostgreSQL, Redis, and Anthropic Claude. **Phases 1-3 Complete**.

## Features

### ✅ Phase 1: Foundation (Complete)
- **Agent Management**: Create, configure, and manage AI agents
- **Agent Execution**: Execute agents with LLM integration (Anthropic Claude)
- **Conversation Management**: Track conversations and message history
- **Multi-Tenant Ready**: Database schema designed for multi-tenancy from day one
- **Authentication**: JWT-based authentication with role-based access
- **RESTful API**: Comprehensive API with OpenAPI/Swagger documentation
- **Docker Compose**: Easy local development setup

### ✅ Phase 2: RAG + MCP + Workflows (Complete)
- **RAG System**: Document processing, vector embeddings (pgvector), semantic search
- **MCP Servers**: 3 pre-built servers (Filesystem, Database, Calculator) with 16 tools
- **Workflow Engine**: Multi-agent orchestration with sequential/parallel execution
- **Conditional Branching**: JSONPath-based workflow routing
- **Template Variables**: Dynamic variable resolution across workflow steps

### ✅ Phase 3: Production Readiness (Complete)
- **Observability**: Prometheus, Grafana, Jaeger, AlertManager stack
- **Performance**: Redis caching, rate limiting, connection pooling, batch operations
- **Security**: Sentry error tracking, security headers, secrets management
- **Load Testing**: Locust-based performance testing
- **Backups**: Automated PostgreSQL backups with S3 support
- **Deployment**: Production Docker Compose and deployment guides

## Tech Stack

### Core
- **Backend**: Python 3.11+ with FastAPI
- **Database**: PostgreSQL 16 with pgvector extension for vector embeddings
- **Cache/Queue**: Redis 7 for caching and task queues
- **ORM**: SQLAlchemy 2.0 with async support
- **Migrations**: Alembic for database versioning
- **LLM**: Anthropic Claude (with OpenAI fallback support)

### Observability & Monitoring
- **Metrics**: Prometheus for metrics collection
- **Visualization**: Grafana for dashboards
- **Tracing**: Jaeger for distributed tracing
- **Alerting**: AlertManager for alert routing
- **Error Tracking**: Sentry for error monitoring
- **Logging**: Structured JSON logging with correlation IDs

### Performance & Security
- **Caching**: Redis with TTL-based invalidation
- **Rate Limiting**: Token bucket algorithm with Redis backend
- **Connection Pooling**: Optimized PostgreSQL and Redis pools
- **Security Headers**: CORS, CSP, HSTS, X-Frame-Options
- **Secrets**: Environment-based secrets management

### DevOps & Testing
- **Containerization**: Docker & Docker Compose
- **Load Testing**: Locust for performance testing
- **Backups**: Automated PostgreSQL backups with S3 support
- **CI/CD**: GitHub Actions ready

## Quick Start

### Prerequisites

- Docker and Docker Compose
- Python 3.11+ (for local development)
- Git

### 1. Clone Repository

```bash
git clone <repository-url>
cd agentic-platform
```

### 2. Environment Setup

```bash
# Copy environment template
cp .env.example .env

# Edit .env and add your API keys
# At minimum, set:
# - SECRET_KEY (generate with: openssl rand -hex 32)
# - JWT_SECRET (generate with: openssl rand -hex 32)
# - ANTHROPIC_API_KEY (get from https://console.anthropic.com/)
```

### 3. Start Services with Docker Compose

```bash
# Build and start all services
docker-compose up -d

# View logs
docker-compose logs -f api
```

### 4. Run Database Migrations

```bash
# Create initial migration
docker-compose exec api alembic revision --autogenerate -m "Initial schema"

# Apply migrations
docker-compose exec api alembic upgrade head
```

### 5. Create Admin User (Optional)

```bash
# Run seed script to create default tenant and admin user
docker-compose exec api python scripts/seed_dev_data.py
```

### 6. Access the API

- **API**: http://localhost:8000
- **API Docs (Swagger)**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **Health Check**: http://localhost:8000/health

## API Endpoints

### Authentication
- `POST /v1/auth/login` - Login and receive JWT tokens
- `POST /v1/auth/logout` - Logout

### Agents
- `POST /v1/agents` - Create a new agent
- `GET /v1/agents` - List all agents (with pagination, search, filtering)
- `GET /v1/agents/{agent_id}` - Get agent details
- `PATCH /v1/agents/{agent_id}` - Update agent configuration
- `DELETE /v1/agents/{agent_id}` - Delete agent (soft delete)
- `POST /v1/agents/{agent_id}/execute` - Execute agent with a task

### Conversations
- `GET /v1/conversations` - List conversations (with pagination, filtering)
- `GET /v1/conversations/{conversation_id}` - Get conversation with messages
- `DELETE /v1/conversations/{conversation_id}` - Delete conversation

### RAG (Retrieval-Augmented Generation)
- `POST /v1/rag/collections` - Create document collection
- `GET /v1/rag/collections` - List collections
- `POST /v1/rag/documents` - Upload document
- `POST /v1/rag/documents/batch` - Batch upload documents
- `GET /v1/rag/documents/{document_id}` - Get document details
- `POST /v1/rag/search` - Semantic search across documents
- `POST /v1/rag/query` - RAG query with context retrieval

### MCP (Model Context Protocol)
- `POST /v1/mcp/servers` - Register MCP server
- `GET /v1/mcp/servers` - List MCP servers
- `GET /v1/mcp/servers/{server_id}` - Get server details
- `GET /v1/mcp/servers/{server_id}/discover` - Discover server capabilities
- `POST /v1/mcp/execute` - Execute MCP tool
- `GET /v1/mcp/executions` - List tool execution history
- `GET /v1/mcp/servers/{server_id}/health` - Check server health

### Workflows
- `POST /v1/workflows/workflows` - Create workflow
- `GET /v1/workflows/workflows` - List workflows
- `GET /v1/workflows/workflows/{workflow_id}` - Get workflow details
- `PATCH /v1/workflows/workflows/{workflow_id}` - Update workflow
- `POST /v1/workflows/workflows/execute` - Execute workflow
- `GET /v1/workflows/workflows/executions/{execution_id}` - Get execution status
- `POST /v1/workflows/workflows/executions/{execution_id}/cancel` - Cancel execution
- `GET /v1/workflows/tasks` - List agent tasks
- `GET /v1/workflows/messages` - List inter-agent messages

## Development

### Local Development (without Docker)

```bash
# Install dependencies with Poetry
poetry install

# Activate virtual environment
poetry shell

# Set up database (make sure PostgreSQL with pgvector is running)
export DATABASE_URL="postgresql://postgres:postgres@localhost:5432/agentic_platform"

# Run migrations
alembic upgrade head

# Start API server with hot reload
uvicorn src.main:app --reload --host 0.0.0.0 --port 8000
```

### Running Tests

```bash
# Run all tests
docker-compose exec api pytest

# Run with coverage
docker-compose exec api pytest --cov=src --cov-report=html

# Run specific test file
docker-compose exec api pytest tests/test_agents.py
```

### Code Quality

```bash
# Format code with Black
poetry run black src tests

# Lint with Ruff
poetry run ruff check src tests

# Type checking with mypy
poetry run mypy src
```

## Database Schema

The platform uses PostgreSQL with **25 tables** across 4 categories:

### Core Tables (8)
- **tenants**: Organizations/tenants for multi-tenancy
- **users**: User accounts belonging to tenants
- **agents**: AI agent definitions and configurations
- **conversations**: Conversation sessions between users and agents
- **messages**: Individual messages within conversations
- **tool_executions**: Log of tool/function executions
- **api_keys**: API keys for programmatic access
- **audit_logs**: Comprehensive audit trail

### RAG Tables (5)
- **collections**: Document collections for organization
- **documents**: Uploaded documents with metadata
- **chunks**: Document chunks with vector embeddings (pgvector)
- **rag_queries**: Query history and performance tracking
- **rag_sources**: Source attribution for retrieved context

### MCP Tables (4)
- **mcp_servers**: Registered MCP server definitions
- **mcp_server_configs**: Server-specific configurations
- **mcp_tool_executions**: Tool execution history and audit
- **mcp_server_registry**: Server discovery and health status

### Workflow Tables (5)
- **workflows**: Workflow definitions with steps and configuration
- **workflow_executions**: Workflow execution instances
- **workflow_step_executions**: Individual step execution tracking
- **agent_tasks**: Task assignments for agent coordination
- **agent_messages**: Inter-agent communication logs

All tables include:
- UUID primary keys
- `tenant_id` for multi-tenant isolation
- `created_at` and `updated_at` timestamps
- Soft delete support (`deleted_at`)
- Optimized indexes for common query patterns

## Creating Your First Agent

### 1. Login (or create test user)

```bash
curl -X POST http://localhost:8000/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@example.com","password":"admin123"}'
```

### 2. Create Agent

```bash
curl -X POST http://localhost:8000/v1/agents \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <your-token>" \
  -d '{
    "name": "Customer Support Agent",
    "slug": "customer-support",
    "description": "Helpful customer support assistant",
    "model_provider": "anthropic",
    "model_name": "claude-sonnet-4-5",
    "system_prompt": "You are a helpful customer support agent. Be friendly and professional.",
    "temperature": 0.7,
    "max_tokens": 4096
  }'
```

### 3. Execute Agent

```bash
curl -X POST http://localhost:8000/v1/agents/{agent_id}/execute \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <your-token>" \
  -d '{
    "input": "Hello! I need help with my account.",
    "stream": false
  }'
```

## Project Structure

```
agentic-platform/
├── src/
│   ├── api/v1/
│   │   ├── agents.py              # Agent endpoints
│   │   ├── auth.py                # Authentication endpoints
│   │   ├── conversations.py       # Conversation endpoints
│   │   ├── rag.py                 # RAG endpoints (NEW)
│   │   ├── mcp.py                 # MCP endpoints (NEW)
│   │   └── workflows.py           # Workflow endpoints (NEW)
│   ├── core/
│   │   ├── config.py              # Configuration
│   │   ├── security.py            # Security utilities
│   │   ├── logging.py             # Structured logging (NEW)
│   │   ├── metrics.py             # Prometheus metrics (NEW)
│   │   ├── tracing.py             # OpenTelemetry tracing (NEW)
│   │   ├── cache.py               # Redis caching (NEW)
│   │   ├── rate_limit.py          # Rate limiting (NEW)
│   │   ├── batch.py               # Batch operations (NEW)
│   │   ├── middleware.py          # Custom middleware (NEW)
│   │   ├── security_headers.py    # Security headers (NEW)
│   │   ├── secrets.py             # Secrets management (NEW)
│   │   └── sentry_config.py       # Sentry integration (NEW)
│   ├── db/
│   │   ├── base.py                # SQLAlchemy base
│   │   ├── models.py              # All database models (25 tables)
│   │   └── session.py             # Database session with pooling
│   ├── schemas/
│   │   ├── agent.py               # Agent schemas
│   │   ├── auth.py                # Auth schemas
│   │   ├── conversation.py        # Conversation schemas
│   │   ├── rag.py                 # RAG schemas (NEW)
│   │   ├── mcp.py                 # MCP schemas (NEW)
│   │   └── workflow.py            # Workflow schemas (NEW)
│   ├── services/
│   │   ├── agent_executor.py      # Agent execution service
│   │   ├── document_processor.py  # Document processing (NEW)
│   │   ├── embedding_service.py   # Vector embeddings (NEW)
│   │   ├── rag_service.py         # RAG retrieval (NEW)
│   │   ├── mcp_client.py          # MCP client (NEW)
│   │   └── workflow_engine.py     # Workflow orchestration (NEW)
│   ├── mcp_servers/               # MCP Server implementations (NEW)
│   │   ├── base_server.py         # Base server framework
│   │   ├── filesystem_server.py   # Filesystem tools (7 tools)
│   │   ├── database_server.py     # Database tools (4 tools)
│   │   └── calculator_server.py   # Calculator tools (5 tools)
│   └── main.py                    # FastAPI application
├── alembic/versions/              # Database migrations
├── tests/                         # Comprehensive test suite
├── scripts/
│   ├── seed_dev_data.py           # Development seed data
│   ├── seed_mcp_servers.py        # Seed MCP servers (NEW)
│   ├── seed_workflow_templates.py # Seed workflow templates (NEW)
│   └── backup/                    # Backup automation (NEW)
│       ├── backup.sh              # Backup script
│       ├── Dockerfile             # Backup container
│       └── README.md              # Backup guide
├── observability/                 # Observability stack (NEW)
│   ├── prometheus/                # Prometheus configuration
│   ├── grafana/                   # Grafana dashboards
│   └── alertmanager/              # Alert routing
├── load_tests/                    # Load testing (NEW)
│   ├── locustfile.py              # Locust test scenarios
│   └── README.md                  # Load testing guide
├── docs/
│   ├── README.md                  # Documentation hub
│   ├── QUICK_REFERENCE.md         # Daily patterns
│   ├── CODEBASE_DEEP_DIVE.md      # Complete understanding
│   ├── ARCHITECTURE_DECISIONS.md  # ADRs
│   ├── architecture.md            # System architecture
│   ├── database-schema.md         # Database design
│   ├── api-specification.md       # API reference
│   ├── rag-implementation.md      # RAG guide (NEW)
│   ├── mcp-implementation.md      # MCP guide (NEW)
│   ├── MCP_USAGE_GUIDE.md         # MCP usage (NEW)
│   ├── WORKFLOW_ARCHITECTURE.md   # Workflow design (NEW)
│   ├── WORKFLOW_USAGE_GUIDE.md    # Workflow usage (NEW)
│   ├── OBSERVABILITY.md           # Observability guide (NEW)
│   ├── PERFORMANCE.md             # Performance guide (NEW)
│   ├── TESTING_GUIDE.md           # Testing guide (NEW)
│   ├── deployment.md              # Deployment guide
│   ├── DOCKER_DEPLOYMENT.md       # Docker deployment (NEW)
│   ├── RUNBOOK.md                 # Operations runbook (NEW)
│   └── SENTRY.md                  # Sentry setup (NEW)
├── .github/workflows/             # CI/CD workflows (NEW)
├── docker-compose.yml             # Development environment
├── docker-compose.prod.yml        # Production environment (NEW)
├── Dockerfile                     # Application container
├── pyproject.toml                 # Python dependencies
├── .env.example                   # Environment template
└── README.md                      # This file
```

## Environment Variables

See `.env.example` for all available configuration options.

### Required Variables

- `SECRET_KEY`: Application secret key (32+ characters)
- `JWT_SECRET`: JWT signing secret (32+ characters)
- `DATABASE_URL`: PostgreSQL connection string
- `REDIS_URL`: Redis connection string
- `ANTHROPIC_API_KEY`: Anthropic API key for Claude

### Optional - LLM Providers

- `OPENAI_API_KEY`: OpenAI API key (for OpenAI models)

### Optional - Observability

- `SENTRY_DSN`: Sentry DSN for error tracking
- `SENTRY_ENVIRONMENT`: Environment name (development, staging, production)
- `OTEL_EXPORTER_OTLP_ENDPOINT`: OpenTelemetry collector endpoint
- `PROMETHEUS_MULTIPROC_DIR`: Prometheus multiprocess directory

### Optional - Performance

- `CACHE_TTL`: Default cache TTL in seconds (default: 300)
- `RATE_LIMIT_REQUESTS`: Requests per minute per user (default: 60)
- `DB_POOL_SIZE`: Database connection pool size (default: 20)
- `DB_MAX_OVERFLOW`: Max overflow connections (default: 10)

### Optional - Features

- `LOG_LEVEL`: Logging level (DEBUG, INFO, WARNING, ERROR)
- `ALLOWED_ORIGINS`: CORS allowed origins (comma-separated)
- `DEFAULT_AGENT_TIMEOUT`: Default agent execution timeout (default: 300)
- `MAX_AGENT_ITERATIONS`: Maximum agent iterations (default: 10)
- `ENABLE_METRICS`: Enable Prometheus metrics (default: true)
- `ENABLE_TRACING`: Enable OpenTelemetry tracing (default: false)

## Troubleshooting

### Database Connection Issues

```bash
# Check if PostgreSQL is running
docker-compose ps postgres

# Check logs
docker-compose logs postgres

# Restart PostgreSQL
docker-compose restart postgres
```

### Migration Issues

```bash
# Check migration status
docker-compose exec api alembic current

# View migration history
docker-compose exec api alembic history

# Downgrade one revision
docker-compose exec api alembic downgrade -1
```

### API Not Responding

```bash
# Check API logs
docker-compose logs -f api

# Restart API
docker-compose restart api

# Rebuild API image
docker-compose up -d --build api
```

## Implementation Roadmap

### ✅ Phase 1: Foundation (Complete)
- Single agent execution environment
- JWT authentication with multi-tenant database schema
- PostgreSQL + Redis infrastructure
- Basic REST API with OpenAPI documentation

### ✅ Phase 2: RAG + MCP + Workflows (Complete)
- RAG system with pgvector for semantic search
- MCP protocol with 3 pre-built servers (16 tools)
- Multi-agent workflow orchestration engine
- Sequential/parallel execution with conditional branching

### ✅ Phase 3: Production Readiness (Complete)
- Full observability stack (Prometheus, Grafana, Jaeger)
- Performance optimizations (caching, rate limiting, pooling)
- Security hardening (Sentry, security headers, secrets)
- Operational tooling (backups, load testing, runbooks)

### 📅 Phase 4: Multi-Region & Scale (Planned)
- Kubernetes deployment manifests
- Multi-region data replication
- Global load balancing
- Advanced tenant isolation
- Resource quotas and billing
- Horizontal autoscaling

## Documentation

📚 **[Complete Documentation Guide](docs/README.md)** - Start here for all documentation

### Quick Links

**Essential Reading:**
- 🗺️ [Documentation Navigation](docs/README.md) - Which doc to read when
- ⚡ [Quick Reference](docs/QUICK_REFERENCE.md) - Daily patterns and commands
- 📖 [Codebase Deep Dive](docs/CODEBASE_DEEP_DIVE.md) - Complete understanding
- 📋 [Architecture Decisions](docs/ARCHITECTURE_DECISIONS.md) - Why we chose X over Y

**Reference Documentation:**
- [Architecture](docs/architecture.md) - System design and scaling
- [Database Schema](docs/database-schema.md) - Tables and relationships
- [API Specification](docs/api-specification.md) - Endpoint reference
- [RAG Implementation](docs/rag-implementation.md) - Document processing & search
- [MCP Implementation](docs/mcp-implementation.md) - Model Context Protocol
- [Deployment Guide](docs/deployment.md) - Production deployment

**New Developer?** Start with [docs/README.md](docs/README.md) → Follow the onboarding path (4 hours to productivity)

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run tests and linting
5. Submit a pull request

## License

[Your License Here]

## Support

For issues and questions:
- GitHub Issues: [repository-url]/issues
- Documentation: [docs-url]
- Email: support@example.com
