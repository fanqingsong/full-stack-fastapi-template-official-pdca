# Import all models to ensure SQLModel can properly initialize relationships
# This is required for the database to work correctly
from app.models import *  # noqa: F401, F403
from app.pdca.models import *  # noqa: F401, F403
