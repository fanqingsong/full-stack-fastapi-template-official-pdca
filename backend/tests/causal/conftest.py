"""Minimal conftest for causal tests that don't need database."""

import pytest
from collections.abc import Generator
from sqlmodel import Session


@pytest.fixture(scope="session")
def db() -> Generator[Session, None, None]:
    """Override database fixture for causal tests - no database needed."""
    yield None
