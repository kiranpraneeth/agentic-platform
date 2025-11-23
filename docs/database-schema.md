# Database Schema Design Specification

## Overview
Design a PostgreSQL database schema that is multi-tenant ready from day one, scalable, and follows best practices for data integrity and performance.

## Design Principles
- **Multi-tenant Ready**: Every table must include `tenant_id` for data isolation
- **Audit Trail**: Track who did what and when (created_at, updated_at, deleted_at)
- **Soft Deletes**: Use `deleted_at` timestamp instead of hard deletes where appropriate
- **Timestamps**: All tables should have `created_at` and `updated_at` timestamps
- **UUIDs**: Use UUIDs for primary keys for better distribution and security
- **Indexes**: Create indexes on foreign keys and commonly queried fields
- **JSONB**: Use JSONB for flexible metadata and configuration storage

## Required Tables

### 1. Tenants Table
Purpose: Store organization/tenant information for multi-tenancy.

Fields needed:
- Unique identifier (UUID)
- Name and URL-friendly slug
- Status (active, suspended, deleted)
- Plan type (free, starter, pro, enterprise)
- Resource limits (max agents, daily requests, monthly tokens)
- Contact information (email, contact name)
- Settings and metadata (JSONB for flexibility)
- Standard timestamps

Indexes: slug, status, deleted_at

### 2. Users Table
Purpose: User accounts that belong to tenants.

Fields needed:
- Unique identifier (UUID)
- Reference to tenant
- Email (unique per tenant), username
- Password hash
- Profile info (first name, last name, avatar)
- Status (active, inactive, suspended)
- Email verification status
- Last login timestamp
- Role (admin, user, viewer)
- Permissions array (JSONB)
- Standard timestamps

Indexes: tenant_id, email, status
Constraints: Unique combination of tenant_id and email

### 3. Agents Table
Purpose: Store agent definitions, configurations, and capabilities.

Fields needed:
- Unique identifier (UUID)
- Reference to tenant
- Name and slug (URL-friendly)
- Description
- Model configuration (provider, model name, temperature, max_tokens)
- System prompt
- Capabilities array (e.g., "data_analysis", "web_search")
- Tools array (e.g., "python_repl", "calculator")
- Resource limits (timeout, max iterations)
- Memory enabled flag
- Status (active, inactive, archived)
- Version string
- Tags, config, and metadata (JSONB)
- Standard timestamps

Indexes: tenant_id, status, combination of tenant_id and slug
Constraints: Unique combination of tenant_id and slug

### 4. Conversations Table
Purpose: Track conversation sessions between users and agents.

Fields needed:
- Unique identifier (UUID)
- References to tenant, agent, and user
- Title/summary
- Status (active, completed, failed, cancelled)
- Context and metadata (JSONB)
- Started timestamp
- Completed timestamp
- Standard timestamps

Indexes: tenant_id, agent_id, user_id, status, started_at (descending)

### 5. Messages Table
Purpose: Store individual messages within conversations.

Fields needed:
- Unique identifier (UUID)
- References to tenant and conversation
- Role (user, assistant, system, tool)
- Content (text)
- Token count
- Model used
- Tool calls and results (JSONB arrays)
- Latency in milliseconds
- Metadata (JSONB)
- Created timestamp
- Sequence number (for ordering within conversation)

Indexes: tenant_id, conversation_id, created_at, combination of conversation_id and sequence_number

### 6. Tool Executions Table
Purpose: Track all tool/function executions for debugging and analytics.

Fields needed:
- Unique identifier (UUID)
- References to tenant, conversation, message, and agent
- Tool name
- Tool input and output (JSONB)
- Status (success, error, timeout)
- Error message (if failed)
- Execution time in milliseconds
- Metadata (JSONB)
- Started and completed timestamps

Indexes: tenant_id, conversation_id, agent_id, tool_name, status, started_at (descending)

### 7. Workflows Table (Phase 2)
Purpose: Define multi-agent workflows.

Fields needed:
- Unique identifier (UUID)
- Reference to tenant
- Name and slug
- Description
- Workflow definition (JSONB - DAG or steps)
- List of agent IDs involved (JSONB array)
- Timeout and retry configuration
- Status and version
- Tags and metadata (JSONB)
- Standard timestamps

Indexes: tenant_id, status
Constraints: Unique combination of tenant_id and slug

### 8. Workflow Executions Table (Phase 2)
Purpose: Track instances of workflow runs.

Fields needed:
- Unique identifier (UUID)
- References to tenant, workflow, and user
- Status (running, completed, failed, cancelled)
- Current step being executed
- Input and output data (JSONB)
- Error message (if failed)
- Progress tracking (steps completed, steps total)
- Metadata (JSONB)
- Started, completed, and updated timestamps

