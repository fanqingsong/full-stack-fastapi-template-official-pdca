"""Tests for web_tests API endpoints."""

import uuid
from unittest.mock import patch, MagicMock

import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session

from app.core.config import settings
from app.models import User
from app.web_tests.models import WebTest, WebTestCreate, WebTestResult
from app.web_tests.crud import create_web_test, update_web_test_status


@pytest.fixture
def test_web_test(db: Session, test_user: User) -> WebTest:
    """Create a test web test."""
    web_test_create = WebTestCreate(
        url="https://example.com",
        description="Test description for web automation"
    )
    return create_web_test(session=db, web_test_create=web_test_create, owner_id=test_user.id)


@patch('app.web_tests.executor.check_claude_available')
@patch('app.web_tests.executor.validate_url')
def test_create_web_test(
    mock_validate_url, mock_check_claude, client: TestClient, superuser_token_headers: dict[str, str]
) -> None:
    """Test creating a new web test."""
    mock_validate_url.return_value = True
    mock_check_claude.return_value = True

    data = {
        "url": "https://example.com",
        "description": "Test the login functionality of the website"
    }
    response = client.post(
        f"{settings.API_V1_STR}/web-tests/",
        headers=superuser_token_headers,
        json=data,
    )
    assert response.status_code == 201
    content = response.json()
    assert content["url"] == data["url"]
    assert content["description"] == data["description"]
    assert content["status"] == "pending"
    assert "id" in content
    assert "owner_id" in content


@patch('app.web_tests.executor.check_claude_available')
@patch('app.web_tests.executor.validate_url')
def test_create_web_test_invalid_url(
    mock_validate_url, mock_check_claude, client: TestClient, superuser_token_headers: dict[str, str]
) -> None:
    """Test creating a web test with invalid URL."""
    mock_validate_url.return_value = False
    mock_check_claude.return_value = True

    data = {
        "url": "not-a-valid-url",
        "description": "Test description"
    }
    response = client.post(
        f"{settings.API_V1_STR}/web-tests/",
        headers=superuser_token_headers,
        json=data,
    )
    assert response.status_code == 400


def test_read_web_tests(
    client: TestClient, superuser_token_headers: dict[str, str], db: Session, test_user: User
) -> None:
    """Test reading list of web tests."""
    # Create a few web tests
    from app.web_tests.crud import create_web_test
    from app.web_tests.models import WebTestCreate

    for i in range(3):
        web_test_create = WebTestCreate(
            url=f"https://example{i}.com",
            description=f"Test description {i}"
        )
        create_web_test(session=db, web_test_create=web_test_create, owner_id=test_user.id)

    response = client.get(
        f"{settings.API_V1_STR}/web-tests/",
        headers=superuser_token_headers,
    )
    assert response.status_code == 200
    content = response.json()
    assert len(content["data"]) >= 3
    assert "count" in content


def test_read_web_test(
    client: TestClient, superuser_token_headers: dict[str, str], test_web_test: WebTest
) -> None:
    """Test reading a single web test."""
    response = client.get(
        f"{settings.API_V1_STR}/web-tests/{test_web_test.id}",
        headers=superuser_token_headers,
    )
    assert response.status_code == 200
    content = response.json()
    assert content["id"] == str(test_web_test.id)
    assert content["url"] == test_web_test.url
    assert content["description"] == test_web_test.description


def test_read_web_test_not_found(
    client: TestClient, superuser_token_headers: dict[str, str]
) -> None:
    """Test reading a non-existent web test."""
    response = client.get(
        f"{settings.API_V1_STR}/web-tests/{uuid.uuid4()}",
        headers=superuser_token_headers,
    )
    assert response.status_code == 404
    content = response.json()
    assert content["detail"] == "Web test not found"


def test_read_web_test_not_enough_permissions(
    client: TestClient, normal_user_token_headers: dict[str, str], test_web_test: WebTest
) -> None:
    """Test reading a web test owned by another user."""
    response = client.get(
        f"{settings.API_V1_STR}/web-tests/{test_web_test.id}",
        headers=normal_user_token_headers,
    )
    assert response.status_code == 403
    content = response.json()
    assert content["detail"] == "Not enough permissions"


