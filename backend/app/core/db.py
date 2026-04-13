from sqlmodel import Session, create_engine, select

from app import crud
from app.core.config import settings
from app.models import User, UserCreate

# Import PDCA models first, before creating the engine
from app.pdca.models import PDCACycle, AgentConfig  # noqa: F401

# Now create the engine after all models are imported
engine = create_engine(str(settings.SQLALCHEMY_DATABASE_URI))

# Import metrics module (optional - may not be available in all environments)
try:
    from app.core import metrics as metrics_module
    HAS_METRICS = True
except ImportError:
    HAS_METRICS = False
    metrics_module = None


# make sure all SQLModel models are imported (app.models) before initializing DB
# otherwise, SQLModel might fail to initialize relationships properly
# for more details: https://github.com/fastapi/full-stack-fastapi-template/issues/28


def init_db(session: Session) -> None:
    # Tables should be created with Alembic migrations
    # But if you don't want to use migrations, create
    # the tables un-commenting the next lines
    # from sqlmodel import SQLModel

    # This works because the models are already imported and registered from app.models
    # SQLModel.metadata.create_all(engine)

    user = session.exec(
        select(User).where(User.email == settings.FIRST_SUPERUSER)
    ).first()
    if not user:
        user_in = UserCreate(
            email=settings.FIRST_SUPERUSER,
            password=settings.FIRST_SUPERUSER_PASSWORD,
            is_superuser=True,
        )
        user = crud.create_user(session=session, user_create=user_in)

if HAS_METRICS and metrics_module:
    # Only import and use metrics if the prometheus_client package is available
    from app.core.metrics import db_connections_active
else:
    # Create a dummy function if metrics are not available
    db_connections_active = None

import logging

logger = logging.getLogger(__name__)


def update_db_pool_metrics():
    """
    Update database connection pool metrics.

    Should be called periodically to track pool state.
    """
    if not HAS_METRICS or db_connections_active is None:
        # Metrics not available, skip
        return

    try:
        if engine and engine.pool:
            pool = engine.pool

            # Get pool status
            status = pool.status()
            db_connections_active.labels(state='checked_out').set(status.checkedout)
            db_connections_active.labels(state='active').set(pool.size() - pool.checkedout())
            db_connections_active.labels(state='idle').set(pool.checkedout())

    except Exception as e:
        logger.warning(f"Failed to update DB pool metrics: {e}")