Indexes: tenant_id, workflow_id, status, started_at (descending)

### 9. API Keys Table
Purpose: Manage API keys for programmatic access.

Fields needed:
- Unique identifier (UUID)
- References to tenant and user
- Key name
- Key hash (hashed version of actual key)
- Key prefix (first few characters for identification)
- Scopes/permissions (JSONB array like ["agents:read", "agents:execute"])
- Status (active, revoked, expired)
- Expiration timestamp
- Last used timestamp
- Metadata (JSONB)
- Standard timestamps

Indexes: tenant_id, key_hash, status
Constraints: key_hash must be unique

### 10. Usage Metrics Table
Purpose: Track resource usage for billing and quotas.

Fields needed:
- Unique identifier (UUID)
- Reference to tenant
- Metric type (api_calls, tokens, agent_executions, etc.)
- Metric value (integer count)
- Optional references to agent and user
- Metadata (JSONB)
- Recorded timestamp
- Period start and end timestamps

Indexes: tenant_id, metric_type, period range, recorded_at (descending)

### 11. Audit Logs Table
Purpose: Comprehensive audit trail for compliance and debugging.

Fields needed:
- Unique identifier (UUID)
- Reference to tenant
- Reference to user (actor who performed action)
- Action performed (e.g., "agent.created", "document.deleted")
- Resource type and resource ID (what was affected)
- Old and new values (JSONB for before/after state)
- IP address and user agent
- Status (success, failure)
- Error message (if failed)
- Metadata (JSONB)
- Timestamp

Indexes: tenant_id, user_id, action, resource_type, timestamp (descending)

## Implementation Notes

### Phase 1 (MVP)
Implement these tables first:
- tenants
- users  
- agents
- conversations
- messages
- tool_executions
- api_keys
- audit_logs

### Phase 2 (Multi-Agent + RAG + MCP)
Add these tables:
- workflows
- workflow_executions
- collections (RAG)
- documents (RAG)
- chunks (RAG)
- rag_queries (RAG)
- mcp_servers
- mcp_server_configs
- mcp_tool_executions

### Phase 3 (Multi-Tenancy Enhancement)
Add these tables:
- usage_metrics
- billing_records
- subscription_plans
- tenant_quotas

### Phase 4 (Multi-Region)
Add these tables:
- regions
- tenant_regions
- replication_status
- cross_region_sync_logs

## Additional Tables for RAG (Phase 2)

### collections Table
Purpose: Organize documents into knowledge base collections.

Fields needed:
- Unique identifier (UUID)
- Reference to tenant
- Name and slug
- Description
- Embedding model used (e.g., "text-embedding-3-small")
- Chunking configuration (chunk size, overlap)
- Document count
- Total chunks count
- Status (active, archived)
- Metadata and settings (JSONB)
- Standard timestamps

Indexes: tenant_id, slug, status

### documents Table
Purpose: Track uploaded documents in collections.

Fields needed:
- Unique identifier (UUID)
- Reference to tenant and collection
- Title and filename
- File type (pdf, docx, txt, etc.)
- File size in bytes
- Storage path/URL (S3 key)
- Processing status (pending, processing, indexed, failed)
- Chunk count
- Error message (if processing failed)
- Metadata (author, version, custom fields) (JSONB)
- Uploaded by user reference
- Standard timestamps

Indexes: tenant_id, collection_id, status, uploaded_at (descending)

### chunks Table
Purpose: Store document chunks with embeddings.

Fields needed:
- Unique identifier (UUID)
- Reference to tenant, collection, and document
- Chunk content (text)
- Chunk index/position in document
- Vector embedding (use vector type if pgvector, or JSONB for other stores)
- Embedding model used
- Token count
- Metadata (page number, section, headers) (JSONB)
- Created timestamp

Indexes: tenant_id, document_id, collection_id
Special indexes: Vector similarity index (HNSW or IVF for pgvector)

### rag_queries Table
Purpose: Log RAG queries for analytics and improvement.

Fields needed:
- Unique identifier (UUID)
- Reference to tenant, collection
- Query text
- Results returned (array of chunk IDs)
- Top result score
- Retrieval strategy used
- Filters applied (JSONB)
- Response time in milliseconds
- User feedback (if provided)
- Timestamp

Indexes: tenant_id, collection_id, timestamp (descending)

## Additional Tables for MCP (Phase 2)

### mcp_servers Table
Purpose: Registry of available MCP servers.

Fields needed:
- Unique identifier (UUID)
- Server name and slug
- Description
- Version
- Category (system, integration, data, etc.)
- Server type (stdio, sse)
- Command to start server
- Configuration schema (JSONB)
- Tool definitions (JSONB array)
- Resource definitions (JSONB array)
- Status (active, deprecated, disabled)
- Is public (available to all tenants)
- Documentation URL
- Repository URL
- Metadata (JSONB)
- Standard timestamps

