# API Specification

## Overview
RESTful API design for the agentic platform with versioning, authentication, and comprehensive documentation.

## General API Principles

### Base URL Structure
```
https://api.platform.com/v1/{resource}
```

### Versioning
- Version in URL path (/v1/, /v2/)
- Support at least 2 versions simultaneously
- Deprecation notices 6 months in advance

### Authentication
- API Key in header: `Authorization: Bearer {api_key}`
- JWT tokens for user sessions
- OAuth 2.0 for third-party integrations

### Request/Response Format
- Content-Type: `application/json`
- Character encoding: UTF-8
- Date format: ISO 8601 (e.g., "2025-01-15T10:30:00Z")

### Status Codes
- 200: Success
- 201: Created
- 204: No Content
- 400: Bad Request
- 401: Unauthorized
- 403: Forbidden
- 404: Not Found
- 429: Too Many Requests
- 500: Internal Server Error
- 503: Service Unavailable

### Error Response Format
```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Invalid input parameters",
    "details": [
      {
        "field": "agent_id",
        "issue": "Agent ID is required"
      }
    ],
    "request_id": "req_123abc"
  }
}
```

### Pagination
```
GET /v1/agents?page=2&limit=20
```

Response includes:
```json
{
  "data": [...],
  "pagination": {
    "page": 2,
    "limit": 20,
    "total": 150,
    "total_pages": 8
  }
}
```

### Rate Limiting
- Header: `X-RateLimit-Limit`, `X-RateLimit-Remaining`, `X-RateLimit-Reset`
- Limits based on plan tier
- 429 status when exceeded

## API Endpoints

### Authentication

#### POST /v1/auth/login
Login and receive JWT token.

**Request:**
```json
{
  "email": "user@example.com",
  "password": "secure_password"
}
```

**Response:**
```json
{
  "access_token": "jwt_token",
  "refresh_token": "refresh_token",
  "expires_in": 3600,
  "user": {
    "id": "user_uuid",
    "email": "user@example.com",
    "role": "admin"
  }
}
```

#### POST /v1/auth/refresh
Refresh expired token.

#### POST /v1/auth/logout
Invalidate current session.

### Agents

#### POST /v1/agents
Create a new agent.

**Request:**
```json
{
  "name": "Customer Support Agent",
  "slug": "customer-support",
  "description": "Handles customer inquiries and support tickets",
  "model_provider": "anthropic",
  "model_name": "claude-sonnet-4-5",
  "system_prompt": "You are a helpful customer support agent...",
  "temperature": 0.7,
  "max_tokens": 4096,
  "capabilities": ["conversation", "data_retrieval"],
  "tools": ["web_search", "database_query"],
  "config": {
    "memory_enabled": true,
    "timeout_seconds": 300
  }
}
```

**Response:** (201 Created)
```json
{
  "id": "agent_uuid",
  "tenant_id": "tenant_uuid",
  "name": "Customer Support Agent",
  "slug": "customer-support",
  "status": "active",
  "created_at": "2025-01-15T10:30:00Z",
  "...": "all other fields"
}
```

#### GET /v1/agents
List all agents for tenant.

**Query Parameters:**
- `page`: Page number (default: 1)
- `limit`: Results per page (default: 20, max: 100)
- `status`: Filter by status (active, inactive, archived)
- `search`: Search by name or description
- `sort`: Sort field (created_at, name, updated_at)
- `order`: Sort order (asc, desc)

**Response:** (200 OK)
```json
{
  "data": [
    {
      "id": "agent_uuid",
      "name": "Customer Support Agent",
      "slug": "customer-support",
      "status": "active",
      "model_name": "claude-sonnet-4-5",
      "created_at": "2025-01-15T10:30:00Z"
    }
  ],
  "pagination": {
    "page": 1,
    "limit": 20,
    "total": 5,
    "total_pages": 1
  }
}
```

#### GET /v1/agents/:agent_id
Get agent details.

**Response:** (200 OK)
```json
{
  "id": "agent_uuid",
  "tenant_id": "tenant_uuid",
  "name": "Customer Support Agent",
  "slug": "customer-support",
  "description": "...",
  "model_provider": "anthropic",
  "model_name": "claude-sonnet-4-5",
  "system_prompt": "...",
  "temperature": 0.7,
  "max_tokens": 4096,
  "capabilities": ["conversation", "data_retrieval"],
  "tools": ["web_search", "database_query"],
  "status": "active",
  "version": "1.0.0",
  "config": {...},
  "metadata": {...},
  "created_at": "2025-01-15T10:30:00Z",
  "updated_at": "2025-01-15T10:30:00Z"
}
```

#### PATCH /v1/agents/:agent_id
Update agent configuration.

