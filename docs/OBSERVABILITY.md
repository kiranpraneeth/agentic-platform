# Observability Guide

> **Comprehensive observability stack for the Agentic Platform**
>
> **Version**: 1.0.0
> **Phase**: 3 - Production Readiness

---

## Table of Contents

1. [Overview](#overview)
2. [Architecture](#architecture)
3. [Components](#components)
4. [Getting Started](#getting-started)
5. [Logging](#logging)
6. [Metrics](#metrics)
7. [Tracing](#tracing)
8. [Dashboards](#dashboards)
9. [Alerting](#alerting)
10. [Best Practices](#best-practices)
11. [Troubleshooting](#troubleshooting)

---

## Overview

The Agentic Platform implements a comprehensive observability stack with three pillars:

- **Logs**: Structured logging with correlation IDs for request tracking
- **Metrics**: Prometheus metrics for performance and health monitoring
- **Traces**: OpenTelemetry distributed tracing for request flow visualization

### Observability Stack

| Component | Purpose | URL |
|-----------|---------|-----|
| **Prometheus** | Metrics collection & storage | http://localhost:9090 |
| **Grafana** | Visualization & dashboards | http://localhost:3000 |
| **Jaeger** | Distributed tracing UI | http://localhost:16686 |
| **AlertManager** | Alert routing & notification | http://localhost:9093 |

---

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     Agentic Platform API                     │
│                                                               │
│  ┌───────────────┐  ┌───────────────┐  ┌──────────────────┐ │
│  │   Structured  │  │   Prometheus  │  │   OpenTelemetry  │ │
│  │    Logging    │  │    Metrics    │  │      Traces      │ │
│  └───────┬───────┘  └───────┬───────┘  └────────┬─────────┘ │
│          │                  │                     │           │
└──────────┼──────────────────┼─────────────────────┼───────────┘
           │                  │                     │
           ▼                  ▼                     ▼
    ┌────────────┐     ┌────────────┐      ┌──────────────┐
    │   Stdout   │     │ Prometheus │      │    Jaeger    │
    │   Logs     │     │   Server   │      │   Collector  │
    └────────────┘     └──────┬─────┘      └──────────────┘
                              │
                              ▼
                       ┌─────────────┐
                       │   Grafana   │
                       │  Dashboards │
                       └─────────────┘
                              │
                              ▼
                       ┌─────────────┐
                       │ AlertManager│
                       └─────────────┘
```

---

## Components

### 1. Structured Logging

**Location**: `src/core/logging.py`

Features:
- JSON-formatted logs in production
- Human-readable logs in development
- Correlation IDs for request tracking
- Automatic context enrichment (service, environment)
- Log level configuration via `LOG_LEVEL` env var

**Example Usage**:

```python
from src.core.logging import get_logger

logger = get_logger(__name__)

logger.info("user_login", user_id="123", email="user@example.com")
logger.error("payment_failed", amount=99.99, error="Insufficient funds")
```

**Log Output (Production)**:

```json
{
  "timestamp": "2024-01-15T10:30:45.123Z",
  "level": "INFO",
  "logger": "src.api.v1.auth",
  "message": "user_login",
  "correlation_id": "abc123-def456",
  "service": "agentic-platform",
  "environment": "production",
  "user_id": "123",
  "email": "user@example.com"
}
```

### 2. Correlation IDs

Every HTTP request gets a unique correlation ID that flows through:
- All log messages
- HTTP response headers (`X-Correlation-ID`)
- Distributed traces

**Headers**:
- **Request**: `X-Correlation-ID` (optional - generated if not provided)
- **Response**: `X-Correlation-ID`, `X-Response-Time`

### 3. Prometheus Metrics

**Location**: `src/core/metrics.py`

**Available Metrics**:

#### HTTP Metrics
- `http_requests_total` - Total HTTP requests (by method, endpoint, status)
- `http_request_duration_seconds` - Request latency histogram
- `http_requests_in_progress` - Current in-flight requests

#### Agent Metrics
- `agent_executions_total` - Total agent executions (by agent_id, status)
- `agent_execution_duration_seconds` - Agent execution time histogram
- `agent_token_usage_total` - LLM token usage (by agent, model, type)

#### Workflow Metrics
- `workflow_executions_total` - Total workflow executions
- `workflow_execution_duration_seconds` - Workflow execution time
- `workflow_step_duration_seconds` - Individual step execution time

#### MCP Server Metrics
- `mcp_tool_calls_total` - Total MCP tool calls
- `mcp_tool_call_duration_seconds` - Tool call latency

#### RAG Metrics
- `rag_document_processing_total` - Documents processed
- `rag_search_queries_total` - Search query count
- `rag_search_duration_seconds` - Search latency
- `rag_embedding_generation_duration_seconds` - Embedding generation time

#### Database Metrics
- `db_connection_pool_size` - Current pool size
- `db_connection_pool_overflow` - Pool overflow count
- `db_query_duration_seconds` - Query execution time

#### Cache Metrics
- `cache_hits_total` - Cache hits (by type)
- `cache_misses_total` - Cache misses (by type)

**Example Usage**:

```python
from src.core.metrics import agent_executions_total, agent_execution_duration_seconds

# Record agent execution
with agent_execution_duration_seconds.labels(agent_id=agent.id).time():
    result = await execute_agent(agent)

agent_executions_total.labels(
    agent_id=agent.id,
    status="success"
).inc()
```

### 4. OpenTelemetry Tracing

**Location**: `src/core/tracing.py`

Automatically instruments:
- FastAPI endpoints
- HTTP client requests (httpx)
- Database queries (SQLAlchemy)

**Manual Tracing**:

```python
from src.core.tracing import get_tracer

tracer = get_tracer(__name__)

with tracer.start_as_current_span("process_document") as span:
    span.set_attribute("document.id", doc_id)
    span.set_attribute("document.size", len(content))

    # Your code here
    result = process_document(content)

    span.set_attribute("chunks.count", len(result))
```

---

## Getting Started

### 1. Start Observability Stack

```bash
# Start the observability services
docker-compose -f docker-compose.observability.yml up -d

# Verify services are running
docker-compose -f docker-compose.observability.yml ps
```

### 2. Access Dashboards

- **Grafana**: http://localhost:3000 (admin/admin)
- **Prometheus**: http://localhost:9090
- **Jaeger**: http://localhost:16686
- **AlertManager**: http://localhost:9093

### 3. Configure Environment

Add to `.env`:

```bash
# Logging
LOG_LEVEL=INFO
ENVIRONMENT=production

# Tracing (optional - for external OTLP collector)
OTEL_EXPORTER_OTLP_ENDPOINT=http://jaeger:4317
```

### 4. View Metrics

```bash
# Check metrics endpoint
curl http://localhost:8000/metrics

# Check health endpoints
curl http://localhost:8000/health
curl http://localhost:8000/health/ready
curl http://localhost:8000/health/live
```

---

## Logging

### Log Levels

```bash
# Development
export LOG_LEVEL=DEBUG

# Production
export LOG_LEVEL=INFO
```

### Viewing Logs

```bash
# Follow API logs
docker-compose logs -f api

# Search logs with jq
docker-compose logs api | jq 'select(.correlation_id == "abc123")'

# Filter by log level
docker-compose logs api | jq 'select(.level == "ERROR")'
```

### Correlation ID Tracking

Track a request across all logs:

```bash
# Extract correlation ID from response
CORRELATION_ID=$(curl -v http://localhost:8000/api/v1/agents 2>&1 | grep -i x-correlation-id | awk '{print $3}')

# View all logs for that request
docker-compose logs api | jq "select(.correlation_id == \"$CORRELATION_ID\")"
```

---

## Metrics

### Metrics Endpoint

```bash
# View all metrics
curl http://localhost:8000/metrics

# Specific metric
curl http://localhost:8000/metrics | grep http_requests_total
```

### Prometheus Queries

Access Prometheus at http://localhost:9090 and try these queries:

#### Request Rate
```promql
rate(http_requests_total[5m])
```

#### Error Rate
```promql
rate(http_requests_total{status_code=~"5.."}[5m]) /
rate(http_requests_total[5m])
```

#### 95th Percentile Latency
```promql
histogram_quantile(0.95,
  rate(http_request_duration_seconds_bucket[5m])
)
```

#### Agent Success Rate
```promql
rate(agent_executions_total{status="success"}[10m]) /
rate(agent_executions_total[10m])
```

---

## Tracing

### View Traces

1. Open Jaeger UI: http://localhost:16686
2. Select service: `agentic-platform`
3. Click "Find Traces"

### Trace Search

- **By Operation**: Filter by endpoint (e.g., `GET /api/v1/agents`)
- **By Duration**: Find slow requests (Min Duration > 1s)
- **By Tags**: Search by `correlation_id`, `user_id`, etc.

### Trace Analysis

Each trace shows:
- Total request duration
- Individual span timings
- Database query times
- External API calls
- Errors and exceptions

---

## Dashboards

### Agentic Platform Overview

Access: http://localhost:3000/d/agentic-platform-overview

**Panels**:
1. HTTP Request Rate
2. HTTP Request Latency (p95)
3. Error Rate (%)
4. Requests In Progress
5. Agent Execution Rate
6. Agent Execution Duration
7. Workflow Execution Rate
8. MCP Tool Call Rate
9. RAG Search Rate & Latency
10. Database Connection Pool
11. Cache Hit/Miss Rate

### Custom Dashboards

Create custom dashboards in Grafana:
1. Login to Grafana (admin/admin)
2. Click "+" → "Dashboard"
3. Add panels with PromQL queries
4. Save to `/var/lib/grafana/dashboards` for persistence

---

## Alerting

### Alert Rules

**Location**: `observability/prometheus/alerts.yml`

**Active Alerts**:
- APIDown - API unavailable for 1 minute
- HighErrorRate - >5% error rate for 5 minutes
- HighRequestLatency - p95 > 2s for 5 minutes
- HighAgentFailureRate - >10% agent failures
- DatabaseConnectionPoolExhausted - Pool exhausted
- SlowDatabaseQueries - p95 > 1s

### Configure Notifications

Edit `observability/alertmanager/alertmanager.yml`:

**Slack Example**:

```yaml
receivers:
  - name: 'critical-alerts'
    slack_configs:
      - api_url: 'YOUR_SLACK_WEBHOOK_URL'
        channel: '#alerts'
        title: '[CRITICAL] {{ .GroupLabels.alertname }}'
        text: '{{ range .Alerts }}{{ .Annotations.description }}{{ end }}'
```

**Email Example**:

```yaml
receivers:
  - name: 'critical-alerts'
    email_configs:
      - to: 'oncall@example.com'
        from: 'alerts@example.com'
        smarthost: 'smtp.gmail.com:587'
        auth_username: 'alerts@example.com'
        auth_password: 'YOUR_APP_PASSWORD'
```

**PagerDuty Example**:

```yaml
receivers:
  - name: 'critical-alerts'
    pagerduty_configs:
      - service_key: 'YOUR_PAGERDUTY_SERVICE_KEY'
```

### Test Alerts

```bash
# Restart AlertManager after config changes
docker-compose -f docker-compose.observability.yml restart alertmanager

# View active alerts
curl http://localhost:9093/api/v2/alerts
```

---

## Best Practices

### Logging

✅ **DO**:
- Use structured logging with context fields
- Include correlation IDs in log messages
- Log at appropriate levels (DEBUG, INFO, WARNING, ERROR)
- Log errors with full stack traces

❌ **DON'T**:
- Log sensitive data (passwords, tokens, PII)
- Use string interpolation for log messages
- Log excessively in hot paths

### Metrics

✅ **DO**:
- Use histograms for latencies
- Use counters for totals
- Add meaningful labels
- Keep cardinality low (< 10 label values)

❌ **DON'T**:
- Use high-cardinality labels (user IDs, request IDs)
- Create metrics in request handlers (define globally)
- Over-instrument (measure what matters)

### Tracing

✅ **DO**:
- Add custom spans for important operations
- Set meaningful span attributes
- Record errors in spans
- Use semantic conventions

❌ **DON'T**:
- Trace every function call
- Add PII to span attributes
- Create overly granular spans

---

## Troubleshooting

### No Metrics in Prometheus

**Problem**: Prometheus shows no data for `agentic-api`

**Solution**:
```bash
# Check if API is exposing metrics
curl http://localhost:8000/metrics

# Check Prometheus targets
# Visit http://localhost:9090/targets
# Ensure agentic-api is UP

# Check Prometheus logs
docker-compose -f docker-compose.observability.yml logs prometheus
```

### Grafana Dashboard Empty

**Problem**: Dashboard shows "No data"

**Solution**:
```bash
# Verify Prometheus datasource
# Grafana → Configuration → Data Sources
# Test connection to Prometheus

# Check if metrics are being scraped
# Prometheus → Status → Targets
```

### No Traces in Jaeger

**Problem**: Jaeger UI shows no traces

**Solution**:
```bash
# Check OTLP endpoint configuration
echo $OTEL_EXPORTER_OTLP_ENDPOINT

# Should be: http://jaeger:4317

# Check Jaeger logs
docker-compose -f docker-compose.observability.yml logs jaeger

# Verify tracing is enabled in app
curl http://localhost:8000/health | jq .
```

### High Cardinality Warning

**Problem**: Prometheus warns about high cardinality

**Solution**:
- Review metric labels
- Remove high-cardinality labels (user_id, request_id)
- Use bucketing/aggregation for variable values

---

## Environment Variables

```bash
# Logging
LOG_LEVEL=INFO                    # DEBUG, INFO, WARNING, ERROR, CRITICAL
ENVIRONMENT=production            # development, staging, production

# Tracing
OTEL_EXPORTER_OTLP_ENDPOINT=http://jaeger:4317
OTEL_SERVICE_NAME=agentic-platform
```

---

## Architecture Decisions

### Why Structured Logging?

- **Searchability**: JSON logs are easily searchable and filterable
- **Consistency**: Standardized format across all services
- **Integration**: Works with log aggregation tools (ELK, Loki, CloudWatch)

### Why Prometheus?

- **Pull-based**: No need to configure endpoints in app
- **Powerful queries**: PromQL for complex metric analysis
- **Ecosystem**: Wide adoption, many integrations

### Why OpenTelemetry?

- **Vendor-neutral**: Not locked into specific tracing backend
- **Standards-based**: Industry standard for observability
- **Auto-instrumentation**: Minimal code changes required

---

## Performance Impact

Observability overhead:

| Component | CPU Impact | Memory Impact | Latency Impact |
|-----------|------------|---------------|----------------|
| Logging | < 1% | ~10MB | < 0.1ms/req |
| Metrics | < 1% | ~20MB | < 0.1ms/req |
| Tracing | 1-3% | ~30MB | < 1ms/req |
| **Total** | **< 5%** | **~60MB** | **< 2ms/req** |

*Impact varies based on request volume and complexity*

---

## Next Steps

1. **Configure Alerting**: Set up Slack/PagerDuty notifications
2. **Add Custom Dashboards**: Create team-specific views
3. **Log Aggregation**: Add Loki for centralized log storage
4. **SLO Monitoring**: Define and track Service Level Objectives
5. **Distributed Tracing**: Add custom spans for critical paths

---

*Last Updated: 2025-01-15*
*Version: 1.0.0*
*Phase: 3 - Production Readiness*
