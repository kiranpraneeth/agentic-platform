# Sentry Error Tracking

This document describes the Sentry integration for error tracking and performance monitoring in the Agentic Platform.

## Overview

Sentry provides:
- **Error tracking** - Capture and track exceptions automatically
- **Performance monitoring** - Monitor API response times and database queries
- **Release tracking** - Track errors by deployment version
- **User context** - Associate errors with specific users/tenants
- **Breadcrumbs** - Capture events leading up to errors
- **Alerts** - Get notified of new errors and performance issues

## Setup

### 1. Create Sentry Project

1. Sign up at [sentry.io](https://sentry.io)
2. Create a new project
3. Select **Python** as the platform
4. Copy the **DSN** (Data Source Name)

### 2. Configure Environment

Add Sentry DSN to your environment:

```bash
# .env
SENTRY_DSN=https://examplePublicKey@o0.ingest.sentry.io/0
```

Or use environment variable:

```bash
export SENTRY_DSN=https://examplePublicKey@o0.ingest.sentry.io/0
```

### 3. Install Dependencies

```bash
poetry install
```

This installs `sentry-sdk` with FastAPI, SQLAlchemy, HTTPX, and Redis integrations.

## Configuration

### Automatic Initialization

Sentry is automatically configured when the application starts in `src/main.py`:

```python
from src.core.sentry_config import configure_sentry

configure_sentry()
```

### Environment-Based Behavior

- **Development:** Sentry disabled (no DSN configured)
- **Staging:** Sentry enabled with 100% sampling
- **Production:** Sentry enabled with 10% sampling

### Sample Rates

**Traces Sample Rate** (Performance Monitoring):
- Production: 10% of requests
- Staging: 100% of requests
- Development: Disabled

**Profiles Sample Rate** (Profiling):
- Production: 10% of requests
- Staging: 100% of requests
- Development: Disabled

Lower sample rates in production reduce performance overhead and costs.

## Features

### 1. Automatic Error Tracking

All unhandled exceptions are automatically captured and sent to Sentry:

```python
# This exception will automatically be captured
@app.get("/api/v1/example")
async def example():
    raise ValueError("Something went wrong")
```

### 2. Manual Error Capture

Capture exceptions manually with additional context:

```python
from src.core.sentry_config import capture_exception

try:
    result = process_data(data)
except Exception as e:
    capture_exception(
        e,
        user_id=user.id,
        tenant_id=tenant.id,
        action="process_data",
        data_size=len(data)
    )
    raise
```

### 3. Message Capture

Send custom messages to Sentry:

```python
from src.core.sentry_config import capture_message

capture_message(
    "Unusual activity detected",
    level="warning",
    user_id=user.id,
    activity_type="multiple_failed_logins"
)
```

### 4. User Context

Set user context to associate errors with specific users:

```python
from src.core.sentry_config import set_user_context

# In your authentication middleware
set_user_context(
    user_id=str(user.id),
    email=user.email,
    username=user.username,
    tenant_id=str(tenant.id)
)
```

User context is automatically included in all subsequent error reports.

### 5. Tags

Add tags to filter and group errors:

```python
from src.core.sentry_config import set_tag

set_tag("feature", "rag_search")
set_tag("model", "claude-3")
set_tag("tenant", tenant.slug)
```

### 6. Custom Context

Add structured context data:

```python
from src.core.sentry_config import set_context

set_context("agent_execution", {
    "agent_id": agent.id,
    "agent_type": agent.type,
    "execution_time": elapsed_time,
    "iterations": iteration_count
})
```

### 7. Performance Monitoring

Track custom transactions and spans:

```python
from src.core.sentry_config import start_transaction, start_span

# Track a custom transaction
with start_transaction(name="agent.execute", op="agent") as transaction:
    # Track individual operations within the transaction
    with start_span(op="llm.call", description="Claude API call"):
        response = await call_claude_api()

    with start_span(op="db.query", description="Load context"):
        context = await load_context()

    result = await execute_agent(response, context)
```

## Integrations

Sentry automatically instruments:

### FastAPI Integration
- Captures unhandled exceptions in routes
- Tracks request/response performance
- Associates errors with HTTP requests
- Filters out 4xx errors (client errors)

### SQLAlchemy Integration
- Tracks database query performance
- Captures database errors
- Shows slow queries in performance monitoring

### Redis Integration
- Tracks cache operations
- Captures Redis connection errors
- Shows cache hit/miss patterns

### HTTPX Integration
- Tracks external API calls
- Captures HTTP client errors
- Shows external service latency

### Asyncio Integration
- Captures errors in async tasks
- Tracks async operation performance

## Error Filtering

Sentry is configured to filter out noise:

### Ignored Errors
- `KeyboardInterrupt` - User interruption
- `SystemExit` - Normal shutdown
- `httpx.HTTPStatusError` - HTTP client errors (expected in many cases)

### Ignored Requests
- Health check endpoints (`/health/*`)
- 404 Not Found errors (logged but not sent to Sentry)

### Data Scrubbing

Sensitive data is automatically scrubbed from error reports:

**Headers:**
- `Authorization: [Filtered]`
- `Cookie: [Filtered]`
- `X-API-Key: [Filtered]`

**Request Body:**
- `password: [Filtered]`
- `api_key: [Filtered]`
- `secret: [Filtered]`
- `token: [Filtered]`

This protects user credentials and API keys from appearing in Sentry.

## Release Tracking

Errors are automatically associated with the application version:

```python
release=f"agentic-platform@{settings.VERSION}"
```

**In Sentry Dashboard:**
1. View errors by release
2. Compare error rates between releases
3. Automatically create release notes
4. Track regressions

**Create a release:**
```bash
# Tag and deploy
git tag v1.2.3
git push origin v1.2.3

# Sentry will automatically associate errors with v1.2.3
```

## Monitoring

### Sentry Dashboard

**Errors:**
1. Navigate to **Issues**
2. Filter by environment (production/staging)
3. Sort by frequency or recency
4. View stack traces and breadcrumbs
5. Mark as resolved or assign to team members

**Performance:**
1. Navigate to **Performance**
2. View transaction list (API endpoints)
3. Click transaction to see:
   - Average response time
   - P95/P99 latency
   - Throughput
   - Slow queries
   - External API calls

### Alerts

Configure alerts in Sentry dashboard:

**Error Alerts:**
```yaml
Alert Name: New Production Errors
Conditions:
  - First time seen in production
  - Error rate > 10 per minute
Actions:
  - Send Slack notification
  - Email on-call engineer
```

**Performance Alerts:**
```yaml
Alert Name: Slow API Response
Conditions:
  - P95 latency > 5 seconds
  - Sustained for 10 minutes
Actions:
  - Send Slack notification
  - Create PagerDuty incident
```

### Metrics

Track these key metrics in Sentry:

- **Error Rate** - Errors per minute
- **Crash-Free Sessions** - % of requests without errors
- **APDEX Score** - Application performance score
- **P95 Latency** - 95th percentile response time
- **Throughput** - Requests per second

## Best Practices

### 1. Use Structured Context

```python
# Good - Structured context
capture_exception(e, user_id=user.id, tenant_id=tenant.id, action="create_agent")

# Bad - Unstructured message
capture_message(f"Error for user {user.id} in tenant {tenant.id}")
```

### 2. Set Appropriate Levels

```python
# Critical errors - Use capture_exception
capture_exception(DatabaseConnectionError())

# Warnings - Use capture_message with level
capture_message("Cache miss for popular query", level="warning")

# Info - Use logging instead
logger.info("Agent execution started")
```

### 3. Add Business Context

```python
# Add context relevant to your business
set_context("subscription", {
    "plan": tenant.subscription_plan,
    "usage": tenant.monthly_usage,
    "limit": tenant.usage_limit
})
```

### 4. Tag for Filtering

```python
# Use tags to filter and group errors
set_tag("tenant", tenant.slug)
set_tag("feature", "workflow_execution")
set_tag("model_provider", "anthropic")
```

### 5. Don't Over-Sample in Production

```python
# Keep sample rates low in production to control costs
traces_sample_rate = 0.1  # 10% of requests
profiles_sample_rate = 0.1  # 10% of requests
```

### 6. Use Releases

```python
# Always deploy with version tags
git tag v1.2.3
git push origin v1.2.3

# Sentry will track errors by release
```

## Troubleshooting

### Sentry Not Capturing Errors

**Check DSN is configured:**
```bash
echo $SENTRY_DSN
```

**Check environment:**
```python
# Sentry only enabled in production/staging
if settings.ENVIRONMENT in ["production", "staging"]:
    # Sentry is active
```

**Check logs:**
```bash
docker-compose logs api | grep sentry
# Should see: sentry_initialized environment=production
```

### Too Many Events (Over Quota)

**Reduce sample rates:**
```python
# In src/core/sentry_config.py
traces_sample_rate = 0.05  # 5% instead of 10%
```

**Add more filters:**
```python
def before_send_hook(event, hint):
    # Filter out specific errors
    if "Expected error" in str(hint.get("exc_info")):
        return None
    return event
```

**Increase quota:** Upgrade Sentry plan

### Missing Context

**Ensure middleware is configured:**
```python
# User context should be set in authentication middleware
set_user_context(user_id=user.id, email=user.email)
```

**Check scope:**
```python
# Context is scoped - set it before the error occurs
with sentry_sdk.push_scope() as scope:
    scope.set_context("custom", data)
    # Error captured here will include context
    raise Exception("Error")
```

### Performance Overhead

**Reduce sampling:**
```python
traces_sample_rate = 0.05  # Lower sample rate
```

**Disable profiling:**
```python
profiles_sample_rate = 0  # Disable profiling
```

**Filter transactions:**
```python
def traces_sampler(sampling_context):
    # Don't sample health checks
    if "/health" in sampling_context.get("transaction", ""):
        return 0
    return 0.1
```

## Cost Management

### Pricing Factors

1. **Events** - Number of errors captured
2. **Transactions** - Number of performance traces
3. **Replay Sessions** - Session recordings (not configured)
4. **Attachments** - File uploads (not configured)

### Optimization Tips

**1. Sample strategically:**
```python
# Sample critical endpoints at 100%
# Sample others at 10%
def traces_sampler(sampling_context):
    if "/api/v1/agents/execute" in sampling_context.get("transaction", ""):
        return 1.0  # 100% for critical endpoint
    return 0.1  # 10% for others
```

**2. Use inbound filters:**

In Sentry dashboard → Settings → Inbound Filters:
- Filter legacy browsers
- Filter localhost errors
- Filter known web crawlers

**3. Set rate limits:**

In Sentry dashboard → Settings → Rate Limits:
- Max events per key: 1000/hour
- Max events per project: 10000/hour

**4. Archive old issues:**

Regularly archive resolved issues to reduce storage costs.

## Integration with Observability Stack

Sentry complements the observability stack:

- **Sentry** - Error tracking and alerting
- **Prometheus** - Metrics and system monitoring
- **Jaeger** - Distributed tracing
- **Grafana** - Visualization and dashboards

**Use Sentry for:**
- Production error alerting
- User-facing error tracking
- Release-specific error analysis
- Performance regression detection

**Use Prometheus/Jaeger for:**
- System-level metrics
- Detailed trace analysis
- Custom metrics tracking
- Real-time monitoring

## Security Considerations

1. **DSN Security**
   - Treat DSN as sensitive (allows sending events)
   - Don't commit DSN to repository
   - Use environment variables or secrets

2. **Data Privacy**
   - PII scrubbing is enabled (`send_default_pii=False`)
   - Sensitive fields are filtered automatically
   - Review events for unintended data leaks

3. **Access Control**
   - Limit team member access in Sentry dashboard
   - Use SSO for authentication
   - Enable 2FA for all team members

4. **Compliance**
   - Review data residency options (US/EU)
   - Configure data retention policies
   - Ensure GDPR/CCPA compliance

## Resources

- [Sentry Documentation](https://docs.sentry.io)
- [Sentry Python SDK](https://docs.sentry.io/platforms/python/)
- [FastAPI Integration](https://docs.sentry.io/platforms/python/guides/fastapi/)
- [Performance Monitoring](https://docs.sentry.io/product/performance/)
- [Release Tracking](https://docs.sentry.io/product/releases/)