**Request:**
```json
{
  "description": "Updated description",
  "system_prompt": "New system prompt",
  "temperature": 0.8,
  "tools": ["web_search", "database_query", "calculator"]
}
```

**Response:** (200 OK) - Returns updated agent

#### DELETE /v1/agents/:agent_id
Delete (soft delete) an agent.

**Response:** (204 No Content)

#### POST /v1/agents/:agent_id/execute
Execute agent with a task/prompt.

**Request:**
```json
{
  "input": "What is the status of order #12345?",
  "conversation_id": "optional_existing_conversation_uuid",
  "context": {
    "user_id": "user_uuid",
    "session_id": "session_123"
  },
  "stream": false,
  "max_iterations": 5
}
```

**Response:** (200 OK)
```json
{
  "conversation_id": "conversation_uuid",
  "message_id": "message_uuid",
  "response": "Order #12345 is currently in transit...",
  "tool_calls": [
    {
      "tool": "database_query",
      "input": {"order_id": "12345"},
      "output": {...}
    }
  ],
  "token_usage": {
    "input_tokens": 150,
    "output_tokens": 200,
    "total_tokens": 350
  },
  "latency_ms": 1250,
  "created_at": "2025-01-15T10:35:00Z"
}
```

**Streaming Response:** (if stream=true)
Server-Sent Events (SSE) format:
```
event: token
data: {"content": "Order "}

event: token
data: {"content": "#12345 "}

event: tool_call
data: {"tool": "database_query", "input": {...}}

event: tool_result
data: {"output": {...}}

event: complete
data: {"conversation_id": "...", "total_tokens": 350}
```

### Conversations

#### GET /v1/conversations
List conversations.

**Query Parameters:**
- `agent_id`: Filter by agent
- `user_id`: Filter by user
- `status`: Filter by status
- `page`, `limit`: Pagination

**Response:** (200 OK)
```json
{
  "data": [
    {
      "id": "conversation_uuid",
      "agent_id": "agent_uuid",
      "user_id": "user_uuid",
      "title": "Order Status Inquiry",
      "status": "completed",
      "message_count": 8,
      "started_at": "2025-01-15T10:00:00Z",
      "completed_at": "2025-01-15T10:15:00Z"
    }
  ],
  "pagination": {...}
}
```

#### GET /v1/conversations/:conversation_id
Get conversation details with messages.

**Response:** (200 OK)
```json
{
  "id": "conversation_uuid",
  "agent_id": "agent_uuid",
  "agent_name": "Customer Support Agent",
  "user_id": "user_uuid",
  "title": "Order Status Inquiry",
  "status": "completed",
  "messages": [
    {
      "id": "message_uuid",
      "role": "user",
      "content": "What is the status of order #12345?",
      "created_at": "2025-01-15T10:00:00Z"
    },
    {
      "id": "message_uuid_2",
      "role": "assistant",
      "content": "Let me check that for you...",
      "tool_calls": [...],
      "token_count": 150,
      "created_at": "2025-01-15T10:00:05Z"
    }
  ],
  "context": {...},
  "metadata": {...},
  "started_at": "2025-01-15T10:00:00Z",
  "completed_at": "2025-01-15T10:15:00Z"
}
```

#### DELETE /v1/conversations/:conversation_id
Delete a conversation.

**Response:** (204 No Content)

### RAG (Knowledge Base)

#### POST /v1/collections
Create a knowledge base collection.

**Request:**
```json
{
  "name": "Product Documentation",
  "slug": "product-docs",
  "description": "All product documentation and guides",
  "embedding_model": "text-embedding-3-small",
  "chunk_size": 512,
  "chunk_overlap": 50,
  "metadata": {
    "category": "documentation"
  }
}
```

**Response:** (201 Created)
```json
{
  "id": "collection_uuid",
  "tenant_id": "tenant_uuid",
  "name": "Product Documentation",
  "slug": "product-docs",
  "document_count": 0,
  "total_chunks": 0,
  "embedding_model": "text-embedding-3-small",
  "status": "active",
  "created_at": "2025-01-15T10:30:00Z"
}
```

#### GET /v1/collections
List collections.

**Response:** (200 OK) - Paginated list of collections

#### GET /v1/collections/:collection_id
Get collection details.

#### POST /v1/collections/:collection_id/documents
Upload document to collection.

**Request:** (multipart/form-data)
```
file: [PDF/DOCX/TXT file]
metadata: {
  "title": "User Guide",
  "author": "Product Team",
  "version": "2.0"
}
```

**Response:** (202 Accepted)
```json
{
  "document_id": "document_uuid",
  "status": "processing",
  "estimated_time_seconds": 30
}
```

#### GET /v1/collections/:collection_id/documents
List documents in collection.

