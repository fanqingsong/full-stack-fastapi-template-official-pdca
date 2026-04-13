"""
Prometheus metrics definitions and registry.

This module defines all Prometheus metrics used across the application,
including HTTP requests, PDCA business metrics, AI agent calls, and infrastructure metrics.
"""
import logging
from prometheus_client import Counter, Gauge, Histogram
# In prometheus_client >= 0.25.0, Registry is renamed to REGISTRY
try:
    from prometheus_client import REGISTRY
except ImportError:
    from prometheus_client import Registry
    REGISTRY = Registry()
from prometheus_client.exposition import generate_latest

logger = logging.getLogger(__name__)

# Use the default REGISTRY instance
# Note: REGISTRY is a pre-instantiated CollectorRegistry, not callable
registry = REGISTRY

# ==============================================================================
# HTTP Request Metrics
# ==============================================================================

http_requests_total = Counter(
    'http_requests_total',
    'Total HTTP requests',
    ['method', 'path', 'status'],
    registry=registry
)

http_request_duration_seconds = Histogram(
    'http_request_duration_seconds',
    'HTTP request duration in seconds',
    ['method', 'path', 'status'],
    registry=registry,
    buckets=(0.005, 0.01, 0.025, 0.05, 0.075, 0.1, 0.25, 0.5, 0.75, 1.0, 2.5, 5.0, 7.5, 10.0)
)

http_requests_active = Gauge(
    'http_requests_active',
    'Number of active HTTP requests',
    ['path'],
    registry=registry
)

# ==============================================================================
# PDCA Business Metrics
# ==============================================================================

pdca_cycles_created_total = Counter(
    'pdca_cycles_created_total',
    'Total PDCA cycles created',
    ['user_id', 'department'],
    registry=registry
)

pdca_cycles_by_status = Gauge(
    'pdca_cycles_by_status',
    'PDCA cycles by status',
    ['status', 'department'],
    registry=registry
)

pdca_stage_duration_seconds = Histogram(
    'pdca_stage_duration_seconds',
    'PDCA stage duration in seconds',
    ['stage'],
    registry=registry,
    buckets=(60, 300, 600, 1800, 3600, 7200, 14400, 28800, 43200, 86400)
)

# ==============================================================================
# AI Agent Metrics
# ==============================================================================

ai_requests_total = Counter(
    'ai_requests_total',
    'Total AI agent requests',
    ['provider', 'model', 'status'],
    registry=registry
)

ai_request_duration_seconds = Histogram(
    'ai_request_duration_seconds',
    'AI request duration in seconds',
    ['provider', 'model'],
    registry=registry,
    buckets=(0.5, 1.0, 2.0, 5.0, 10.0, 20.0, 30.0, 60.0, 120.0)
)

ai_tokens_used_total = Counter(
    'ai_tokens_used_total',
    'Total AI tokens used',
    ['provider', 'model', 'type'],  # type: prompt/completion
    registry=registry
)

ai_cost_usd_total = Counter(
    'ai_cost_usd_total',
    'Total AI cost in USD',
    ['provider', 'model'],
    registry=registry
)

# ==============================================================================
# Infrastructure Metrics
# ==============================================================================

db_connections_active = Gauge(
    'db_connections_active',
    'Active database connections',
    ['state'],  # state: checked_out/active/idle
    registry=registry
)

db_query_duration_seconds = Histogram(
    'db_query_duration_seconds',
    'Database query duration in seconds',
    ['operation', 'table'],
    registry=registry,
    buckets=(0.001, 0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0)
)


def safe_record_metric(metric_func):
    """
    Decorator to ensure metric recording failures don't affect business logic.

    Args:
        metric_func: The metric recording function to wrap

    Returns:
        Wrapped function that logs errors instead of raising them
    """
    def wrapper(*args, **kwargs):
        try:
            return metric_func(*args, **kwargs)
        except Exception as e:
            logger.warning(f"Failed to record metric: {e}")
    return wrapper


def generate_metrics() -> bytes:
    """
    Generate Prometheus metrics exposition format.

    Returns:
        Metrics in Prometheus text format
    """
    return generate_latest(registry)