Indexes: slug, category, status

### mcp_server_configs Table
Purpose: Tenant-specific MCP server configurations.

Fields needed:
- Unique identifier (UUID)
- Reference to tenant and mcp_server
- Enabled flag
- Configuration values (JSONB - secrets encrypted)
- Environment variables (JSONB - secrets encrypted)
- Resource limits (timeout, memory, etc.) (JSONB)
- Allowed users (array of user IDs or "all")
- Created by user reference
- Standard timestamps

Indexes: tenant_id, mcp_server_id, enabled
Constraints: Unique combination of tenant_id and mcp_server_id

### mcp_tool_executions Table
Purpose: Log MCP tool executions for debugging and analytics.

Fields needed:
- Unique identifier (UUID)
- Reference to tenant, mcp_server, agent
- Reference to conversation and message (if part of agent execution)
- Tool name
- Tool parameters (JSONB)
- Tool result (JSONB)
- Status (success, error, timeout)
- Error message and error code (if failed)
- Execution time in milliseconds
- Server instance ID
- Metadata (JSONB)
- Started and completed timestamps

Indexes: tenant_id, mcp_server_id, agent_id, tool_name, status, started_at (descending)

## Database Constraints and Relationships

### Foreign Key Constraints
- All tenant_id fields reference tenants(id) with ON DELETE CASCADE
- All user_id fields reference users(id) with ON DELETE SET NULL or CASCADE
- All agent_id fields reference agents(id) with ON DELETE CASCADE
- conversation_id references conversations(id) with ON DELETE CASCADE
- document_id references documents(id) with ON DELETE CASCADE
- collection_id references collections(id) with ON DELETE CASCADE

### Unique Constraints
- tenants: slug must be unique globally
- users: email must be unique per tenant (tenant_id, email)
- agents: slug must be unique per tenant (tenant_id, slug)
- api_keys: key_hash must be unique globally
- collections: slug must be unique per tenant (tenant_id, slug)
- workflows: slug must be unique per tenant (tenant_id, slug)

### Check Constraints
- temperature: Must be between 0.0 and 2.0
- max_tokens: Must be positive integer
- similarity scores: Between 0.0 and 1.0
- chunk_size: Must be positive integer
- Email format validation

## Indexes Strategy

### Performance Indexes
Create indexes on:
- All foreign keys
- Frequently filtered fields (status, created_at)
- Compound indexes for common query patterns
- Partial indexes where beneficial (e.g., WHERE deleted_at IS NULL)

### Examples of Compound Indexes
```sql
-- Messages by conversation, ordered
CREATE INDEX idx_messages_conversation_sequence 
ON messages(conversation_id, sequence_number);

-- Active agents per tenant
CREATE INDEX idx_agents_tenant_active 
ON agents(tenant_id, status) 
WHERE deleted_at IS NULL;

-- Recent conversations
CREATE INDEX idx_conversations_tenant_recent 
ON conversations(tenant_id, started_at DESC);

-- Vector similarity (for pgvector)
CREATE INDEX idx_chunks_embedding 
ON chunks USING ivfflat (embedding vector_cosine_ops) 
WITH (lists = 100);
```

## Row-Level Security (RLS) for Multi-Tenancy

If using PostgreSQL Row-Level Security:

### Enable RLS
```sql
ALTER TABLE agents ENABLE ROW LEVEL SECURITY;
ALTER TABLE conversations ENABLE ROW LEVEL SECURITY;
-- etc. for all tenant-scoped tables
```

### Create Policies
```sql
-- Policy: Users can only access their tenant's data
CREATE POLICY tenant_isolation ON agents
FOR ALL
USING (tenant_id = current_setting('app.current_tenant_id')::uuid);

-- Similar policies for all other tenant-scoped tables
```

### Application Usage
Set tenant context for each request:
```sql
SET LOCAL app.current_tenant_id = '{tenant_uuid}';
```

## Database Migrations Strategy

### Migration Files Structure
```
migrations/
├── versions/
│   ├── 001_initial_schema.py
│   ├── 002_add_workflows.py
│   ├── 003_add_rag_tables.py
│   ├── 004_add_mcp_tables.py
│   ├── 005_add_indexes.py
│   └── ...
└── alembic.ini
```

### Migration Best Practices
1. **Backward Compatible**: Make additive changes first
2. **Data Migration**: Include data transformation scripts
3. **Rollback Scripts**: Always include downgrade logic
4. **Test Migrations**: Test on copy of production data
5. **Version Control**: Commit migrations with code changes
6. **Documentation**: Comment complex migrations

### Sample Migration Workflow
```python
# Add new column (backward compatible)
def upgrade():
    op.add_column('agents', sa.Column('new_field', sa.String(255)))

# Remove old column after code deployment
def upgrade():
    op.drop_column('agents', 'old_field')
```

