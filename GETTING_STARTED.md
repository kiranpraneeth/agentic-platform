# Getting Started with Agentic Platform Development

## Quick Start for Claude Code

This document provides instructions for using Claude Code to build the agentic platform based on all the context documents in this repository.

## Repository Structure

```
agentic-platform/
├── PROJECT_CONTEXT.md           # Main project overview and phases
├── docs/
│   ├── architecture.md          # System architecture and design
│   ├── database-schema.md       # Database design specification
│   ├── api-specification.md     # Complete API documentation
│   ├── rag-implementation.md    # RAG system specification
│   ├── mcp-implementation.md    # MCP servers specification
│   └── deployment.md            # Deployment and infrastructure guide
├── src/                         # Source code (to be generated)
├── tests/                       # Tests (to be generated)
├── k8s/                         # Kubernetes manifests (to be generated)
├── terraform/                   # Infrastructure as code (to be generated)
└── docker-compose.yml           # Local development setup (to be generated)
```

## How to Use These Context Files with Claude Code

### Step 1: Initial Setup

Start Claude Code with comprehensive context:

```bash
claude-code "Read all files in docs/ directory and PROJECT_CONTEXT.md. 
I want to build Phase 1 MVP of the agentic platform.

Start with:
1. Create the project structure for a FastAPI backend
2. Set up docker-compose.yml with PostgreSQL, Redis, and pgvector
3. Create the database schema based on docs/database-schema.md
4. Implement the core API endpoints from docs/api-specification.md
5. Add basic authentication and tenant management

Use Python 3.11+, FastAPI, SQLAlchemy, Alembic for migrations, and follow the architecture in docs/architecture.md"
```

### Step 2: Build Incrementally

After the initial setup, continue building features:

```bash
# Add RAG functionality
claude-code "Based on docs/rag-implementation.md, implement Phase 1 of RAG:
- Document upload and processing pipeline
- Integration with pgvector for embeddings
- Retrieval API endpoint
- Agent tool for RAG queries"

# Add MCP servers
claude-code "Based on docs/mcp-implementation.md, create:
- Filesystem MCP server with safety checks
- Database MCP server for PostgreSQL
- MCP client integration in agents"

# Add multi-agent orchestration
claude-code "Implement Phase 2 from PROJECT_CONTEXT.md:
- Agent registry service
- Basic workflow engine
- Inter-agent communication via Redis"
```

### Step 3: Iterate and Refine

Ask Claude Code to improve specific areas:

```bash
# Improve error handling
claude-code "Review all API endpoints and add comprehensive error handling following best practices"

# Add tests
claude-code "Create pytest tests for all agent execution endpoints with mocks for LLM calls"

# Optimize performance
claude-code "Review database queries and add appropriate indexes based on common query patterns"
```

## Current Phase: Phase 1 MVP

**Goal:** Single agent execution with basic RAG and MCP support

**Key Features:**
- ✅ API Gateway with authentication
- ✅ Agent creation and management
- ✅ Agent execution endpoint with LLM integration
- ✅ Conversation and message persistence
- ✅ Basic RAG with document upload and retrieval
- ✅ 2-3 essential MCP servers (filesystem, database)
- ✅ Docker Compose for local development
- ✅ Database migrations
- ✅ Basic tests

**Tech Stack:**
- Backend: Python 3.11+ with FastAPI
- Database: PostgreSQL with pgvector
- Cache/Queue: Redis
- LLM: Anthropic Claude (with OpenAI as fallback)
- ORM: SQLAlchemy
- Migrations: Alembic
- Testing: pytest
- Containerization: Docker & Docker Compose

## Key Context Documents

### 1. PROJECT_CONTEXT.md
**Purpose:** High-level overview, phases, tech stack decisions

**Key Sections:**
- Development phases (1-4)
- Architecture principles
- Tech stack recommendations
- Initial MVP requirements

**When to reference:** Starting new phase, making technology decisions, understanding overall goals

### 2. docs/architecture.md
**Purpose:** System design and component interactions

**Key Sections:**
- Architecture layers (API, Application, Data, Integration)
- Service communication patterns
- Phase-by-phase architecture evolution
- Scalability patterns

