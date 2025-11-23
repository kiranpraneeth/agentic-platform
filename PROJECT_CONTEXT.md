# Agentic Platform - Project Context

## Project Overview
Production-ready multi-tenant AI agentic platform with RAG, MCP, and workflow orchestration. **Phases 1-3 Complete**. Built with FastAPI, PostgreSQL (pgvector), Redis, comprehensive observability, and production-grade tooling.

## Development Phases

### ✅ Phase 1: Foundation (COMPLETE)
**Implemented Components:**
- ✅ Agent Runtime: Async execution environment with LLM integration (Anthropic Claude)
- ✅ Task Queue: Redis-based job queue
- ✅ State Management: PostgreSQL with multi-tenant schema (25 tables)
- ✅ API Gateway: FastAPI REST API with OpenAPI documentation
- ✅ Authentication: JWT-based auth with role-based access control
- ✅ Multi-tenant Database: tenant_id isolation across all tables

**Achievements:**
- Modular architecture with plugin system
- Comprehensive database schema with UUID primary keys
- Soft delete support and audit logging
- Docker Compose development environment

### ✅ Phase 2: Multi-Agent Orchestration + RAG + MCP (COMPLETE)

**RAG Implementation (COMPLETE):**
- ✅ Vector Database: pgvector extension for embeddings
- ✅ Document Processing Pipeline: Chunking, embedding, and indexing
- ✅ Retrieval Service: Semantic search with context retrieval
- ✅ Knowledge Base Management: Collections, documents, chunks (5 tables)
- ✅ Embedding Service: Anthropic embeddings integration
- ✅ RAG Query API: Complete REST API for document operations

**MCP (Model Context Protocol) - COMPLETE:**
- ✅ MCP Server Framework: Abstract base class for easy extension
- ✅ Pre-built MCP Servers: 3 servers with 16 total tools
  - Filesystem Server (7 tools): read, write, list, create, delete, search, info
  - Database Server (4 tools): query, list tables, describe, get schema
  - Calculator Server (5 tools): add, subtract, multiply, divide, power
- ✅ MCP Client Service: JSON-RPC stdio communication (409 lines)
- ✅ Tool Discovery: Dynamic capability discovery
- ✅ Server Registry: Health monitoring and execution tracking (4 tables)
- ✅ Complete REST API: 14 endpoints for CRUD, execution, discovery

**Multi-Agent Workflow Orchestration (COMPLETE):**
- ✅ Workflow Engine: Complete orchestration service (817 lines)
- ✅ Sequential Execution: Steps run in defined order
- ✅ Parallel Execution: Concurrent step execution with wait strategies
- ✅ Conditional Branching: JSONPath-based routing with operators
- ✅ Template Variables: Dynamic variable resolution across steps
- ✅ Step Types: Agent, MCP tool, HTTP, transformation, conditional
- ✅ Error Handling: Automatic retries with exponential backoff
- ✅ State Management: Complete workflow and step state tracking (5 tables)
- ✅ Inter-agent Communication: Agent tasks and messages
- ✅ Complete REST API: 18 endpoints for workflow management
- ✅ Example Templates: 5 pre-built workflow templates seeded

**Patterns Implemented:**
- ✅ Supervisor pattern (coordinator agent)
- ✅ Sequential pipelines
- ✅ Parallel execution with synthesis
- ✅ RAG-enhanced agents with knowledge retrieval
- ✅ Tool-augmented agents via MCP servers

### ✅ Phase 3: Production Readiness (COMPLETE)

**Observability Stack (COMPLETE):**
- ✅ Metrics: Prometheus for metrics collection and storage
- ✅ Visualization: Grafana dashboards for monitoring
- ✅ Tracing: Jaeger for distributed request tracing
- ✅ Alerting: AlertManager for alert routing and notification
- ✅ Error Tracking: Sentry integration for error monitoring
- ✅ Logging: Structured JSON logging with correlation IDs

**Performance Optimizations (COMPLETE):**
- ✅ Caching: Redis caching layer with TTL-based invalidation
- ✅ Rate Limiting: Token bucket algorithm with Redis backend
- ✅ Connection Pooling: Optimized PostgreSQL and Redis pools
- ✅ Batch Operations: Bulk insert/update operations
- ✅ Database Indexes: Comprehensive indexing strategy (~65 indexes)
- ✅ Query Optimization: Efficient SQLAlchemy queries

