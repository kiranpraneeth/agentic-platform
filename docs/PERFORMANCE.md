# Performance Optimization Guide

> **Comprehensive performance optimizations for the Agentic Platform**
>
> **Version**: 1.0.0
> **Phase**: 3 - Production Readiness

---

## Table of Contents

1. [Overview](#overview)
2. [Database Optimizations](#database-optimizations)
3. [Caching Strategy](#caching-strategy)
4. [Rate Limiting](#rate-limiting)
5. [Connection Pooling](#connection-pooling)
6. [Batch Processing](#batch-processing)
7. [Load Testing](#load-testing)
8. [Performance Metrics](#performance-metrics)
9. [Best Practices](#best-practices)
10. [Troubleshooting](#troubleshooting)

---

## Overview

The Agentic Platform implements comprehensive performance optimizations across multiple layers:

| Layer | Optimization | Impact |
|-------|--------------|--------|
| **Database** | Indexes, query optimization | 5-10x faster queries |
| **Caching** | Redis caching layer | 50-100x faster reads |
| **API** | Rate limiting | Prevent abuse |
| **Connections** | Optimized pooling | Better resource utilization |
| **Batch** | Bulk operations | 10-50x faster bulk inserts |

### Performance Targets

| Metric | Target | Acceptable |
|--------|--------|------------|
| **API Response (p95)** | < 200ms | < 500ms |
| **Database Query (p95)** | < 50ms | < 200ms |
| **Cache Hit Rate** | > 80% | > 60% |
| **Throughput** | > 100 req/s | > 50 req/s |
| **Error Rate** | < 0.1% | < 1% |

---

## Database Optimizations

### Indexes Added

**Migration:** `alembic/versions/20250115_0000_add_performance_indexes.py`

#### User & Tenant Indexes
```sql
-- Users
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_tenant_id ON users(tenant_id);
CREATE INDEX idx_users_tenant_status ON users(tenant_id, status);

-- Tenants
CREATE INDEX idx_tenants_slug ON tenants(slug);
CREATE INDEX idx_tenants_status ON tenants(status);
```

#### Agent Indexes
```sql
CREATE INDEX idx_agents_tenant_id ON agents(tenant_id);
CREATE INDEX idx_agents_slug ON agents(slug);
CREATE INDEX idx_agents_tenant_slug ON agents(tenant_id, slug);  -- Composite for lookups
CREATE INDEX idx_agents_status ON agents(status);
CREATE INDEX idx_agents_created_at ON agents(created_at);  -- For sorting
CREATE INDEX idx_agents_deleted_at ON agents(deleted_at);  -- Soft deletes
```

#### Conversation Indexes
```sql
CREATE INDEX idx_conversations_tenant_id ON conversations(tenant_id);
CREATE INDEX idx_conversations_agent_id ON conversations(agent_id);
CREATE INDEX idx_conversations_user_id ON conversations(user_id);
CREATE INDEX idx_conversations_tenant_created ON conversations(tenant_id, created_at);  -- Composite for pagination
```

#### RAG Indexes
```sql
-- Collections
CREATE INDEX idx_collections_tenant_id ON collections(tenant_id);
CREATE INDEX idx_collections_tenant_slug ON collections(tenant_id, slug);

-- Documents
CREATE INDEX idx_documents_collection_id ON documents(collection_id);
CREATE INDEX idx_documents_collection_status ON documents(collection_id, status);

-- Vector index for semantic search (HNSW algorithm)
CREATE INDEX idx_chunks_embedding_hnsw ON document_chunks
  USING hnsw (embedding vector_cosine_ops)
  WITH (m = 16, ef_construction = 64);
```

**Impact:** 5-10x faster queries on indexed columns

### Query Optimization Tips

#### Use Indexes Effectively
```python
# Good: Uses index
agents = await db.execute(
    select(Agent).where(
        Agent.tenant_id == tenant_id,
        Agent.status == "active"
    )
)

# Bad: Full table scan
agents = await db.execute(
    select(Agent).where(Agent.name.like("%test%"))
)
```

#### Eager Loading to Prevent N+1
```python
# Good: Eager load relationships
from sqlalchemy.orm import selectinload

agents = await db.execute(
    select(Agent)
    .options(selectinload(Agent.conversations))
    .where(Agent.tenant_id == tenant_id)
)

# Bad: N+1 queries
agents = await db.execute(select(Agent))
for agent in agents:
    conversations = await db.execute(
        select(Conversation).where(Conversation.agent_id == agent.id)
    )
```

#### Use Pagination
```python
# Good: Limit results
agents = await db.execute(
    select(Agent)
    .where(Agent.tenant_id == tenant_id)
    .limit(100)
    .offset(0)
)

# Bad: Load all results
agents = await db.execute(
    select(Agent).where(Agent.tenant_id == tenant_id)
)
```

### Apply Migration

```bash
# Run migration
docker-compose exec api alembic upgrade head

# Verify indexes
docker-compose exec db psql -U postgres -d agentic_db -c "\d+ agents"
```

---

## Caching Strategy

**Location:** `src/core/cache.py`

### Cache Service

```python
from src.core.cache import cache, agent_cache_key

# Get from cache
cached_agent = await cache.get(
    agent_cache_key(tenant_id, agent_id),
    cache_type="agent"
)

if cached_agent:
    return cached_agent

# Cache miss - fetch from DB
agent = await db.get(Agent, agent_id)

# Store in cache (5 minute TTL)
await cache.set(
    agent_cache_key(tenant_id, agent_id),
    agent.to_dict(),
    ttl=300,
    cache_type="agent"
)
```

### What to Cache

| Data Type | TTL | Key Pattern |
|-----------|-----|-------------|
| **Agents** | 5 minutes | `agent:{tenant_id}:{agent_id}` |
| **Workflows** | 5 minutes | `workflow:{tenant_id}:{workflow_id}` |
| **MCP Servers** | 10 minutes | `mcp_server:{tenant_id}:{server_id}` |
| **Embeddings** | 1 hour | `embedding:{model}:{text_hash}` |
| **RAG Search** | 5 minutes | `rag_search:{collection_id}:{query_hash}:{top_k}` |

### Cache Invalidation

```python
# Invalidate on update
await cache.delete(agent_cache_key(tenant_id, agent_id))

# Invalidate pattern (e.g., all agents for tenant)
await cache.delete_pattern(f"agent:{tenant_id}:*")
```

### Cache Metrics

Monitor cache performance:
- `cache_hits_total` - Total cache hits
- `cache_misses_total` - Total cache misses
- Hit rate = hits / (hits + misses)

**Target:** > 80% hit rate for frequently accessed data

---

## Rate Limiting

**Location:** `src/core/rate_limit.py`

### Global Rate Limits

Applied to all API requests:
- **60 requests/minute** per client
- **1000 requests/hour** per client

### Configuration

```python
# In src/main.py
app.add_middleware(
    RateLimitMiddleware,
    requests_per_minute=60,
    requests_per_hour=1000,
    enabled=True,
)
```

### Response Headers

Every request includes rate limit headers:
```
X-RateLimit-Limit: 60
X-RateLimit-Remaining: 45
X-RateLimit-Reset: 1705315200
```

### Endpoint-Specific Limits

For expensive operations:

```python
from fastapi import Depends
from src.core.rate_limit import expensive_endpoint_limiter

@router.post("/workflows/execute")
async def execute_workflow(
    _: None = Depends(expensive_endpoint_limiter),  # 10/min limit
):
    ...
```

### Exempted Endpoints

These endpoints bypass rate limiting:
- `/health`
- `/health/ready`
- `/health/live`
- `/metrics`
- `/docs`

### Disable for Testing

```bash
# In .env
RATE_LIMIT_ENABLED=false

# Restart
docker-compose restart api
```

---

## Connection Pooling

**Location:** `src/db/session.py`

### Database Pool Configuration

```python
engine = create_async_engine(
    DATABASE_URL,
    pool_size=20,              # Base pool size
    max_overflow=10,           # Additional connections
    pool_pre_ping=True,        # Verify connections
    pool_recycle=3600,         # Recycle after 1 hour
    poolclass=QueuePool,       # Queue-based pooling
)
```

**Total Connections:** 20 (base) + 10 (overflow) = 30 max

### Redis Pool Configuration

```python
redis_client = redis.from_url(
    REDIS_URL,
    max_connections=10,        # Connection pool size
    decode_responses=True,
)
```

### Monitor Pool Usage

```python
from src.db.session import get_pool_status

status = get_pool_status()
# {
#   'size': 20,
#   'checked_in': 15,
#   'checked_out': 5,
#   'overflow': 2,
#   'total': 22
# }
```

### Pool Metrics

- `db_connection_pool_size` - Current connections in use
- `db_connection_pool_overflow` - Overflow connections

**Alert:** If overflow > 80% of max_overflow

---

## Batch Processing

**Location:** `src/core/batch.py`

### Batch Insert

Instead of inserting one at a time:

```python
# Bad: Individual inserts (slow)
for document in documents:
    db.add(document)
    await db.commit()

# Good: Batch insert (fast)
from src.core.batch import batch_insert

await batch_insert(db, documents, batch_size=1000)
```

**Speed Improvement:** 10-50x faster

### Batch Embeddings

```python
from src.core.batch import batch_generate_embeddings

texts = [doc.content for doc in documents]

embeddings = await batch_generate_embeddings(
    texts,
    embedding_fn=generate_embedding,
    batch_size=50,          # 50 texts per batch
    max_concurrent=3,       # 3 concurrent batches
)
```

### Batch Processor (Auto-Flush)

```python
from src.core.batch import BatchProcessor

# Create processor with auto-flush
processor = BatchProcessor(
    process_fn=process_batch,
    batch_size=100,
    flush_interval=5.0,     # Flush every 5 seconds
)

# Add items (auto-flushes when batch is full)
for item in items:
    await processor.add(item)

# Manual flush
await processor.flush()
```

### Bulk Operations

```python
from src.core.batch import BulkOperationHelper

helper = BulkOperationHelper(db, batch_size=1000)

# Queue operations
for document in documents:
    await helper.add_insert(document)

# Flush all at once
await helper.flush_all()
```

---

## Load Testing

**Location:** `load_tests/`

### Quick Start

```bash
# Install Locust
pip install locust

# Run tests
cd load_tests
locust -f locustfile.py

# Open web UI
open http://localhost:8089
```

### Test Profiles

#### Development (Light)
```bash
locust -f locustfile.py \
  --headless \
  --users 10 \
  --spawn-rate 1 \
  --run-time 2m
```

#### Staging (Medium)
```bash
locust -f locustfile.py \
  --headless \
  --users 50 \
  --spawn-rate 5 \
  --run-time 10m
```

#### Production (Heavy)
```bash
locust -f locustfile.py \
  --headless \
  --users 200 \
  --spawn-rate 10 \
  --run-time 30m
```

### Monitoring During Tests

1. **Grafana Dashboard**: http://localhost:3000
2. **Prometheus Metrics**: http://localhost:9090
3. **API Logs**: `docker-compose logs -f api`

### Performance Baselines

| Load Level | Users | Req/s | p95 Latency | Error Rate |
|------------|-------|-------|-------------|------------|
| Light | 10 | 15-20 | < 200ms | < 0.1% |
| Medium | 50 | 60-80 | < 300ms | < 0.5% |
| Heavy | 200 | 150-200 | < 500ms | < 1% |

---

## Performance Metrics

### Key Metrics to Monitor

#### API Performance
```promql
# Request rate
rate(http_requests_total[5m])

# Error rate
rate(http_requests_total{status_code=~"5.."}[5m]) /
rate(http_requests_total[5m])

# p95 latency
histogram_quantile(0.95,
  rate(http_request_duration_seconds_bucket[5m])
)
```

#### Database Performance
```promql
# Query duration p95
histogram_quantile(0.95,
  rate(db_query_duration_seconds_bucket[5m])
)

# Connection pool usage
db_connection_pool_size /
(db_connection_pool_size + db_connection_pool_overflow)
```

#### Cache Performance
```promql
# Cache hit rate
rate(cache_hits_total[5m]) /
(rate(cache_hits_total[5m]) + rate(cache_misses_total[5m]))
```

### Alerts

Performance alerts configured in Prometheus:
- High latency (p95 > 2s)
- High error rate (> 5%)
- Low cache hit rate (< 60%)
- Database pool exhaustion

---

## Best Practices

### 1. Always Use Pagination

```python
# Limit results
@router.get("/agents")
async def list_agents(
    offset: int = 0,
    limit: int = 100,
):
    return await get_agents(offset=offset, limit=min(limit, 100))
```

### 2. Cache Frequently Accessed Data

```python
# Check cache first
cached = await cache.get(key)
if cached:
    return cached

# Fetch from DB
data = await fetch_from_db()

# Cache result
await cache.set(key, data, ttl=300)
```

### 3. Use Batch Operations

```python
# Batch instead of loop
await batch_insert(db, items)

# Not this:
for item in items:
    db.add(item)
    await db.commit()
```

### 4. Monitor Performance

- Set up Grafana alerts
- Review slow query logs
- Track cache hit rates
- Run regular load tests

### 5. Optimize Queries

- Use indexes
- Avoid N+1 queries
- Select only needed columns
- Use query explain plans

```bash
# Analyze query
docker-compose exec db psql -U postgres -d agentic_db -c \
  "EXPLAIN ANALYZE SELECT * FROM agents WHERE tenant_id = '...'"
```

---

## Troubleshooting

### Slow API Responses

**Symptoms:** p95 latency > 1s

**Check:**
1. Database query times
   ```promql
   histogram_quantile(0.95, rate(db_query_duration_seconds_bucket[5m]))
   ```
2. Missing indexes
   ```sql
   SELECT * FROM pg_stat_user_indexes WHERE idx_scan = 0;
   ```
3. Cache hit rate
   ```promql
   rate(cache_hits_total[5m]) / (rate(cache_hits_total[5m]) + rate(cache_misses_total[5m]))
   ```

**Fix:**
- Add missing indexes
- Increase cache TTL
- Optimize slow queries

### High Database CPU

**Symptoms:** DB CPU > 80%

**Check:**
1. Slow queries
   ```sql
   SELECT query, mean_exec_time, calls
   FROM pg_stat_statements
   ORDER BY mean_exec_time DESC
   LIMIT 10;
   ```
2. Missing indexes
3. Table statistics

**Fix:**
- Add indexes
- Optimize queries
- Run VACUUM ANALYZE

### Connection Pool Exhausted

**Symptoms:** "Too many connections" errors

**Check:**
```python
from src.db.session import get_pool_status
status = get_pool_status()
# Check overflow value
```

**Fix:**
1. Increase pool size
   ```python
   # In config
   DATABASE_POOL_SIZE = 30
   DATABASE_MAX_OVERFLOW = 20
   ```
2. Fix connection leaks
3. Reduce connection hold time

### Low Cache Hit Rate

**Symptoms:** Hit rate < 60%

**Check:**
```promql
rate(cache_hits_total[5m]) /
(rate(cache_hits_total[5m]) + rate(cache_misses_total[5m]))
```

**Fix:**
1. Increase TTL for stable data
2. Add caching to more endpoints
3. Pre-warm cache on startup
4. Review cache invalidation strategy

---

## Performance Checklist

Before deploying to production:

- [ ] Database indexes created
- [ ] Caching implemented for hot paths
- [ ] Rate limiting enabled
- [ ] Connection pooling optimized
- [ ] Batch processing used for bulk operations
- [ ] Load tests passed
- [ ] Performance metrics monitored
- [ ] Alerts configured
- [ ] Query optimization verified
- [ ] Cache hit rate > 80%

---

## Configuration Reference

### Environment Variables

```bash
# Database
DATABASE_POOL_SIZE=20
DATABASE_MAX_OVERFLOW=10

# Redis
REDIS_POOL_SIZE=10

# Rate Limiting
RATE_LIMIT_ENABLED=true
RATE_LIMIT_PER_MINUTE=60
RATE_LIMIT_PER_HOUR=1000

# Caching
CACHE_TTL_AGENTS=300
CACHE_TTL_WORKFLOWS=300
CACHE_TTL_EMBEDDINGS=3600
```

---

## Next Steps

1. **Establish Baselines**: Run load tests to establish performance baselines
2. **Monitor Continuously**: Set up Grafana dashboards and alerts
3. **Optimize Iteratively**: Use metrics to identify bottlenecks
4. **Test Regularly**: Run load tests before each release
5. **Document Changes**: Keep performance benchmarks updated

---

*Last Updated: 2025-01-15*
*Version: 1.0.0*
*Phase: 3 - Production Readiness*
