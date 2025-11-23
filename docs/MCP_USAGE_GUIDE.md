# MCP (Model Context Protocol) Usage Guide

> **Complete guide to using MCP servers in the Agentic Platform**
>
> **Last Updated**: 2025-11-21

---

## Table of Contents

1. [Overview](#overview)
2. [Quick Start](#quick-start)
3. [Available MCP Servers](#available-mcp-servers)
4. [API Reference](#api-reference)
5. [Example Workflows](#example-workflows)
6. [Troubleshooting](#troubleshooting)
7. [Best Practices](#best-practices)

---

## Overview

MCP (Model Context Protocol) enables AI agents to interact with external tools and resources through a standardized protocol. The Agentic Platform provides pre-built MCP servers and the infrastructure to create custom servers.

### What You Can Do

- **File Operations**: Read, write, and manage files safely
- **Database Queries**: Execute SQL queries with safety controls
- **Custom Tools**: Create your own MCP servers for specific needs
- **Agent Integration**: Give agents access to tools dynamically

### Architecture

```
┌──────────┐          ┌────────────┐          ┌──────────────┐
│  Agent   │────────▶ │ MCP Client │◀────────▶│  MCP Server  │
│ (Claude) │          │  Service   │          │   (Process)  │
└──────────┘          └────────────┘          └──────────────┘
                            │
                            ▼
                      ┌──────────┐
                      │ Database │
                      │ (Audit)  │
                      └──────────┘
```

---

## Quick Start

### 1. Prerequisites

- API running on `http://localhost:8000`
- Valid JWT token (from `/v1/auth/login`)
- Tenant ID from authentication

### 2. Get Your Auth Token

```bash
# Login to get JWT token
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "admin@demo.com",
    "password": "admin123"
  }'

# Response includes:
# {
#   "access_token": "eyJ...",
#   "token_type": "bearer",
#   "user": {...}
# }

# Set token as environment variable
export TOKEN="your-access-token-here"
```

### 3. List Available MCP Servers

```bash
curl http://localhost:8000/api/v1/mcp/servers \
  -H "Authorization: Bearer $TOKEN"
```

### 4. Discover Server Capabilities

```bash
# Replace {server_id} with actual ID from list
curl http://localhost:8000/api/v1/mcp/servers/{server_id}/discover \
  -H "Authorization: Bearer $TOKEN"
```

### 5. Execute a Tool

```bash
curl -X POST http://localhost:8000/api/v1/mcp/execute \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "server_id": "{server_id}",
    "tool_name": "add",
    "tool_input": {"a": 5, "b": 3}
  }'
```

---

## Available MCP Servers

### 1. Calculator Server

**Purpose**: Simple math operations (testing/demonstration)

**Category**: Utility

**Tools**:

| Tool | Description | Input | Output |
|------|-------------|-------|--------|
| `add` | Add two numbers | `{a: number, b: number}` | `{result: number}` |
| `subtract` | Subtract b from a | `{a: number, b: number}` | `{result: number}` |
| `multiply` | Multiply two numbers | `{a: number, b: number}` | `{result: number}` |
| `divide` | Divide a by b | `{a: number, b: number}` | `{result: number}` |
| `power` | Raise base to exponent | `{base: number, exponent: number}` | `{result: number}` |

**Example**:

```bash
# Add two numbers
curl -X POST http://localhost:8000/api/v1/mcp/execute \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "server_id": "{calculator_server_id}",
    "tool_name": "add",
    "tool_input": {"a": 42, "b": 8}
  }'

# Response:
# {
#   "execution_id": "uuid",
#   "status": "success",
#   "tool_output": {"content": {"result": 50}},
#   "execution_time_ms": 15
# }
```

---

### 2. Filesystem Server

**Purpose**: Safe file system operations with sandboxing

**Category**: System

**Security Features**:
- Path traversal prevention
- Sandboxed to allowed directories (default: `/tmp`)
- File size limits (default: 10MB)
- Type validation

**Tools**:

| Tool | Description | Input | Output |
|------|-------------|-------|--------|
| `read_file` | Read file contents | `{path: string}` | `{content, size, path}` |
| `write_file` | Write to file | `{path: string, content: string}` | `{path, size, message}` |
| `list_directory` | List directory contents | `{path: string}` | `{entries[], count}` |
| `create_directory` | Create directory | `{path: string}` | `{path, message}` |
| `get_file_info` | Get file metadata | `{path: string}` | `{size, type, modified, ...}` |
| `delete_file` | Delete file | `{path: string}` | `{path, message}` |
| `search_files` | Search by pattern | `{directory: string, pattern: string}` | `{matches[], count}` |

**Examples**:

```bash
# Write a file
curl -X POST http://localhost:8000/api/v1/mcp/execute \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "server_id": "{filesystem_server_id}",
    "tool_name": "write_file",
    "tool_input": {
      "path": "/tmp/test.txt",
      "content": "Hello from MCP!"
    }
  }'

# Read the file
curl -X POST http://localhost:8000/api/v1/mcp/execute \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "server_id": "{filesystem_server_id}",
    "tool_name": "read_file",
    "tool_input": {"path": "/tmp/test.txt"}
  }'

# List directory
curl -X POST http://localhost:8000/api/v1/mcp/execute \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "server_id": "{filesystem_server_id}",
    "tool_name": "list_directory",
    "tool_input": {"path": "/tmp"}
  }'

# Search for Python files
curl -X POST http://localhost:8000/api/v1/mcp/execute \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "server_id": "{filesystem_server_id}",
    "tool_name": "search_files",
    "tool_input": {
      "directory": "/tmp",
      "pattern": "*.py"
    }
  }'
```

---

### 3. Database Server

**Purpose**: Read-only PostgreSQL database access

**Category**: Data

**Security Features**:
- Read-only mode (only SELECT queries)
- SQL injection prevention
- Query whitelisting
- Row limits (default: 1000)
- Schema restrictions

**Tools**:

| Tool | Description | Input | Output |
|------|-------------|-------|--------|
| `query` | Execute SELECT query | `{sql: string, params?: array}` | `{rows[], count, truncated}` |
| `list_tables` | List all tables | `{schema?: string}` | `{tables[], count}` |
| `describe_table` | Get table structure | `{table_name: string, schema?: string}` | `{columns[], indexes[]}` |
| `get_schema` | Get complete schema | `{schema?: string}` | `{tables[], table_count}` |

**Examples**:

```bash
# List all tables
curl -X POST http://localhost:8000/api/v1/mcp/execute \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "server_id": "{database_server_id}",
    "tool_name": "list_tables",
    "tool_input": {"schema": "public"}
  }'

# Describe a table
curl -X POST http://localhost:8000/api/v1/mcp/execute \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "server_id": "{database_server_id}",
    "tool_name": "describe_table",
    "tool_input": {
      "table_name": "agents",
      "schema": "public"
    }
  }'

# Query data
curl -X POST http://localhost:8000/api/v1/mcp/execute \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "server_id": "{database_server_id}",
    "tool_name": "query",
    "tool_input": {
      "sql": "SELECT name, status FROM agents WHERE status = $1",
      "params": ["active"]
    }
  }'

# Get complete schema
curl -X POST http://localhost:8000/api/v1/mcp/execute \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "server_id": "{database_server_id}",
    "tool_name": "get_schema",
    "tool_input": {"schema": "public"}
  }'
```

---

## API Reference

### Server Management

#### List Servers

```bash
GET /api/v1/mcp/servers?page=1&page_size=20&status=active&category=system&search=file
```

**Query Parameters**:
- `page`: Page number (default: 1)
- `page_size`: Items per page (default: 20, max: 100)
- `status`: Filter by status (inactive, ready, running, etc.)
- `category`: Filter by category (system, data, utility, etc.)
- `search`: Search in server names

**Response**:
```json
{
  "servers": [...],
  "total": 3,
  "page": 1,
  "page_size": 20,
  "has_more": false
}
```

#### Get Server Details

```bash
GET /api/v1/mcp/servers/{server_id}
```

#### Update Server

```bash
PATCH /api/v1/mcp/servers/{server_id}
Content-Type: application/json

{
  "name": "Updated Name",
  "status": "active",
  "config": {...}
}
```

#### Discover Capabilities

```bash
GET /api/v1/mcp/servers/{server_id}/discover
```

This connects to the server and discovers all available tools and resources.

#### Health Check

```bash
POST /api/v1/mcp/servers/{server_id}/health
```

### Tool Execution

#### Execute Tool

```bash
POST /api/v1/mcp/execute
Content-Type: application/json

{
  "server_id": "uuid",
  "tool_name": "tool_name",
  "tool_input": {...},
  "conversation_id": "uuid (optional)",
  "agent_id": "uuid (optional)"
}
```

**Response**:
```json
{
  "execution_id": "uuid",
  "server_id": "uuid",
  "tool_name": "add",
  "status": "success",
  "tool_output": {...},
  "error_message": null,
  "execution_time_ms": 15,
  "started_at": "2025-11-21T...",
  "completed_at": "2025-11-21T..."
}
```

#### List Executions

```bash
GET /api/v1/mcp/executions?server_id=uuid&agent_id=uuid&status=success&page=1
```

#### Get Execution Details

```bash
GET /api/v1/mcp/executions/{execution_id}
```

---

## Example Workflows

### Workflow 1: Data Analysis Pipeline

```bash
# 1. Query database for data
curl -X POST http://localhost:8000/api/v1/mcp/execute \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "server_id": "{db_server_id}",
    "tool_name": "query",
    "tool_input": {
      "sql": "SELECT * FROM agents WHERE created_at > NOW() - INTERVAL '\''7 days'\''"
    }
  }'

# 2. Save results to file
curl -X POST http://localhost:8000/api/v1/mcp/execute \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "server_id": "{fs_server_id}",
    "tool_name": "write_file",
    "tool_input": {
      "path": "/tmp/recent_agents.json",
      "content": "{\"data\": [...]}"
    }
  }'

# 3. Read and verify
curl -X POST http://localhost:8000/api/v1/mcp/execute \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "server_id": "{fs_server_id}",
    "tool_name": "get_file_info",
    "tool_input": {"path": "/tmp/recent_agents.json"}
  }'
```

### Workflow 2: Server Health Monitoring

```bash
# Check health of all servers
for server_id in $(curl -s http://localhost:8000/api/v1/mcp/servers \
  -H "Authorization: Bearer $TOKEN" | jq -r '.servers[].id'); do

  echo "Checking server: $server_id"
  curl -X POST "http://localhost:8000/api/v1/mcp/servers/$server_id/health" \
    -H "Authorization: Bearer $TOKEN"
done
```

---

## Troubleshooting

### Server Won't Start

**Problem**: Server status stays "starting" or changes to "failed"

**Solutions**:
1. Check server logs in execution history
2. Verify command and args are correct
3. Check environment variables are set
4. Ensure dependencies are installed

```bash
# Check recent executions with errors
curl http://localhost:8000/api/v1/mcp/executions?status=error&page_size=10 \
  -H "Authorization: Bearer $TOKEN"
```

### Tool Execution Timeout

**Problem**: Tool execution times out

**Solutions**:
1. Increase timeout in server config
2. Optimize tool implementation
3. Check for blocking operations

```bash
# Update timeout
curl -X PATCH http://localhost:8000/api/v1/mcp/servers/{server_id} \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"config": {"timeout_seconds": 60}}'
```

### Path Not Allowed (Filesystem)

**Problem**: "Path is not within allowed directories"

**Solution**: Update allowed paths in server configuration

```bash
# Check current config
curl http://localhost:8000/api/v1/mcp/servers/{server_id} \
  -H "Authorization: Bearer $TOKEN"

# Update allowed paths (requires server restart)
curl -X PATCH http://localhost:8000/api/v1/mcp/servers/{server_id} \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "args": ["-m", "src.mcp_servers.filesystem_server", "/tmp", "/app/data"]
  }'
```

### SQL Query Rejected (Database)

**Problem**: "Only SELECT queries are allowed"

**Solution**: Database server is in read-only mode by default

- Only SELECT and SHOW queries are permitted
- No INSERT, UPDATE, DELETE, DROP operations
- For write operations, create a custom server with appropriate permissions

---

## Best Practices

### Security

1. **Principle of Least Privilege**
   - Only grant necessary tool access
   - Use whitelisting over blacklisting
   - Restrict file paths and database schemas

2. **Input Validation**
   - Validate all tool inputs
   - Use parameterized queries
   - Sanitize file paths

3. **Audit Logging**
   - All executions are logged automatically
   - Review execution history regularly
   - Monitor for unusual patterns

### Performance

1. **Connection Pooling**
   - MCP client reuses server connections
   - Servers stay running between requests
   - Health checks prevent stale connections

2. **Timeouts**
   - Set appropriate timeouts for long-running operations
   - Use async operations where possible
   - Implement retry logic for transient failures

3. **Resource Limits**
   - File size limits prevent memory issues
   - Row limits prevent excessive data transfer
   - Rate limiting prevents abuse

### Development

1. **Testing**
   - Use calculator server for basic testing
   - Test error conditions
   - Verify audit logs

2. **Monitoring**
   - Track execution times
   - Monitor error rates
   - Set up alerts for failures

3. **Documentation**
   - Document custom tools clearly
   - Provide input/output examples
   - Include error codes and messages

---

## Next Steps

1. **Create Custom MCP Servers**
   - Follow `src/mcp_servers/base_server.py` pattern
   - Implement `get_tools()` and `handle_tool_call()`
   - Test thoroughly before production

2. **Integrate with Agents**
   - Configure agents to use MCP tools
   - Provide tool access based on agent role
   - Monitor agent tool usage

3. **Build Workflows**
   - Combine multiple tools
   - Create automation pipelines
   - Implement error handling

---

## Support

- **Documentation**: `docs/mcp-implementation.md`
- **API Docs**: `http://localhost:8000/docs#/mcp`
- **Examples**: `docs/MCP_USAGE_GUIDE.md` (this file)
- **Source Code**: `src/mcp_servers/`

---

*Last Updated: 2025-11-21*
*Version: 1.0*
