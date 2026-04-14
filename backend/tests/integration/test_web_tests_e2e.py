"""End-to-end integration tests for web automation testing API."""
import uuid
from unittest.mock import patch

from fastapi.testclient import TestClient
from sqlmodel import Session

from app.core.config import settings
from app.models import User
from app.web_tests.models import WebTest, WebTestCreate
from app.web_tests import crud
from tests.utils.user import user_authentication_headers


@patch('app.web_tests.executor.check_claude_available')
@patch('app.web_tests.executor.validate_url')
def test_web_test_full_lifecycle(
    mock_validate_url, mock_check_claude,
    client: TestClient,
    db: Session,
    test_user: User
) -> None:
    """
    Test the complete lifecycle of a web test:
    1. Login and get authentication token
    2. Create a new web test via API
    3. Get test details
    4. Get tests list
    5. Delete the test
    6. Verify deletion
    """
    # Setup mocks
    mock_validate_url.return_value = True
    mock_check_claude.return_value = True

    # Step 1: Get authentication token
    password = "testpassword123"
    headers = user_authentication_headers(
        client=client,
        email=test_user.email,
        password=password
    )

    # Step 2: Create a new web test
    test_data = {
        "url": "https://example.com",
        "description": "Test homepage loads correctly"
    }

    response = client.post(
        f"{settings.API_V1_STR}/web-tests/",
        json=test_data,
        headers=headers
    )

    assert response.status_code == 201
    data = response.json()
    web_test_id = uuid.UUID(data["id"])
    assert data["url"] == test_data["url"]
    assert data["description"] == test_data["description"]
    assert data["status"] == "pending"

    # Get the web test from database
    web_test = crud.get_web_test_by_id(session=db, web_test_id=web_test_id)
    assert web_test is not None

    # Step 3: Get test details
    response = client.get(
        f"{settings.API_V1_STR}/web-tests/{web_test_id}",
        headers=headers
    )
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == str(web_test_id)
    assert data["url"] == test_data["url"]
    assert data["description"] == test_data["description"]
    assert "created_at" in data
    assert "status" in data

    # Step 4: Get tests list
    response = client.get(
        f"{settings.API_V1_STR}/web-tests/",
        headers=headers
    )
    assert response.status_code == 200
    data = response.json()
    assert "data" in data
    assert "count" in data
    assert data["count"] >= 1
    # Find our test in the list
    our_test = next((t for t in data["data"] if t["id"] == str(web_test_id)), None)
    assert our_test is not None
    assert our_test["url"] == test_data["url"]

    # Step 5: Delete the test
    # First, ensure the test is not running (set to failed if needed)
    web_test = crud.get_web_test_by_id(session=db, web_test_id=web_test_id)
    if web_test.status == "running":
        web_test = crud.update_web_test_status(
            session=db,
            db_web_test=web_test,
            status="failed"
        )

    response = client.delete(
        f"{settings.API_V1_STR}/web-tests/{web_test_id}",
        headers=headers
    )
    assert response.status_code == 200
    data = response.json()
    assert data["message"] == "Web test deleted successfully"

    # Step 6: Verify deletion
    response = client.get(
        f"{settings.API_V1_STR}/web-tests/{web_test_id}",
        headers=headers
    )
    assert response.status_code == 404

    # Verify it's gone from the list
    response = client.get(
        f"{settings.API_V1_STR}/web-tests/",
        headers=headers
    )
    assert response.status_code == 200
    data = response.json()
    our_test = next((t for t in data["data"] if t["id"] == str(web_test_id)), None)
    assert our_test is None


def test_web_test_create_invalid_url(
    client: TestClient,
    db: Session,
    test_user: User
) -> None:
    """Test that creating a web test with an invalid URL fails."""
    from unittest.mock import patch

    with patch('app.web_tests.executor.validate_url') as mock_validate:
        mock_validate.return_value = False

        password = "testpassword123"
        headers = user_authentication_headers(
            client=client,
            email=test_user.email,
            password=password
        )

        test_data = {
            "url": "not-a-valid-url",
            "description": "This should fail validation"
        }

        response = client.post(
            f"{settings.API_V1_STR}/web-tests/",
            json=test_data,
            headers=headers
        )

        assert response.status_code == 400
        data = response.json()
        assert "detail" in data
        assert "Invalid URL format" in data["detail"]


