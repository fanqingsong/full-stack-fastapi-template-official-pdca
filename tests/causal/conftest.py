"""Pytest fixtures for causal tests."""

import sys
from pathlib import Path

# Add backend to path so we can import fixtures
backend_path = Path(__file__).parent.parent / "backend"
sys.path.insert(0, str(backend_path))

from tests.conftest import db  # noqa: E402

# Export the db fixture as db_session
db_session = db  # noqa: F821
