"""Test metrics initialization and basic functionality."""
from app.core.metrics import (
    http_requests_total,
    http_request_duration_seconds,
    pdca_cycles_created_total,
    ai_requests_total,
    generate_metrics,
)


def test_metrics_registry_exists():
    """Test that metrics are properly registered."""
    # Check that metrics have the right name and type
    assert http_requests_total._name == 'http_requests_total'
    assert pdca_cycles_created_total._name == 'pdca_cycles_created_total'
    assert ai_requests_total._name == 'ai_requests_total'


def test_metrics_can_be_incremented():
    """Test that counters can be incremented."""
    initial_value = http_requests_total.labels(
        method='GET',
        path='/api/v1/test',
        status='200'
    )._value.get()

    http_requests_total.labels(
        method='GET',
        path='/api/v1/test',
        status='200'
    ).inc()

    final_value = http_requests_total.labels(
        method='GET',
        path='/api/v1/test',
        status='200'
    )._value.get()

    assert final_value == initial_value + 1


def test_metrics_can_be_observed():
    """Test that histograms can observe values."""
    http_request_duration_seconds.labels(
        method='GET',
        path='/api/v1/test',
        status='200'
    ).observe(0.123)

    # Should not raise any errors
    assert True


def test_generate_metrics_returns_bytes():
    """Test that generate_metrics returns bytes."""
    metrics = generate_metrics()
    assert isinstance(metrics, bytes)
    assert b'http_requests_total' in metrics