**When to reference:** Designing new services, understanding component relationships, planning multi-agent features

### 3. docs/database-schema.md
**Purpose:** Complete database design specification

**Key Sections:**
- Design principles
- All table definitions with fields and relationships
- Indexes and constraints
- Multi-tenant considerations

**When to reference:** Creating migrations, adding new features that need persistence, optimizing queries

### 4. docs/api-specification.md
**Purpose:** REST API design and endpoints

**Key Sections:**
- All API endpoints with request/response formats
- Authentication and authorization
- Error handling
- Rate limiting
- Webhook events

**When to reference:** Implementing API endpoints, integrating with frontend, writing API tests

### 5. docs/rag-implementation.md
**Purpose:** RAG system architecture and implementation

**Key Sections:**
- Document processing pipeline
- Embedding service
- Vector database integration
- Retrieval strategies
- Multi-tenant RAG

**When to reference:** Building knowledge base features, implementing document upload, optimizing retrieval

### 6. docs/mcp-implementation.md
**Purpose:** MCP servers and integration

**Key Sections:**
- MCP client integration
- Pre-built server specifications
- Server registry
- Security and sandboxing

**When to reference:** Creating new MCP servers, integrating tools with agents, extending capabilities

### 7. docs/deployment.md
**Purpose:** Infrastructure and deployment strategy

**Key Sections:**
- Docker Compose setup
- Kubernetes configuration
- CI/CD pipeline
- Monitoring and logging
- Multi-region deployment

**When to reference:** Setting up environments, deploying to production, scaling infrastructure

## Development Workflow

### 1. Feature Development

```bash
# Example: Adding a new feature
claude-code "I want to add workflow execution tracking. 

Based on:
- docs/database-schema.md: workflows and workflow_executions tables
- docs/api-specification.md: workflow endpoints
- docs/architecture.md: Phase 2 multi-agent orchestration

Implement:
1. Database models for workflows and workflow_executions
2. API endpoints for creating and executing workflows
3. Workflow engine that coordinates multiple agents
4. Status tracking and error handling"
```

### 2. Bug Fixes

```bash
claude-code "There's an issue with agent execution timing out. 

Review:
- Agent execution endpoint code
- Timeout configuration
- Add proper error handling and retry logic
- Ensure timeouts are configurable per agent"
```

### 3. Optimization

```bash
claude-code "The RAG retrieval is slow. 

Based on docs/rag-implementation.md:
- Review the current retrieval implementation
- Add caching for frequently accessed chunks
- Optimize vector similarity queries
- Add performance monitoring"
```

### 4. Testing

```bash
claude-code "Create comprehensive tests for the agent execution flow:
- Unit tests for agent creation and validation
- Integration tests for complete execution flow
- Mock LLM responses
- Test error cases and edge conditions"
```

## Best Practices for Claude Code Instructions

### ✅ Good Instructions

**Specific with context:**
```bash
claude-code "Based on docs/api-specification.md, implement the POST /v1/agents endpoint with:
- Request validation using Pydantic
- Database persistence using SQLAlchemy
- Return 201 on success with created agent
- Handle duplicate slug errors"
```

**Clear scope:**
```bash
claude-code "Create the Agent SQLAlchemy model based on the agents table definition in docs/database-schema.md. Include all fields, relationships, and constraints."
```

**References documentation:**
```bash
claude-code "Following the architecture in docs/architecture.md Phase 1, create the FastAPI application structure with proper separation of concerns: routers, services, models, and database."
```

### ❌ Avoid Vague Instructions

**Too vague:**
```bash
claude-code "Build the platform"  # Too broad
```

**Missing context:**
```bash
claude-code "Add RAG"  # Which part? What scope?
```

**No reference:**
```bash
claude-code "Make it better"  # Better how?
```

## Common Tasks

### Initialize Project

```bash
claude-code "Initialize the agentic platform project:

Based on PROJECT_CONTEXT.md Phase 1 and docs/deployment.md:
1. Create Python project with pyproject.toml
2. Set up FastAPI application structure
3. Create docker-compose.yml with PostgreSQL, Redis, pgvector
4. Add Alembic for migrations
5. Create .env.example with all required variables
6. Add README.md with setup instructions
7. Create basic project structure: src/, tests/, docs/"
```

