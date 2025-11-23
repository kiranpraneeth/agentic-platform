# Load Testing

Load tests for the Agentic Platform using Locust.

## Quick Start

```bash
# 1. Install Locust
pip install locust

# 2. Start the API
docker-compose up -d

# 3. Seed test data
docker-compose exec api python scripts/seed_dev_data.py

# 4. Run load tests
cd load_tests
locust

# 5. Open web UI
open http://localhost:8089
```

## Test Scenarios

### 1. Basic Load Test (`locustfile.py`)

Simulates mixed read/write operations:
- 10: List agents
- 5: Get specific agent
- 3: Create agent
- 8: List workflows
- 5: List collections
- 2: List MCP servers
- 1: Health checks

**Usage:**
```bash
locust -f locustfile.py --host=http://localhost:8000
```

### 2. Read-Only Test

Simulates read-heavy workload:
- 20: List agents
- 10: List workflows
- 5: List collections

**Usage:**
```bash
locust -f locustfile.py --users 50 --spawn-rate 5 --run-time 5m ReadOnlyUser
```

## Running Tests

### Web UI Mode (Interactive)

```bash
# Start web UI
locust -f locustfile.py

# Open browser
open http://localhost:8089

# Configure:
# - Number of users: 50
# - Spawn rate: 5 users/second
# - Host: http://localhost:8000
```

### Headless Mode (CLI)

```bash
# Run for 5 minutes with 50 users
locust -f locustfile.py \
  --headless \
  --users 50 \
  --spawn-rate 5 \
  --run-time 5m \
  --host http://localhost:8000

# Generate HTML report
locust -f locustfile.py \
  --headless \
  --users 100 \
  --spawn-rate 10 \
  --run-time 10m \
  --html report.html \
  --host http://localhost:8000
```

### Distributed Load Testing

```bash
# Master node
locust -f locustfile.py --master

# Worker nodes (run on multiple machines)
locust -f locustfile.py --worker --master-host=<master-ip>
```

## Test Profiles

### Light Load (Development)
```bash
locust -f locustfile.py \
  --headless \
  --users 10 \
  --spawn-rate 1 \
  --run-time 2m
```

### Medium Load (Staging)
```bash
locust -f locustfile.py \
  --headless \
  --users 50 \
  --spawn-rate 5 \
  --run-time 10m
```

### Heavy Load (Production Simulation)
```bash
locust -f locustfile.py \
  --headless \
  --users 200 \
  --spawn-rate 10 \
  --run-time 30m
```

### Spike Test (Sudden Traffic)
```bash
locust -f locustfile.py \
  --headless \
  --users 500 \
  --spawn-rate 50 \
  --run-time 5m
```

## Metrics to Monitor

### While Running Tests

Watch these metrics in real-time:

```bash
# Prometheus metrics
open http://localhost:9090

# Grafana dashboard
open http://localhost:3000

# API logs
docker-compose logs -f api
```

### Key Metrics

| Metric | Target | Alert Threshold |
|--------|--------|-----------------|
| **Response Time (p95)** | < 500ms | > 2s |
| **Error Rate** | < 1% | > 5% |
| **Requests/sec** | > 100 | - |
| **DB Connection Pool** | < 80% | > 90% |
| **Memory Usage** | < 1GB | > 2GB |
| **CPU Usage** | < 70% | > 90% |

## Interpreting Results

### Good Performance
```
Response times (p50): 100ms
Response times (p95): 300ms
Error rate: 0.1%
Requests/sec: 150
```

### Performance Issues
```
Response times (p50): 1000ms
Response times (p95): 5000ms
Error rate: 5%
Requests/sec: 20
```

### Common Bottlenecks

1. **High latency**
   - Check: Database query times
   - Check: Missing indexes
   - Check: Cache hit rate

2. **High error rate**
   - Check: Application logs
   - Check: Database connection pool
   - Check: Rate limiting

3. **Low throughput**
   - Check: CPU usage
   - Check: Memory usage
   - Check: Network I/O

## Test Data Setup

Before running load tests, ensure you have test data:

```bash
# Create test user
docker-compose exec api python -c "
from src.db.session import AsyncSessionLocal
from src.db.models import User, Tenant
from src.core.security import get_password_hash
import asyncio

async def create_test_user():
    async with AsyncSessionLocal() as session:
        # Create or get test tenant
        tenant = Tenant(name='Test Tenant', slug='test-tenant', settings={})
        session.add(tenant)
        await session.flush()

        # Create test user
        user = User(
            tenant_id=tenant.id,
            email='test@example.com',
            username='testuser',
            hashed_password=get_password_hash('testpass123'),
            full_name='Test User',
            is_active=True,
        )
        session.add(user)
        await session.commit()
        print(f'Created test user: {user.email}')

asyncio.run(create_test_user())
"

# Seed additional data
docker-compose exec api python scripts/seed_dev_data.py
```

## Troubleshooting

### Connection Refused
```bash
# Ensure API is running
docker-compose ps api

# Check if port 8000 is accessible
curl http://localhost:8000/health
```

### Authentication Errors
```bash
# Verify test user exists
docker-compose exec db psql -U postgres -d agentic_db \
  -c "SELECT email FROM users WHERE email='test@example.com';"

# Reset password if needed
# (run the test user creation script above)
```

### Rate Limiting
```bash
# Disable rate limiting for load tests
# Edit .env:
RATE_LIMIT_ENABLED=false

# Restart API
docker-compose restart api
```

## Best Practices

1. **Start Small**: Begin with 10 users, gradually increase
2. **Monitor Metrics**: Watch Grafana dashboards during tests
3. **Test Realistic Scenarios**: Mix read/write operations
4. **Run Multiple Times**: Ensure consistent results
5. **Clean Up**: Remove test data after load tests
6. **Document Results**: Keep records of performance baselines

## Example Test Run

```bash
$ locust -f locustfile.py --headless --users 100 --spawn-rate 10 --run-time 5m

[2025-01-15 10:00:00,000] Starting load test
[2025-01-15 10:00:00,500] Spawning 10 users...
[2025-01-15 10:00:01,000] Spawning 10 users...
...
[2025-01-15 10:05:00,000] Stopping load test

Name                          # reqs  # fails  Avg    Min    Max    Med    req/s  failures/s
------------------------------------------------------------------------------------------
GET /api/v1/agents            5000    0        145    45     850    120    16.7   0.00
GET /api/v1/workflows         4000    0        132    40     720    110    13.3   0.00
POST /api/v1/agents           1500    5        245    100    1200   200    5.0    0.02
GET /health                   500     0        12     5      45     10     1.7    0.00
------------------------------------------------------------------------------------------
Aggregated                    11000   5        156    5      1200   130    36.7   0.02

Response time percentiles (approximated):
Type        Name                          50%    66%    75%    80%    90%    95%    98%    99%  99.9% 99.99%
--------    ----------------------------- ------ ------ ------ ------ ------ ------ ------ ------ ------ ------
GET         /api/v1/agents                120    140    160    180    220    280    400    550    850    850
GET         /api/v1/workflows             110    130    150    170    210    270    380    520    720    720
POST        /api/v1/agents                200    230    260    290    380    500    750    950    1200   1200
```

## Next Steps

1. Set performance baselines
2. Run load tests before each release
3. Add custom test scenarios
4. Integrate with CI/CD
5. Set up automated performance regression tests