## Database Initialization

### Seed Data for Development
Create seed data script that populates:
- Default tenant for development
- Admin user
- Sample agents
- Test API keys
- Sample MCP servers

### Initial Setup Commands
```bash
# Create database
createdb agentic_platform

# Enable extensions
psql agentic_platform -c "CREATE EXTENSION IF NOT EXISTS \"uuid-ossp\";"
psql agentic_platform -c "CREATE EXTENSION IF NOT EXISTS \"pgvector\";"

# Run migrations
alembic upgrade head

# Seed development data
python scripts/seed_dev_data.py
```

## Performance Optimization

### Connection Pooling
- Use PgBouncer or built-in connection pooling
- Pool size: 20-50 connections per application instance
- Max connections based on (application instances × pool size) + buffer

### Query Optimization
- Use EXPLAIN ANALYZE for slow queries
- Add indexes based on query patterns
- Avoid N+1 queries (use JOINs or batch loading)
- Use database views for complex queries
- Consider materialized views for reports

### Partitioning Strategy (for large tables)
Consider partitioning for:
- **messages**: Partition by created_at (monthly)
- **audit_logs**: Partition by timestamp (monthly)
- **tool_executions**: Partition by started_at (monthly)
- **usage_metrics**: Partition by period_start (monthly)

Example:
```sql
-- Create partitioned table
CREATE TABLE messages (
    id UUID NOT NULL,
    created_at TIMESTAMP NOT NULL,
    -- other fields
) PARTITION BY RANGE (created_at);

-- Create partitions
CREATE TABLE messages_2025_01 PARTITION OF messages
FOR VALUES FROM ('2025-01-01') TO ('2025-02-01');
```

## Backup and Maintenance

### Backup Strategy
- **Full backup**: Daily at low-traffic time
- **Incremental backup**: Every 6 hours
- **WAL archiving**: Continuous for point-in-time recovery
- **Retention**: 30 days online, 90 days archived

### Maintenance Tasks
- **VACUUM**: Weekly on large tables
- **ANALYZE**: After significant data changes
- **REINDEX**: Monthly on heavily updated indexes
- **Update statistics**: After bulk operations

### Monitoring Queries
```sql
-- Check table sizes
SELECT schemaname, tablename, 
       pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) 
FROM pg_tables 
WHERE schemaname = 'public' 
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;

-- Check index usage
SELECT schemaname, tablename, indexname, idx_scan
FROM pg_stat_user_indexes
WHERE idx_scan = 0 AND indexrelname NOT LIKE 'pg_%';

-- Active connections
SELECT datname, count(*) 
FROM pg_stat_activity 
GROUP BY datname;
```

## Security Considerations

### Data Encryption
- Encrypt sensitive columns (password_hash, api key_hash)
- Use PostgreSQL pgcrypto for column encryption
- Transparent Data Encryption (TDE) at rest
- SSL/TLS for all connections

### Access Control
- Database users per service (read-only, read-write)
- Least privilege principle
- No direct production database access for developers
- Use bastion hosts or VPN for admin access

### Sensitive Data Handling
- Never log passwords or API keys
- Hash API keys before storage
- Rotate database passwords regularly
- Use secrets management (Vault, AWS Secrets Manager)

## Testing Database

### Test Database Setup
```bash
# Create test database
createdb agentic_platform_test

# Run migrations
ENVIRONMENT=test alembic upgrade head

# Run tests
pytest tests/
```

### Test Data Factories
Use factories for creating test data:
```python
# Using factory_boy or similar
class TenantFactory:
    tenant_id = uuid4()
    name = "Test Tenant"
    slug = "test-tenant"
    # ...
```

### Cleanup Between Tests
- Use transactions and rollback
- Or truncate tables
- Or recreate database

## Documentation Requirements

### Database Documentation
- ER diagrams showing all relationships
- Data dictionary for all tables and columns
- Index strategy explanation
- Migration history and changelog
- Common query patterns
- Troubleshooting guide

### Automated Documentation
- Generate docs from schema using tools like SchemaSpy
- Keep ER diagrams updated
- Document any denormalization decisions
- Explain partition strategy

## Summary

The database schema is designed to:
- Support multi-tenancy from day one
- Scale from single agent to multi-agent workflows
- Enable RAG with vector embeddings
- Support MCP server ecosystem
- Provide comprehensive audit trails
- Allow progressive feature rollout across 4 phases
- Maintain performance at scale
- Ensure data integrity and security

All tables follow consistent patterns:
- UUIDs for primary keys
- tenant_id for multi-tenancy
- created_at/updated_at timestamps
- deleted_at for soft deletes
- JSONB for flexible metadata
- Proper indexes for performance