**Response:** (200 OK)
```json
{
  "data": [
    {
      "id": "document_uuid",
      "title": "User Guide",
      "filename": "user-guide.pdf",
      "status": "indexed",
      "chunk_count": 45,
      "size_bytes": 1024000,
      "uploaded_at": "2025-01-15T10:30:00Z"
    }
  ],
  "pagination": {...}
}
```

#### DELETE /v1/collections/:collection_id/documents/:document_id
Delete document from collection.

**Response:** (204 No Content)

#### POST /v1/collections/:collection_id/query
Query collection for relevant information.

**Request:**
```json
{
  "query": "How do I reset my password?",
  "top_k": 5,
  "similarity_threshold": 0.7,
  "filters": {
    "category": "authentication"
  },
  "rerank": true
}
```

**Response:** (200 OK)
```json
{
  "query": "How do I reset my password?",
  "results": [
    {
      "chunk_id": "chunk_uuid",
      "content": "To reset your password, navigate to...",
      "score": 0.95,
      "metadata": {
        "document_id": "document_uuid",
        "document_title": "User Guide",
        "page": 12,
        "section": "Authentication"
      }
    }
  ],
  "total_results": 3,
  "retrieval_time_ms": 85
}
```

### MCP Servers

#### GET /v1/mcp/servers
List available MCP servers.

**Response:** (200 OK)
```json
{
  "data": [
    {
      "id": "server_uuid",
      "name": "filesystem-server",
      "description": "Safe filesystem access",
      "version": "1.0.0",
      "category": "system",
      "status": "active",
      "tools": ["read_file", "write_file", "list_directory"]
    }
  ]
}
```

#### GET /v1/mcp/servers/:server_id
Get MCP server details.

**Response:** (200 OK)
```json
{
  "id": "server_uuid",
  "name": "filesystem-server",
  "description": "Safe filesystem access",
  "version": "1.0.0",
  "category": "system",
  "status": "active",
  "tools": [
    {
      "name": "read_file",
      "description": "Read file contents",
      "input_schema": {
        "type": "object",
        "properties": {
          "path": {"type": "string"}
        },
        "required": ["path"]
      }
    }
  ],
  "configuration_schema": {...},
  "documentation_url": "https://..."
}
```

#### POST /v1/mcp/servers/:server_id/configure
Configure MCP server for tenant.

**Request:**
```json
{
  "config": {
    "allowed_paths": ["/data/tenant-files"],
    "max_file_size": 10485760
  },
  "enabled": true
}
```

**Response:** (200 OK)
```json
{
  "server_id": "server_uuid",
  "tenant_id": "tenant_uuid",
  "config": {...},
  "enabled": true,
  "configured_at": "2025-01-15T10:30:00Z"
}
```

#### POST /v1/mcp/servers/:server_id/execute
Execute MCP tool directly (for testing).

**Request:**
```json
{
  "tool": "read_file",
  "parameters": {
    "path": "/data/tenant-files/document.txt"
  }
}
```

**Response:** (200 OK)
```json
{
  "success": true,
  "result": {
    "content": "File contents here..."
  },
  "execution_time_ms": 45
}
```

### Workflows (Phase 2)

#### POST /v1/workflows
Create a multi-agent workflow.

**Request:**
```json
{
  "name": "Customer Onboarding",
  "slug": "customer-onboarding",
  "description": "Automated customer onboarding process",
  "definition": {
    "steps": [
      {
        "id": "collect_info",
        "agent_id": "agent_uuid_1",
        "prompt": "Collect customer information"
      },
      {
        "id": "verify_email",
        "agent_id": "agent_uuid_2",
        "prompt": "Verify email address",
        "depends_on": ["collect_info"]
      }
    ]
  },
  "timeout_seconds": 600
}
```

**Response:** (201 Created) - Workflow object

#### POST /v1/workflows/:workflow_id/execute
Execute a workflow.

**Request:**
```json
{
  "input": {
    "customer_email": "new@example.com",
    "company_name": "Acme Corp"
  },
  "context": {...}
}
```

**Response:** (202 Accepted)
```json
{
  "execution_id": "execution_uuid",
  "workflow_id": "workflow_uuid",
  "status": "running",
  "started_at": "2025-01-15T10:30:00Z"
}
```

#### GET /v1/workflows/:workflow_id/executions/:execution_id
Get workflow execution status.

**Response:** (200 OK)
```json
{
  "id": "execution_uuid",
  "workflow_id": "workflow_uuid",
  "status": "completed",
  "current_step": "verify_email",
  "steps_completed": 2,
  "steps_total": 2,
  "input": {...},
  "output": {...},
  "started_at": "2025-01-15T10:30:00Z",
  "completed_at": "2025-01-15T10:35:00Z"
}
```

