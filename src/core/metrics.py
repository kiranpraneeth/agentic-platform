"""Prometheus metrics for application observability."""

from prometheus_client import Counter, Gauge, Histogram, Info
from prometheus_client import generate_latest, CONTENT_TYPE_LATEST

from src.core.config import settings

# Application info
app_info = Info("agentic_platform", "Application information")
app_info.info(
    {
        "version": settings.VERSION,
        "environment": settings.ENVIRONMENT,
        "project": settings.PROJECT_NAME,
    }
)

# HTTP request metrics
http_requests_total = Counter(
    "http_requests_total",
    "Total HTTP requests",
    ["method", "endpoint", "status_code"],
)

http_request_duration_seconds = Histogram(
    "http_request_duration_seconds",
    "HTTP request latency in seconds",
    ["method", "endpoint"],
    buckets=(0.01, 0.05, 0.1, 0.5, 1.0, 2.5, 5.0, 10.0),
)

http_requests_in_progress = Gauge(
    "http_requests_in_progress",
    "Number of HTTP requests in progress",
    ["method", "endpoint"],
)

# Agent execution metrics
agent_executions_total = Counter(
    "agent_executions_total",
    "Total agent executions",
    ["agent_id", "status"],
)

agent_execution_duration_seconds = Histogram(
    "agent_execution_duration_seconds",
    "Agent execution duration in seconds",
    ["agent_id"],
    buckets=(1.0, 5.0, 10.0, 30.0, 60.0, 120.0, 300.0),
)

agent_token_usage_total = Counter(
    "agent_token_usage_total",
    "Total tokens used by agents",
    ["agent_id", "model", "token_type"],
)

# Workflow metrics
workflow_executions_total = Counter(
    "workflow_executions_total",
    "Total workflow executions",
    ["workflow_id", "status"],
)

workflow_execution_duration_seconds = Histogram(
    "workflow_execution_duration_seconds",
    "Workflow execution duration in seconds",
    ["workflow_id"],
    buckets=(1.0, 10.0, 30.0, 60.0, 300.0, 600.0, 1800.0),
)

workflow_step_duration_seconds = Histogram(
    "workflow_step_duration_seconds",
    "Workflow step execution duration in seconds",
    ["workflow_id", "step_type"],
    buckets=(0.1, 0.5, 1.0, 5.0, 10.0, 30.0, 60.0),
)

# Database metrics
db_connection_pool_size = Gauge(
    "db_connection_pool_size",
    "Current database connection pool size",
)

db_connection_pool_overflow = Gauge(
    "db_connection_pool_overflow",
    "Current database connection pool overflow",
)

db_query_duration_seconds = Histogram(
    "db_query_duration_seconds",
    "Database query duration in seconds",
    ["query_type"],
    buckets=(0.001, 0.005, 0.01, 0.05, 0.1, 0.5, 1.0),
)

# MCP server metrics
mcp_tool_calls_total = Counter(
    "mcp_tool_calls_total",
    "Total MCP tool calls",
    ["server_name", "tool_name", "status"],
)

mcp_tool_call_duration_seconds = Histogram(
    "mcp_tool_call_duration_seconds",
    "MCP tool call duration in seconds",
    ["server_name", "tool_name"],
    buckets=(0.01, 0.05, 0.1, 0.5, 1.0, 5.0, 10.0),
)

# RAG metrics
rag_document_processing_total = Counter(
    "rag_document_processing_total",
    "Total documents processed for RAG",
    ["collection_id", "status"],
)

rag_search_queries_total = Counter(
    "rag_search_queries_total",
    "Total RAG search queries",
    ["collection_id"],
)

rag_search_duration_seconds = Histogram(
    "rag_search_duration_seconds",
    "RAG search duration in seconds",
    ["collection_id"],
    buckets=(0.01, 0.05, 0.1, 0.5, 1.0, 2.0, 5.0),
)

rag_embedding_generation_duration_seconds = Histogram(
    "rag_embedding_generation_duration_seconds",
    "Embedding generation duration in seconds",
    buckets=(0.1, 0.5, 1.0, 2.0, 5.0, 10.0),
)

# Cache metrics
cache_hits_total = Counter(
    "cache_hits_total",
    "Total cache hits",
    ["cache_type"],
)

cache_misses_total = Counter(
    "cache_misses_total",
    "Total cache misses",
    ["cache_type"],
)

# Error metrics
errors_total = Counter(
    "errors_total",
    "Total errors",
    ["error_type", "component"],
)

# System metrics
active_users = Gauge(
    "active_users",
    "Number of active users",
)

active_tenants = Gauge(
    "active_tenants",
    "Number of active tenants",
)


def get_metrics() -> bytes:
    """Get current metrics in Prometheus format.

    Returns:
        Metrics data in Prometheus exposition format
    """
    return generate_latest()


def get_metrics_content_type() -> str:
    """Get the content type for metrics endpoint.

    Returns:
        Content type string
    """
    return CONTENT_TYPE_LATEST