**Security & Operations (COMPLETE):**
- ✅ Security Headers: CORS, CSP, HSTS, X-Frame-Options
- ✅ Secrets Management: Environment-based configuration
- ✅ Input Validation: Pydantic schemas for all endpoints
- ✅ SQL Injection Prevention: Parameterized queries
- ✅ Path Traversal Prevention: Filesystem sandboxing
- ✅ Automated Backups: PostgreSQL backup with S3 support
- ✅ Load Testing: Locust-based performance testing
- ✅ Deployment Guides: Docker Compose production deployment
- ✅ Runbook: Operations and troubleshooting guide

**Production Infrastructure:**
- ✅ Docker Compose (development and production)
- ✅ Health check endpoints
- ✅ Graceful shutdown handling
- ✅ Comprehensive documentation (20+ docs)
- ✅ CI/CD ready (GitHub Actions)

### 📅 Phase 4: Multi-Region & Scale (PLANNED)
- Kubernetes Deployment: Helm charts and manifests
- Multi-Region: Global load balancing
- Data Replication: Multi-region PostgreSQL replication
- Advanced Multi-Tenancy: Enhanced tenant isolation and resource quotas
- Billing Integration: Usage tracking and billing hooks
- Horizontal Autoscaling: Pod autoscaling based on metrics

## Tech Stack (Current Implementation)

### Backend
- **Language**: Python 3.11+ with FastAPI
- **Framework**: FastAPI with async/await throughout
- **ORM**: SQLAlchemy 2.0 with async support
- **Migrations**: Alembic for database versioning

### Infrastructure
- **Database**: PostgreSQL 16 with pgvector extension
- **Cache/Queue**: Redis 7 for caching and task queues
- **Containerization**: Docker & Docker Compose
- **Future**: Kubernetes + Terraform (Phase 4)

### Observability & Monitoring
- **Metrics**: Prometheus for collection and storage
- **Visualization**: Grafana for dashboards
- **Tracing**: Jaeger for distributed tracing
- **Alerting**: AlertManager for alert routing
- **Error Tracking**: Sentry for error monitoring
- **Logging**: Structured JSON logging with correlation IDs

### LLM & AI
- **Primary LLM**: Anthropic Claude (claude-sonnet-4-5)
- **Embeddings**: Anthropic embeddings
- **Vector Search**: pgvector extension
- **Future Support**: OpenAI and other providers

### Performance & Security
- **Caching**: Redis with TTL-based invalidation
- **Rate Limiting**: Token bucket algorithm
- **Connection Pooling**: Optimized pools for PostgreSQL and Redis
- **Security**: CORS, CSP, HSTS, security headers, secrets management

### DevOps & Testing
- **CI/CD**: GitHub Actions ready
- **Load Testing**: Locust
- **Backups**: Automated PostgreSQL backups with S3
- **Deployment**: Docker Compose (development and production)

## Architecture Principles

1. **API-First**: Every component exposes well-defined APIs
2. **Event-Driven**: Use events for loosely coupled communication
3. **Stateless Services**: Push state to databases/cache
4. **Configuration as Code**: All infrastructure in Git
5. **Observability Built-In**: Logging, metrics, tracing from day one
6. **Multi-tenant Ready**: Design for isolation from the start

## Data Models

### Agent Definition
```json
{
  "agent_id": "analyst-v1",
  "capabilities": ["data_analysis", "visualization"],
  "tools": ["python_repl", "web_search"],
  "model": "claude-4-sonnet",
  "system_prompt": "...",
  "resource_limits": {
    "max_tokens": 100000,
    "max_execution_time": 300
  }
}
```

### Tenant Context
Every request carries tenant context through headers/JWT for proper isolation and routing.

## Initial MVP Requirements (2-Week Sprint)

1. FastAPI backend with single agent endpoint
2. LangChain/LlamaIndex integration
3. PostgreSQL database with basic schema
4. Docker Compose for local development
5. Simple REST API for agent interaction
6. Basic authentication

## Database Schema (Implemented)

**Total: 25 tables** across 4 categories, all with multi-tenant isolation:

### Core Tables (8)
- tenants, users, agents, conversations, messages, tool_executions, api_keys, audit_logs

### RAG Tables (5)
- collections, documents, chunks (with pgvector embeddings), rag_queries, rag_sources

