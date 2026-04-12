"""End-to-end tests for monitoring system."""
import pytest
import time
from fastapi.testclient import TestClient
from app.core.metrics import (
    http_requests_total,
    pdca_cycles_created_total,
    ai_requests_total,
    generate_metrics,
)


def test_metrics_endpoint_returns_all_metrics(client: TestClient) -> None:
    """Test that /metrics endpoint returns all defined metrics."""
    response = client.get("/metrics")

    assert response.status_code == 200
    assert response.headers["content-type"] == "text/plain; charset=utf-8"

    content = response.content.decode('utf-8')

    # Check for HTTP metrics
    assert "http_requests_total" in content
    assert "http_request_duration_seconds" in content
    assert "http_requests_active" in content

    # Check for PDCA metrics
    assert "pdca_cycles_created_total" in content
    assert "pdca_cycles_by_status" in content
    assert "pdca_stage_duration_seconds" in content

    # Check for AI metrics
    assert "ai_requests_total" in content
    assert "ai_request_duration_seconds" in content
    assert "ai_tokens_used_total" in content
    assert "ai_cost_usd_total" in content

    # Check for infrastructure metrics
    assert "db_connections_active" in content


def test_http_request_metrics_incremented_on_api_call(client: TestClient) -> None:
    """Test that HTTP requests increment metrics."""
    # Make a test API call
    response = client.get("/api/v1/items/")
    initial_status = response.status_code

    # Get metric value before
    metric_before = http_requests_total.labels(
        method='GET',
        path='/api/v1/items/',
        status=str(initial_status)
    )._value.get()

    # Make another call
    response = client.get("/api/v1/items/")

    # Get metric value after
    metric_after = http_requests_total.labels(
        method='GET',
        path='/api/v1/items/',
        status=str(initial_status)
    )._value.get()

    # Metric should have incremented
    assert metric_after == metric_before + 1


def test_metrics_format_is_valid_prometheus(client: TestClient) -> None:
    """Test that metrics are in valid Prometheus format."""
    response = client.get("/metrics")
    content = response.content.decode('utf-8')

    # Check for HELP and TYPE comments (Prometheus format)
    assert "# HELP" in content
    assert "# TYPE" in content

    # Check metric name format (no invalid characters)
    lines = content.split('\n')
    for line in lines:
        if line and not line.startswith('#'):
            metric_name = line.split('{')[0].split(' ')[0]
            # Metric names should match [a-zA-Z_:][a-zA-Z0-9_:]*
            assert metric_name.replace('_', '').replace(':', '').isalnum()


def test_middleware_doesnt_break_normal_operations(client: TestClient) -> None:
    """Test that Prometheus middleware doesn't break normal API operations."""
    # Test various endpoints
    endpoints = [
        "/api/v1/items/",
        "/api/v1/users/me",
    ]

    for endpoint in endpoints:
        response = client.get(endpoint)
        # Should return a valid status code (200, 401, etc., not 500)
        assert response.status_code in [200, 401, 403, 404]


def test_generate_metrics_function() -> None:
    """Test the generate_metrics helper function."""
    metrics = generate_metrics()

    assert isinstance(metrics, bytes)
    assert b"http_requests_total" in metrics
    assert b"pdca_cycles_created_total" in metrics