### Add Database Tables

```bash
claude-code "Create Alembic migration for core tables:

Based on docs/database-schema.md, create migration for:
- tenants table
- users table
- agents table
- conversations table
- messages table
- tool_executions table

Include all indexes and constraints specified."
```

### Implement API Endpoint

```bash
claude-code "Implement the agent execution endpoint:

Based on docs/api-specification.md POST /v1/agents/:agent_id/execute:
1. Create Pydantic request/response models
2. Implement endpoint in agents router
3. Add authentication and tenant context
4. Integrate with Anthropic Claude API
5. Save conversation and messages to database
6. Handle tool calls
7. Return properly formatted response
8. Add error handling"
```

### Add Tests

```bash
claude-code "Create tests for the agent endpoints:

For each endpoint in docs/api-specification.md agents section:
- Test successful cases
- Test validation errors
- Test authentication failures
- Test tenant isolation
- Mock external dependencies (LLM API)
- Use pytest fixtures for common setup"
```

### Set Up RAG

```bash
claude-code "Implement basic RAG functionality:

Based on docs/rag-implementation.md Phase 1:
1. Create document upload endpoint
2. Implement chunking pipeline with configurable strategy
3. Generate embeddings using OpenAI
4. Store in pgvector
5. Create retrieval endpoint with top-k search
6. Add RAG tool for agents to query knowledge base"
```

### Create MCP Server

```bash
claude-code "Create the filesystem MCP server:

Based on docs/mcp-implementation.md section 'Filesystem MCP Server':
1. Implement using official MCP SDK
2. Add read_file, write_file, list_directory tools
3. Implement path traversal prevention
4. Add file size limits
5. Configure allowed paths via environment
6. Include comprehensive error handling
7. Add logging for all operations"
```

## Troubleshooting

### If Claude Code seems confused:

1. **Be more specific:** Reference exact document sections
2. **Break it down:** Ask for one component at a time
3. **Provide examples:** Show what you expect
4. **Review output:** Check if it matches specifications

### If implementation doesn't match specs:

```bash
claude-code "Review the agent execution endpoint implementation against docs/api-specification.md. 
The response format doesn't match the specification. Update it to match exactly."
```

### If you need clarification:

```bash
claude-code "Explain how the multi-agent orchestration should work based on docs/architecture.md Phase 2. 
What components are needed and how do they communicate?"
```

## Next Steps After Phase 1

Once Phase 1 MVP is complete and working:

1. **Phase 2 - Multi-Agent:**
   ```bash
   claude-code "Start Phase 2 based on PROJECT_CONTEXT.md:
   - Implement agent registry
   - Create workflow engine
   - Add RabbitMQ for agent communication
   - Build orchestration service"
   ```

2. **Phase 3 - Multi-Tenant:**
   ```bash
   claude-code "Implement multi-tenancy based on docs/architecture.md Phase 3:
   - Add tenant isolation middleware
   - Implement resource quotas
   - Create tenant management API
   - Add usage tracking"
   ```

3. **Phase 4 - Multi-Region:**
   ```bash
   claude-code "Prepare for multi-region deployment:
   - Create Kubernetes manifests based on docs/deployment.md Phase 4
   - Set up Terraform for infrastructure
   - Implement data replication strategy
   - Configure global load balancing"
   ```

## Tips for Success

1. **Start Small:** Build and test one feature at a time
2. **Reference Docs:** Always point Claude Code to specific documentation
3. **Test Frequently:** Ask for tests as you build features
4. **Iterate:** Review generated code and request improvements
5. **Stay Organized:** Keep code organized following the architecture
6. **Document:** Ask Claude Code to update documentation as features are added

## Questions?

If something is unclear or missing from the context documents:

```bash
claude-code "I need clarification on [specific topic]. 
Based on the docs, explain how [feature] should work and what needs to be implemented."
```

## Ready to Start?

Begin with Phase 1 MVP:

```bash
cd agentic-platform
claude-code "Read all files in docs/ and PROJECT_CONTEXT.md. 
Initialize Phase 1 MVP following the specifications. 
Start with project setup and docker-compose configuration."
```

Happy building! 🚀
