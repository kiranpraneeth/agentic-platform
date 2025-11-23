# Performance Quick Start

Quick reference for performance optimizations in the Agentic Platform.

## Apply Optimizations

```bash
# 1. Run database migrations (add indexes)
docker-compose exec api alembic upgrade head

# 2. Restart API with optimizations
docker-compose restart api

# 3. Verify Redis is running
docker-compose ps redis

# 4. Test performance
curl http://localhost:8000/health/ready
```

## Key Features Enabled

✅ **Database Indexes** - 40+ indexes for faster queries
✅ **Redis Caching** - Cache for agents, workflows, embeddings
✅ **Rate Limiting** - 60/min, 1000/hour per client
✅ **Connection Pooling** - Optimized DB and Redis pools
✅ **Batch Processing** - Efficient bulk operations

## Quick Checks

### 1. Check Cache Hit Rate

```bash
# View metrics
curl http://localhost:8000/metrics | grep cache

# Expected: > 80% hit rate
```

### 2. Check Rate Limits

```bash
# Make request
curl -v http://localhost:8000/api/v1/agents

# Check headers:
# X-RateLimit-Limit: 60
# X-RateLimit-Remaining: 59
```

### 3. Check Connection Pool

```python
from src.db.session import get_pool_status
print(get_pool_status())

# Expected: overflow < 5
```

### 4. Run Load Test

```bash
cd load_tests
locust -f locustfile.py --headless --users 50 --spawn-rate 5 --run-time 5m

# Expected:
# - p95 latency < 500ms
# - Error rate < 1%
# - Req/s > 50
```

## Performance Targets

| Metric | Target | Command |
|--------|--------|---------|
| **API Response (p95)** | < 500ms | Load test |
| **Cache Hit Rate** | > 80% | `/metrics` |
| **Throughput** | > 100 req/s | Load test |
| **Error Rate** | < 1% | `/metrics` |

## Monitor Performance

```bash
# Grafana dashboards
open http://localhost:3000

# Prometheus metrics
open http://localhost:9090

# Live logs
docker-compose logs -f api
```

## Documentation

- **Full Guide**: [docs/PERFORMANCE.md](docs/PERFORMANCE.md)
- **Load Testing**: [load_tests/README.md](load_tests/README.md)
- **Observability**: [docs/OBSERVABILITY.md](docs/OBSERVABILITY.md)

## Troubleshooting

**Slow responses?**
→ Check database indexes: `\d+ agents` in psql

**Low cache hit rate?**
→ Increase TTL in `src/core/cache.py`

**Rate limit errors?**
→ Adjust limits in `src/main.py`

**Connection errors?**
→ Increase pool size in `.env`

---

See [docs/PERFORMANCE.md](docs/PERFORMANCE.md) for comprehensive documentation.
