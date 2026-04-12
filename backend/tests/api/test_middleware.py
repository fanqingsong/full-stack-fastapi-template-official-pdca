"""Test Prometheus middleware."""
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from app.api.middleware import PrometheusMiddleware
from app.core.metrics import http_requests_total, http_request_duration_seconds


@pytest.fixture
def app_with_middleware():
    """Create a test app with Prometheus middleware."""
    app = FastAPI()
    app.add_middleware(PrometheusMiddleware)

    @app.get("/test")
    async def test_endpoint():
        return {"message": "test"}

    @app.get("/test-error")
    async def test_error_endpoint():
        raise ValueError("Test error")

    return app


@pytest.fixture
def client(app_with_middleware):
    """Create test client."""
    return TestClient(app_with_middleware)


def test_middleware_tracks_successful_requests(client):
    """Test that middleware tracks successful requests."""
    initial_value = http_requests_total.labels(
        method='GET',
        path='/test',
        status='200'
    )._value.get()

    response = client.get("/test")

    assert response.status_code == 200

    final_value = http_requests_total.labels(
        method='GET',
        path='/test',
        status='200'
    )._value.get()

    assert final_value == initial_value + 1


def test_middleware_tracks_error_requests(client):
    """Test that middleware tracks failed requests."""
    initial_value = http_requests_total.labels(
        method='GET',
        path='/test-error',
        status='500'
    )._value.get()

    response = client.get("/test-error")

    assert response.status_code == 500

    final_value = http_requests_total.labels(
        method='GET',
        path='/test-error',
        status='500'
    )._value.get()

    assert final_value == initial_value + 1


def test_middleware_tracks_request_duration(client):
    """Test that middleware tracks request duration."""
    response = client.get("/test")

    # Get metric samples
    metric_samples = http_request_duration_seconds.labels(
        method='GET',
        path='/test',
        status='200'
    ).collect()

    # Should have at least one sample
    assert len(metric_samples) > 0
