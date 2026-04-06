"""Tests for PDCA API routes."""
import uuid

from fastapi.testclient import TestClient
from sqlmodel import Session

from app.core.config import settings
from app.pdca.models import PDCACycle, AgentConfig


def test_create_cycle(
    client: TestClient, superuser_token_headers: dict[str, str], db: Session
) -> None:
    """Test creating a PDCA cycle."""
    data = {
        "name": "Test Cycle",
        "description": "Test description",
        "goal": "Test goal",
        "agent_type": "openai",
        "plan_details": {},
        "agent_input": {"prompt": "test"}
    }
    response = client.post(
        f"{settings.API_V1_STR}/pdca/cycles",
        headers=superuser_token_headers,
        json=data,
    )
    assert response.status_code == 201
    content = response.json()
    assert content["name"] == data["name"]
    assert content["goal"] == data["goal"]
    assert "id" in content


def test_read_cycles(
    client: TestClient, superuser_token_headers: dict[str, str], test_pdca_cycle: PDCACycle
) -> None:
    """Test reading PDCA cycles list."""
    response = client.get(
        f"{settings.API_V1_STR}/pdca/cycles",
        headers=superuser_token_headers,
    )
    assert response.status_code == 200
    content = response.json()
    assert "data" in content
    assert "count" in content
    assert content["count"] >= 1


def test_read_cycle(
    client: TestClient, superuser_token_headers: dict[str, str], test_pdca_cycle: PDCACycle
) -> None:
    """Test reading a single PDCA cycle."""
    response = client.get(
        f"{settings.API_V1_STR}/pdca/cycles/{test_pdca_cycle.id}",
        headers=superuser_token_headers,
    )
    assert response.status_code == 200
    content = response.json()
    assert content["id"] == str(test_pdca_cycle.id)
    assert content["name"] == test_pdca_cycle.name


def test_read_cycle_not_found(
    client: TestClient, superuser_token_headers: dict[str, str]
) -> None:
    """Test reading a non-existent PDCA cycle."""
    response = client.get(
        f"{settings.API_V1_STR}/pdca/cycles/{uuid.uuid4()}",
        headers=superuser_token_headers,
    )
    assert response.status_code == 404


def test_list_agent_types(
    client: TestClient
) -> None:
    """Test listing available agent types."""
    response = client.get(
        f"{settings.API_V1_STR}/pdca/agents/types",
    )
    assert response.status_code == 200
    content = response.json()
    assert "types" in content
    assert isinstance(content["types"], list)
    # Note: "openai" might not be registered if no agents are registered yet
    # so we just check that types is a list


def test_create_agent_config(
    client: TestClient, superuser_token_headers: dict[str, str]
) -> None:
    """Test creating an agent configuration."""
    data = {
        "name": "Test Config",
        "agent_type": "openai",
        "description": "Test config description",
        "config": {"model": "gpt-4", "temperature": 0.7}
    }
    response = client.post(
        f"{settings.API_V1_STR}/pdca/agents/configs",
        headers=superuser_token_headers,
        json=data,
    )
    assert response.status_code == 201
    content = response.json()
    assert content["name"] == data["name"]
    assert content["agent_type"] == data["agent_type"]
    assert "id" in content


def test_execute_cycle_unauthorized(
    client: TestClient, test_pdca_cycle: PDCACycle
) -> None:
    """Test executing a cycle without authentication."""
    response = client.post(
        f"{settings.API_V1_STR}/pdca/cycles/{test_pdca_cycle.id}/execute",
    )
    assert response.status_code == 401