def test_delete_web_test(
    client: TestClient, superuser_token_headers: dict[str, str], test_web_test: WebTest
) -> None:
    """Test deleting a web test."""
    response = client.delete(
        f"{settings.API_V1_STR}/web-tests/{test_web_test.id}",
        headers=superuser_token_headers,
    )
    assert response.status_code == 200
    content = response.json()
    assert content["message"] == "Web test deleted successfully"


def test_delete_web_test_not_found(
    client: TestClient, superuser_token_headers: dict[str, str]
) -> None:
    """Test deleting a non-existent web test."""
    response = client.delete(
        f"{settings.API_V1_STR}/web-tests/{uuid.uuid4()}",
        headers=superuser_token_headers,
    )
    assert response.status_code == 404
    content = response.json()
    assert content["detail"] == "Web test not found"


def test_delete_web_test_not_enough_permissions(
    client: TestClient, normal_user_token_headers: dict[str, str], test_web_test: WebTest
) -> None:
    """Test deleting a web test owned by another user."""
    response = client.delete(
        f"{settings.API_V1_STR}/web-tests/{test_web_test.id}",
        headers=normal_user_token_headers,
    )
    assert response.status_code == 403
    content = response.json()
    assert content["detail"] == "Not enough permissions"


@patch('app.web_tests.executor.check_claude_available')
def test_retry_web_test(
    mock_check_claude, client: TestClient, superuser_token_headers: dict[str, str],
    db: Session, test_web_test: WebTest
) -> None:
    """Test retrying a failed web test."""
    mock_check_claude.return_value = True

    # First, update the test to failed status
    update_web_test_status(session=db, db_web_test=test_web_test, status="failed")

    response = client.post(
        f"{settings.API_V1_STR}/web-tests/{test_web_test.id}/retry",
        headers=superuser_token_headers,
    )
    assert response.status_code == 200
    content = response.json()
    assert content["status"] == "pending"


@patch('app.web_tests.executor.check_claude_available')
def test_retry_web_test_claude_not_available(
    mock_check_claude, client: TestClient, superuser_token_headers: dict[str, str],
    db: Session, test_web_test: WebTest
) -> None:
    """Test retrying a web test when Claude CLI is not available."""
    mock_check_claude.return_value = False

    # First, update the test to failed status
    update_web_test_status(session=db, db_web_test=test_web_test, status="failed")

    response = client.post(
        f"{settings.API_V1_STR}/web-tests/{test_web_test.id}/retry",
        headers=superuser_token_headers,
    )
    assert response.status_code == 503
    content = response.json()
    assert "Claude CLI not available" in content["detail"]


def test_get_web_test_result(
    client: TestClient, superuser_token_headers: dict[str, str], db: Session, test_web_test: WebTest
) -> None:
    """Test getting a web test result."""
    # Create a result for the test
    from app.web_tests.crud import create_web_test_result

    result = create_web_test_result(
        session=db,
        test_id=test_web_test.id,
        success=True,
        execution_logs="Test passed successfully",
        execution_duration=10.5,
        claude_version="claude-3.5-sonnet"
    )

    response = client.get(
        f"{settings.API_V1_STR}/web-tests/{test_web_test.id}/result",
        headers=superuser_token_headers,
    )
    assert response.status_code == 200
    content = response.json()
    assert content["test_id"] == str(test_web_test.id)
    assert content["success"] is True
    assert content["execution_logs"] == "Test passed successfully"


def test_get_web_test_result_not_found(
    client: TestClient, superuser_token_headers: dict[str, str], test_web_test: WebTest
) -> None:
    """Test getting a result for a test that has no result."""
    response = client.get(
        f"{settings.API_V1_STR}/web-tests/{test_web_test.id}/result",
        headers=superuser_token_headers,
    )
    assert response.status_code == 404
    content = response.json()
    assert content["detail"] == "Result not found"
