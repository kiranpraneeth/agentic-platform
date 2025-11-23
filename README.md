# Agentic Platform - Phase 1 MVP

Multi-tenant AI agentic platform with RAG and MCP support. Built with FastAPI, PostgreSQL, Redis, and Anthropic Claude.

## Features (Phase 1 MVP)

- ✅ **Agent Management**: Create, configure, and manage AI agents
- ✅ **Agent Execution**: Execute agents with LLM integration (Anthropic Claude)
- ✅ **Conversation Management**: Track conversations and message history
- ✅ **Multi-Tenant Ready**: Database schema designed for multi-tenancy from day one
- ✅ **Authentication**: JWT-based authentication with role-based access
- ✅ **RESTful API**: Comprehensive API with OpenAPI/Swagger documentation
- ✅ **Docker Compose**: Easy local development setup

## Tech Stack

- **Backend**: Python 3.11+ with FastAPI
- **Database**: PostgreSQL 16 with pgvector extension
- **Cache/Queue**: Redis 7
- **ORM**: SQLAlchemy 2.0 with async support
- **Migrations**: Alembic
- **LLM**: Anthropic Claude (with OpenAI fallback support)
- **Containerization**: Docker & Docker Compose

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

The platform uses PostgreSQL with the following core tables:

- **tenants**: Organizations/tenants for multi-tenancy
- **users**: User accounts belonging to tenants
- **agents**: AI agent definitions and configurations
- **conversations**: Conversation sessions between users and agents
- **messages**: Individual messages within conversations
- **tool_executions**: Log of tool/function executions
- **api_keys**: API keys for programmatic access
- **audit_logs**: Comprehensive audit trail

All tables include:
- UUID primary keys
- `tenant_id` for multi-tenant isolation
- `created_at` and `updated_at` timestamps
- Soft delete support (`deleted_at`)

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
│   ├── api/
│   │   ├── v1/
│   │   │   ├── agents.py          # Agent endpoints
│   │   │   ├── auth.py            # Authentication endpoints
│   │   │   └── conversations.py   # Conversation endpoints
│   │   └── dependencies.py        # API dependencies
│   ├── core/
│   │   ├── config.py              # Configuration
│   │   └── security.py            # Security utilities
│   ├── db/
│   │   ├── base.py                # SQLAlchemy base
│   │   ├── models.py              # Database models
│   │   └── session.py             # Database session
│   ├── schemas/
│   │   ├── agent.py               # Agent schemas
│   │   ├── auth.py                # Auth schemas
│   │   └── conversation.py        # Conversation schemas
│   ├── services/
│   │   └── agent_executor.py     # Agent execution service
│   └── main.py                    # FastAPI application
├── alembic/
│   ├── versions/                  # Migration files
│   └── env.py                     # Alembic environment
├── tests/                         # Test files
├── scripts/
│   ├── init-db.sql               # Database initialization
│   └── seed_dev_data.py          # Development seed data
├── docs/                         # Documentation
├── docker-compose.yml            # Docker Compose configuration
├── Dockerfile                    # Docker image definition
├── pyproject.toml                # Python dependencies
├── alembic.ini                   # Alembic configuration
└── README.md                     # This file
```

## Environment Variables

See `.env.example` for all available configuration options.

### Required Variables

- `SECRET_KEY`: Application secret key (32+ characters)
- `JWT_SECRET`: JWT signing secret (32+ characters)
- `DATABASE_URL`: PostgreSQL connection string
- `REDIS_URL`: Redis connection string
- `ANTHROPIC_API_KEY`: Anthropic API key for Claude

### Optional Variables

- `OPENAI_API_KEY`: OpenAI API key (for future support)
- `LOG_LEVEL`: Logging level (DEBUG, INFO, WARNING, ERROR)
- `ALLOWED_ORIGINS`: CORS allowed origins
- `DEFAULT_AGENT_TIMEOUT`: Default agent execution timeout
- `MAX_AGENT_ITERATIONS`: Maximum agent iterations

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

## Next Steps (Upcoming Phases)

### Phase 2: Multi-Agent + RAG + MCP (Weeks 5-8)
- Multi-agent orchestration
- RAG (Retrieval-Augmented Generation) implementation
- MCP (Model Context Protocol) servers
- Workflow engine

### Phase 3: Multi-Tenancy (Weeks 9-12)
- Enhanced tenant isolation
- Resource quotas and billing
- Tenant management UI
- Usage analytics

### Phase 4: Multi-Region (Weeks 13-20)
- Multi-region deployment
- Global load balancing
- Data replication
- Kubernetes manifests

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