### Usage & Analytics

#### GET /v1/usage/summary
Get usage summary for tenant.

**Query Parameters:**
- `start_date`: Start date (ISO 8601)
- `end_date`: End date (ISO 8601)
- `metric_type`: Filter by metric type

**Response:** (200 OK)
```json
{
  "period": {
    "start": "2025-01-01T00:00:00Z",
    "end": "2025-01-31T23:59:59Z"
  },
  "metrics": {
    "api_calls": 15420,
    "tokens_used": 2450000,
    "agent_executions": 3200,
    "documents_indexed": 150
  },
  "breakdown_by_agent": [
    {
      "agent_id": "agent_uuid",
      "agent_name": "Customer Support",
      "executions": 1500,
      "tokens": 850000
    }
  ]
}
```

#### GET /v1/usage/quotas
Get current quota usage and limits.

**Response:** (200 OK)
```json
{
  "plan": "pro",
  "quotas": {
    "api_calls": {
      "used": 15420,
      "limit": 100000,
      "reset_at": "2025-02-01T00:00:00Z"
    },
    "tokens": {
      "used": 2450000,
      "limit": 10000000,
      "reset_at": "2025-02-01T00:00:00Z"
    },
    "agents": {
      "used": 5,
      "limit": 20
    }
  }
}
```

### Admin (Tenant Management)

#### POST /v1/admin/tenants
Create a new tenant (admin only).

**Request:**
```json
{
  "name": "Acme Corporation",
  "slug": "acme-corp",
  "email": "admin@acme.com",
  "plan_type": "pro",
  "max_agents": 20,
  "max_requests_per_day": 50000
}
```

**Response:** (201 Created) - Tenant object

#### GET /v1/admin/tenants
List all tenants (admin only).

#### PATCH /v1/admin/tenants/:tenant_id
Update tenant configuration (admin only).

#### POST /v1/admin/tenants/:tenant_id/suspend
Suspend tenant account (admin only).

## Webhook Events

Webhooks can be configured to notify external systems of events.

### Event Types
- `agent.executed`: Agent completed execution
- `conversation.completed`: Conversation finished
- `document.indexed`: Document finished indexing
- `workflow.completed`: Workflow execution finished
- `quota.exceeded`: Usage quota exceeded
- `error.occurred`: System error occurred

### Webhook Payload
```json
{
  "event": "agent.executed",
  "timestamp": "2025-01-15T10:35:00Z",
  "tenant_id": "tenant_uuid",
  "data": {
    "agent_id": "agent_uuid",
    "conversation_id": "conversation_uuid",
    "status": "success",
    "token_usage": 350
  }
}
```

### Webhook Configuration
```
POST /v1/webhooks

{
  "url": "https://your-domain.com/webhook",
  "events": ["agent.executed", "conversation.completed"],
  "secret": "webhook_secret_for_signature"
}
```

## SDK Examples

### Python SDK Usage
```python
from agentic_platform import AgenticPlatform

client = AgenticPlatform(api_key="your_api_key")

# Create agent
agent = client.agents.create(
    name="Support Agent",
    model_name="claude-sonnet-4-5",
    system_prompt="You are a helpful assistant"
)

# Execute agent
response = client.agents.execute(
    agent_id=agent.id,
    input="Help me with my order"
)

print(response.content)
```

### JavaScript/TypeScript SDK Usage
```typescript
import { AgenticPlatform } from '@agentic-platform/sdk';

const client = new AgenticPlatform({
  apiKey: 'your_api_key'
});

// Create agent
const agent = await client.agents.create({
  name: 'Support Agent',
  modelName: 'claude-sonnet-4-5',
  systemPrompt: 'You are a helpful assistant'
});

// Execute agent with streaming
const stream = await client.agents.executeStream({
  agentId: agent.id,
  input: 'Help me with my order'
});

for await (const chunk of stream) {
  process.stdout.write(chunk.content);
}
```

## Rate Limits by Plan

| Plan | Requests/Day | Tokens/Month | Agents | Collections |
|------|-------------|--------------|--------|-------------|
| Free | 1,000 | 100K | 3 | 1 |
| Starter | 10,000 | 1M | 10 | 5 |
| Pro | 100,000 | 10M | 50 | 20 |
| Enterprise | Custom | Custom | Unlimited | Unlimited |

## API Versioning and Deprecation

- New versions introduced with breaking changes
- Old versions supported for 12 months minimum
- Deprecation warnings in response headers
- Migration guides provided
- Sunset date communicated in advance

## OpenAPI/Swagger Documentation

All endpoints should be documented in OpenAPI 3.0 format and available at:
```
GET /v1/docs
GET /v1/openapi.json
```

Interactive API explorer available at web interface.