"""
Prometheus monitoring middleware for FastAPI.

This middleware automatically tracks HTTP request metrics including
request count, duration, and active requests.
"""
import time
from typing import Callable
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

# Try to import metrics (optional)
try:
    from app.core.metrics import (
        http_requests_total,
        http_request_duration_seconds,
        http_requests_active,
    )
    HAS_METRICS = True
except ImportError:
    HAS_METRICS = False
    # Create dummy functions if metrics are not available
    http_requests_total = None
    http_request_duration_seconds = None
    http_requests_active = None


class PrometheusMiddleware(BaseHTTPMiddleware):
    """
    Middleware to track HTTP request metrics for Prometheus.

    Automatically records:
    - Total request count (by method, path, status)
    - Request duration (by method, path, status)
    - Active request count (by path)
    """

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        Process request and record metrics.

        Args:
            request: Incoming HTTP request
            call_next: Next middleware or route handler

        Returns:
            HTTP response with metrics recorded
        """
        # Extract path for metrics
        path = request.url.path

        # Increment active requests (if metrics available)
        if HAS_METRICS and http_requests_active:
            http_requests_active.labels(path=path).inc()

        # Record start time
        start_time = time.time()

        try:
            # Process request
            response = await call_next(request)

            # Record metrics (if available)
            if HAS_METRICS:
                duration = time.time() - start_time
                status = str(response.status_code)

                http_request_duration_seconds.labels(
                    method=request.method,
                    path=path,
                    status=status
                ).observe(duration)

                http_requests_total.labels(
                    method=request.method,
                    path=path,
                    status=status
                ).inc()

            return response

        finally:
            # Decrement active requests (if metrics available)
            if HAS_METRICS and http_requests_active:
                http_requests_active.labels(path=path).dec()
