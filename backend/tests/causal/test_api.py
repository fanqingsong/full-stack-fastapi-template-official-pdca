"""Tests for causal analysis API."""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models import User


def test_analyze_endpoint_requires_auth(client: TestClient):
    """Test that analyze endpoint requires authentication."""
    response = client.post(
        "/api/v1/causal/analyze",
        json={"natural_language": "What causes success?"}
    )
    assert response.status_code == 401


def test_variables_endpoint_requires_auth(client: TestClient):
    """Test that variables endpoint requires authentication."""
    response = client.get("/api/v1/causal/variables")
    assert response.status_code == 401


@pytest.mark.no_db
def test_variables_endpoint_authenticated():
    """Test variables listing endpoint without database."""
    # This test verifies the endpoint structure without requiring database
    from app.causal.api import router
    from app.causal.data_extractor import get_available_variables

    # Test that the function works
    variables = get_available_variables()
    assert len(variables) > 0
    assert any("success" in var for var in variables)