def test_web_test_create_short_description(
    client: TestClient,
    db: Session,
    test_user: User
) -> None:
    """Test that creating a web test with a short description fails."""
    from unittest.mock import patch

    with patch('app.web_tests.executor.validate_url') as mock_validate:
        mock_validate.return_value = True

        password = "testpassword123"
        headers = user_authentication_headers(
            client=client,
            email=test_user.email,
            password=password
        )

        test_data = {
            "url": "https://example.com",
            "description": "Short"
        }

        response = client.post(
            f"{settings.API_V1_STR}/web-tests/",
            json=test_data,
            headers=headers
        )

        # Should fail validation (description too short)
        assert response.status_code == 422


def test_web_test_unauthorized_access(
    client: TestClient,
    db: Session,
    test_user: User
) -> None:
    """Test that unauthorized access to web tests is properly blocked."""
    # Create a test for the test user
    web_test_in = WebTestCreate(
        url="https://example.com",
        description="Test description for unauthorized access"
    )
    web_test = crud.create_web_test(
        session=db,
        web_test_create=web_test_in,
        owner_id=test_user.id
    )

    # Create another user
    from tests.utils.user import create_random_user
    other_user = create_random_user(db)
    password = "otherpassword123"
    headers = user_authentication_headers(
        client=client,
        email=other_user.email,
        password=password
    )

    # Try to access the first user's test
    response = client.get(
        f"{settings.API_V1_STR}/web-tests/{web_test.id}",
        headers=headers
    )

    assert response.status_code == 403

    # Try to delete the first user's test
    response = client.delete(
        f"{settings.API_V1_STR}/web-tests/{web_test.id}",
        headers=headers
    )

    assert response.status_code == 403

    # Clean up
    crud.delete_web_test(session=db, db_web_test=web_test)


def test_web_test_status_filtering(
    client: TestClient,
    db: Session,
    test_user: User
) -> None:
    """Test filtering web tests by status."""
    password = "testpassword123"
    headers = user_authentication_headers(
        client=client,
        email=test_user.email,
        password=password
    )

    # Create tests with different statuses
    tests = []
    for status in ["pending", "completed", "failed"]:
        web_test_in = WebTestCreate(
            url=f"https://example.com/{status}",
            description=f"Test with status {status}"
        )
        web_test = crud.create_web_test(
            session=db,
            web_test_create=web_test_in,
            owner_id=test_user.id
        )
        web_test = crud.update_web_test_status(
            session=db,
            db_web_test=web_test,
            status=status
        )
        tests.append(web_test)

    # Test filtering by status
    for status in ["pending", "completed", "failed"]:
        response = client.get(
            f"{settings.API_V1_STR}/web-tests/?status={status}",
            headers=headers
        )
        assert response.status_code == 200
        data = response.json()
        assert "data" in data
        # All returned tests should have the requested status
        for test in data["data"]:
            assert test["status"] == status

    # Clean up
    for test in tests:
        crud.delete_web_test(session=db, db_web_test=test)


def test_web_test_pagination(
    client: TestClient,
    db: Session,
    test_user: User
) -> None:
    """Test pagination of web tests list."""
    password = "testpassword123"
    headers = user_authentication_headers(
        client=client,
        email=test_user.email,
        password=password
    )

    # Create multiple tests
    tests = []
    for i in range(5):
        web_test_in = WebTestCreate(
            url=f"https://example.com/page-{i}",
            description=f"Test {i}"
        )
        web_test = crud.create_web_test(
            session=db,
            web_test_create=web_test_in,
            owner_id=test_user.id
        )
        tests.append(web_test)

    # Test pagination
    response = client.get(
        f"{settings.API_V1_STR}/web-tests/?skip=0&limit=3",
        headers=headers
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data["data"]) == 3
    assert data["count"] >= 5

    response = client.get(
        f"{settings.API_V1_STR}/web-tests/?skip=3&limit=3",
        headers=headers
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data["data"]) == 2  # Only 2 remaining

    # Clean up
    for test in tests:
        crud.delete_web_test(session=db, db_web_test=test)
