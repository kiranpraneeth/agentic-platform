# Observability Stack

Quick reference for the Agentic Platform observability stack.

## Quick Start

```bash
# 1. Start observability services
docker-compose -f docker-compose.observability.yml up -d

# 2. Install dependencies
poetry install

# 3. Start the API
docker-compose up -d api

# 4. Access dashboards
open http://localhost:3000  # Grafana (admin/admin)
open http://localhost:9090  # Prometheus
open http://localhost:16686 # Jaeger
```

## Services

| Service | Port | URL | Credentials |
|---------|------|-----|-------------|
| Grafana | 3000 | http://localhost:3000 | admin/admin |
| Prometheus | 9090 | http://localhost:9090 | - |
| Jaeger | 16686 | http://localhost:16686 | - |
| AlertManager | 9093 | http://localhost:9093 | - |

## Endpoints

| Endpoint | Description |
|----------|-------------|
| `/metrics` | Prometheus metrics |
| `/health` | Basic health check |
| `/health/ready` | Readiness probe (DB check) |
| `/health/live` | Liveness probe |

## Configuration Files

```
observability/
├── prometheus/
│   ├── prometheus.yml         # Prometheus scrape config
│   └── alerts.yml             # Alert rules
├── grafana/
│   ├── provisioning/
│   │   ├── datasources/       # Datasource config
│   │   └── dashboards/        # Dashboard provisioning
│   └── dashboards/
│       └── agentic-platform-overview.json  # Main dashboard
└── alertmanager/
    └── alertmanager.yml       # Alert routing config
```

## Key Metrics

```promql
# Request rate
rate(http_requests_total[5m])

# Error rate
rate(http_requests_total{status_code=~"5.."}[5m]) / rate(http_requests_total[5m])

# Latency (p95)
histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m]))

# Agent execution rate
rate(agent_executions_total[5m])
```

## Documentation

See [OBSERVABILITY.md](../docs/OBSERVABILITY.md) for comprehensive documentation.

## Troubleshooting

```bash
# View logs
docker-compose -f docker-compose.observability.yml logs -f

# Restart services
docker-compose -f docker-compose.observability.yml restart

# Stop services
docker-compose -f docker-compose.observability.yml down

# Remove volumes
docker-compose -f docker-compose.observability.yml down -v
```
