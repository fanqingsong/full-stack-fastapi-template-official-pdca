"""Test metrics collection performance overhead."""
import pytest
import time
from fastapi.testclient import TestClient


def test_metrics_endpoint_response_time(client: TestClient) -> None:
    """Test that /metrics endpoint responds quickly."""
    start = time.time()
    response = client.get("/metrics")
    duration = time.time() - start

    assert response.status_code == 200
    # Should respond within 100ms
    assert duration < 0.1, f"/metrics took {duration:.3f}s, expected < 0.1s"


def test_middleware_overhead_is_minimal(client: TestClient) -> None:
    """Test that middleware adds minimal overhead to requests."""
    # Make multiple requests to get average
    iterations = 100
    times = []

    for _ in range(iterations):
        start = time.time()
        client.get("/api/v1/items/")
        times.append(time.time() - start)

    avg_time = sum(times) / len(times)

    # Average request should be under 50ms (allowing for test environment)
    assert avg_time < 0.05, f"Average request time {avg_time:.3f}s exceeds 50ms"


def test_concurrent_metric_recording() -> None:
    """Test that concurrent metric recording is thread-safe."""
    import threading
    from app.core.metrics import http_requests_total

    threads = []
    iterations_per_thread = 100

    def increment_metric():
        for _ in range(iterations_per_thread):
            http_requests_total.labels(
                method='GET',
                path='/test',
                status='200'
            ).inc()

    # Start 10 threads
    for _ in range(10):
        thread = threading.Thread(target=increment_metric)
        threads.append(thread)
        thread.start()

    # Wait for all threads to complete
    for thread in threads:
        thread.join()

    # Check metric value
    expected_value = 10 * iterations_per_thread
    actual_value = http_requests_total.labels(
        method='GET',
        path='/test',
        status='200'
    )._value.get()

    assert actual_value >= expected_value


def test_memory_usage_stays_bound() -> None:
    """Test that metrics don't cause unbounded memory growth."""
    import gc
    import tracemalloc
    from app.core.metrics import http_requests_total

    gc.collect()
    tracemalloc.start()

    # Record baseline
    baseline_memory = tracemalloc.get_traced_memory()[0]

    # Generate many metric recordings
    for i in range(10000):
        http_requests_total.labels(
            method='GET',
            path=f'/test/{i}',
            status='200'
        ).inc()

    # Force garbage collection
    gc.collect()

    # Check memory growth
    current_memory = tracemalloc.get_traced_memory()[0]
    memory_growth = current_memory - baseline_memory

    # Memory growth should be reasonable (< 10MB)
    assert memory_growth < 10 * 1024 * 1024, \
        f"Memory growth {memory_growth / 1024 / 1024:.2f}MB exceeds 10MB"

    tracemalloc.stop()