### MCP Tables (4)
- mcp_servers, mcp_server_configs, mcp_tool_executions, mcp_server_registry

### Workflow Tables (5)
- workflows, workflow_executions, workflow_step_executions, agent_tasks, agent_messages

**Features:**
- Multi-tenancy with tenant_id in all tables
- UUID primary keys for distributed systems
- Soft delete support (deleted_at)
- Comprehensive audit logging
- ~65 optimized indexes for performance
- Vector embeddings with pgvector extension

## API Endpoints (Implemented)

**Total: 50+ endpoints** across 6 categories:

### Authentication (2)
- POST /v1/auth/login, POST /v1/auth/logout

### Agents (6)
- POST /v1/agents, GET /v1/agents, GET /v1/agents/{id}, PATCH /v1/agents/{id}, DELETE /v1/agents/{id}, POST /v1/agents/{id}/execute

### Conversations (3)
- GET /v1/conversations, GET /v1/conversations/{id}, DELETE /v1/conversations/{id}

### RAG (7)
- POST /v1/rag/collections, GET /v1/rag/collections, POST /v1/rag/documents, POST /v1/rag/documents/batch, GET /v1/rag/documents/{id}, POST /v1/rag/search, POST /v1/rag/query

### MCP (7)
- POST /v1/mcp/servers, GET /v1/mcp/servers, GET /v1/mcp/servers/{id}, GET /v1/mcp/servers/{id}/discover, POST /v1/mcp/execute, GET /v1/mcp/executions, GET /v1/mcp/servers/{id}/health

### Workflows (9)
- POST /v1/workflows/workflows, GET /v1/workflows/workflows, GET /v1/workflows/workflows/{id}, PATCH /v1/workflows/workflows/{id}, POST /v1/workflows/workflows/execute, GET /v1/workflows/workflows/executions/{id}, POST /v1/workflows/workflows/executions/{id}/cancel, GET /v1/workflows/tasks, GET /v1/workflows/messages

**Plus:**
- OpenAPI/Swagger documentation at /docs
- Health check endpoint at /health
- Metrics endpoint at /metrics (Prometheus)

## Development Guidelines

- Use TypeScript/Python type hints throughout
- Comprehensive error handling
- Input validation on all endpoints
- Unit tests for core logic
- Integration tests for API endpoints
- Documentation with OpenAPI/Swagger

## Security Requirements

- API key authentication initially
- JWT tokens for future multi-tenancy
- Rate limiting on all endpoints
- Input sanitization
- CORS configuration
- Secrets management (environment variables, then vault)

## Deployment

**Local Development:**
- Docker Compose with all services
- Hot reload for development
- Seed data for testing

**Production (Future):**
- Kubernetes manifests
- Helm charts for deployment
- Horizontal pod autoscaling
- Health checks and readiness probes

## Current Status

### ✅ Completed (Phases 1-3)
1. ✅ Complete project structure with modular architecture
2. ✅ FastAPI server with 50+ endpoints
3. ✅ Database schema with 25 tables and migrations
4. ✅ Anthropic Claude integration (primary LLM)
5. ✅ Agent execution with RAG and MCP tools
6. ✅ Docker Compose setup (development + production)
7. ✅ Comprehensive test suite and documentation
8. ✅ RAG system with pgvector
9. ✅ MCP protocol with 3 pre-built servers (16 tools)
10. ✅ Workflow orchestration engine
11. ✅ Full observability stack (Prometheus, Grafana, Jaeger, Sentry)
12. ✅ Performance optimizations (caching, rate limiting, pooling)
13. ✅ Production tooling (backups, load testing, runbooks)

### 📅 Next Steps (Phase 4)
- Kubernetes deployment manifests and Helm charts
- Multi-region data replication
- Global load balancing
- Advanced tenant isolation and resource quotas
- Billing integration with usage tracking
- Horizontal pod autoscaling

## Resolved Design Decisions

- ✅ **Programming Language**: Python with FastAPI (chosen for async support and ecosystem)
- ✅ **LLM Provider**: Anthropic Claude (primary), OpenAI support ready
- ✅ **Workflow Engine**: Custom workflow engine (built in-house for flexibility)
- ✅ **Vector Database**: pgvector (chosen over Pinecone for cost and simplicity)
- ✅ **Observability**: Prometheus + Grafana + Jaeger + Sentry stack
- ✅ **Deployment**: Docker Compose (current), Kubernetes (Phase 4)