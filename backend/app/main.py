import logging

# Try to import sentry_sdk (optional - for production monitoring)
try:
    import sentry_sdk
    HAS_SENTRY = True
except ImportError:
    HAS_SENTRY = False
    sentry_sdk = None

from fastapi import FastAPI
from fastapi.routing import APIRoute
from fastapi.responses import Response
from starlette.middleware.cors import CORSMiddleware

from app.api.main import api_router
from app.core.config import settings
from app.core.minio import minio_client

# Try to import monitoring components (optional)
try:
    from app.api.middleware import PrometheusMiddleware
    from app.core.metrics import generate_metrics
    HAS_MONITORING = True
except ImportError:
    HAS_MONITORING = False
    PrometheusMiddleware = None
    generate_metrics = None

logger = logging.getLogger(__name__)


def custom_generate_unique_id(route: APIRoute) -> str:
    # Handle routes without tags (like /metrics)
    if route.tags and len(route.tags) > 0:
        return f"{route.tags[0]}-{route.name}"
    return route.name


if HAS_SENTRY and settings.SENTRY_DSN and settings.ENVIRONMENT != "local":
    sentry_sdk.init(dsn=str(settings.SENTRY_DSN), enable_tracing=True)

app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    generate_unique_id_function=custom_generate_unique_id,
)

# Set all CORS enabled origins
if settings.all_cors_origins:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.all_cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

# Add Prometheus middleware if metrics are enabled and available
if settings.METRICS_ENABLED and HAS_MONITORING and PrometheusMiddleware:
    app.add_middleware(PrometheusMiddleware)

app.include_router(api_router, prefix=settings.API_V1_STR)


@app.on_event("startup")
async def startup_event() -> None:
    """Initialize services on startup."""
    # Ensure MinIO bucket exists
    try:
        # Access the client property to trigger lazy initialization and bucket creation
        _ = minio_client.client
        logger.info(f"MinIO bucket '{minio_client.bucket_name}' is ready")
    except Exception as e:
        logger.error(f"Failed to initialize MinIO bucket: {e}")
        # Don't fail startup - MinIO will retry on first access

    # Update DB pool metrics
    try:
        from app.core.db import update_db_pool_metrics
        update_db_pool_metrics()
        logger.info("Database pool metrics initialized")
    except Exception as e:
        logger.warning(f"Failed to initialize DB pool metrics: {e}")


@app.get("/metrics")
async def metrics():
    """
    Prometheus metrics endpoint.

    Returns metrics in Prometheus exposition format.
    Only accessible if METRICS_ENABLED is True and monitoring components are available.
    """
    if not settings.METRICS_ENABLED:
        return Response(content="Metrics disabled", status_code=404)

    if not HAS_MONITORING or generate_metrics is None:
        return Response(content="Monitoring not available", status_code=503)

    return Response(content=generate_metrics(), media_type="text/plain")


