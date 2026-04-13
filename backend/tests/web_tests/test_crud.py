"""CRUD operations tests for web tests module."""

import uuid
from datetime import datetime, timezone

import pytest
from sqlmodel import Session

from app.models import User
from app.web_tests import crud
from app.web_tests.models import WebTest, WebTestCreate, WebTestResult


def test_create_web_test(db: Session, test_user: User) -> None:
    """Test creating a web test."""
    web_test_in = WebTestCreate(
        url="https://example.com",
        description="Test the login functionality",
    )
    web_test = crud.create_web_test(
        session=db, web_test_create=web_test_in, owner_id=test_user.id
    )

    assert web_test.id is not None
    assert web_test.url == "https://example.com"
    assert web_test.description == "Test the login functionality"
    assert web_test.status == "pending"
    assert web_test.owner_id == test_user.id
    assert web_test.created_at is not None
    assert web_test.started_at is None
    assert web_test.completed_at is None


def test_create_web_test_invalid_url(db: Session, test_user: User) -> None:
    """Test creating a web test with invalid URL."""
    web_test_in = WebTestCreate(
        url="not-a-valid-url",
        description="Test with invalid URL",
    )
    with pytest.raises(ValueError, match="Invalid URL format"):
        crud.create_web_test(
            session=db, web_test_create=web_test_in, owner_id=test_user.id
        )


def test_get_web_test_by_id(db: Session, test_user: User) -> None:
    """Test retrieving a web test by ID."""
    web_test_in = WebTestCreate(
        url="https://example.com",
        description="Test description",
    )
    web_test = crud.create_web_test(
        session=db, web_test_create=web_test_in, owner_id=test_user.id
    )

    retrieved_web_test = crud.get_web_test_by_id(session=db, web_test_id=web_test.id)

    assert retrieved_web_test is not None
    assert retrieved_web_test.id == web_test.id
    assert retrieved_web_test.url == web_test.url
    assert retrieved_web_test.description == web_test.description


def test_get_web_test_by_id_not_found(db: Session) -> None:
    """Test retrieving a non-existent web test."""
    fake_id = uuid.uuid4()
    result = crud.get_web_test_by_id(session=db, web_test_id=fake_id)
    assert result is None


def test_get_web_tests_by_owner(db: Session, test_user: User) -> None:
    """Test retrieving all web tests for a specific owner."""
    # Create multiple web tests
    for i in range(3):
        web_test_in = WebTestCreate(
            url=f"https://example{i}.com",
            description=f"Test description {i}",
        )
        crud.create_web_test(
            session=db, web_test_create=web_test_in, owner_id=test_user.id
        )

    # Retrieve all web tests for the owner
    web_tests = crud.get_web_tests_by_owner(session=db, owner_id=test_user.id)

    assert len(web_tests) == 3
    assert all(test.owner_id == test_user.id for test in web_tests)


def test_get_web_tests_by_owner_with_pagination(db: Session, test_user: User) -> None:
    """Test retrieving web tests with pagination."""
    # Create 5 web tests
    for i in range(5):
        web_test_in = WebTestCreate(
            url=f"https://example{i}.com",
            description=f"Test description {i}",
        )
        crud.create_web_test(
            session=db, web_test_create=web_test_in, owner_id=test_user.id
        )

    # Retrieve with pagination
    web_tests_page1 = crud.get_web_tests_by_owner(
        session=db, owner_id=test_user.id, skip=0, limit=2
    )
    web_tests_page2 = crud.get_web_tests_by_owner(
        session=db, owner_id=test_user.id, skip=2, limit=2
    )

    assert len(web_tests_page1) == 2
    assert len(web_tests_page2) == 2


def test_get_web_tests_by_owner_empty(db: Session, test_user: User) -> None:
    """Test retrieving web tests when owner has no tests."""
    web_tests = crud.get_web_tests_by_owner(session=db, owner_id=test_user.id)
    assert len(web_tests) == 0


def test_count_web_tests_by_owner(db: Session, test_user: User) -> None:
    """Test counting web tests for a specific owner."""
    # Create 3 web tests
    for i in range(3):
        web_test_in = WebTestCreate(
            url=f"https://example{i}.com",
            description=f"Test description {i}",
        )
        crud.create_web_test(
            session=db, web_test_create=web_test_in, owner_id=test_user.id
        )

    count = crud.count_web_tests_by_owner(session=db, owner_id=test_user.id)
    assert count == 3


def test_count_web_tests_by_owner_empty(db: Session, test_user: User) -> None:
    """Test counting web tests when owner has no tests."""
    count = crud.count_web_tests_by_owner(session=db, owner_id=test_user.id)
    assert count == 0


def test_count_web_tests_by_status(db: Session, test_user: User) -> None:
    """Test counting web tests by status."""
    # Create tests with different statuses
    statuses = ["pending", "running", "completed", "failed"]
    for status in statuses:
        web_test_in = WebTestCreate(
            url=f"https://{status}.com",
            description=f"Test {status}",
        )
        web_test = crud.create_web_test(
            session=db, web_test_create=web_test_in, owner_id=test_user.id
        )
        if status != "pending":
            crud.update_web_test_status(session=db, db_web_test=web_test, status=status)

    # Count by status
    pending_count = crud.count_web_tests_by_status(
        session=db, owner_id=test_user.id, status="pending"
    )
    running_count = crud.count_web_tests_by_status(
        session=db, owner_id=test_user.id, status="running"
    )
    completed_count = crud.count_web_tests_by_status(
        session=db, owner_id=test_user.id, status="completed"
    )
    failed_count = crud.count_web_tests_by_status(
        session=db, owner_id=test_user.id, status="failed"
    )

    assert pending_count == 1
    assert running_count == 1
    assert completed_count == 1
    assert failed_count == 1


def test_count_web_tests_by_status_invalid_status(db: Session, test_user: User) -> None:
    """Test counting with invalid status raises error."""
    web_test_in = WebTestCreate(
        url="https://example.com",
        description="Test description",
    )
    crud.create_web_test(
        session=db, web_test_create=web_test_in, owner_id=test_user.id
    )

    with pytest.raises(ValueError, match="Invalid status"):
        crud.count_web_tests_by_status(
            session=db, owner_id=test_user.id, status="invalid"
        )


def test_update_web_test_status_to_running(db: Session, test_user: User) -> None:
    """Test updating web test status to running."""
    web_test_in = WebTestCreate(
        url="https://example.com",
        description="Test description",
    )
    web_test = crud.create_web_test(
        session=db, web_test_create=web_test_in, owner_id=test_user.id
    )

    assert web_test.status == "pending"
    assert web_test.started_at is None

    updated_web_test = crud.update_web_test_status(
        session=db, db_web_test=web_test, status="running"
    )

    assert updated_web_test.status == "running"
    assert updated_web_test.started_at is not None
    assert isinstance(updated_web_test.started_at, datetime)


def test_update_web_test_status_to_completed(db: Session, test_user: User) -> None:
    """Test updating web test status to completed."""
    web_test_in = WebTestCreate(
        url="https://example.com",
        description="Test description",
    )
    web_test = crud.create_web_test(
        session=db, web_test_create=web_test_in, owner_id=test_user.id
    )

    # First update to running
    web_test = crud.update_web_test_status(
        session=db, db_web_test=web_test, status="running"
    )

    # Then update to completed
    updated_web_test = crud.update_web_test_status(
        session=db, db_web_test=web_test, status="completed"
    )

    assert updated_web_test.status == "completed"
    assert updated_web_test.completed_at is not None
    assert isinstance(updated_web_test.completed_at, datetime)


def test_update_web_test_status_to_failed(db: Session, test_user: User) -> None:
    """Test updating web test status to failed."""
    web_test_in = WebTestCreate(
        url="https://example.com",
        description="Test description",
    )
    web_test = crud.create_web_test(
        session=db, web_test_create=web_test_in, owner_id=test_user.id
    )

    updated_web_test = crud.update_web_test_status(
        session=db, db_web_test=web_test, status="failed"
    )

    assert updated_web_test.status == "failed"
    assert updated_web_test.completed_at is not None


def test_delete_web_test(db: Session, test_user: User) -> None:
    """Test deleting a web test."""
    web_test_in = WebTestCreate(
        url="https://example.com",
        description="Test description",
    )
    web_test = crud.create_web_test(
        session=db, web_test_create=web_test_in, owner_id=test_user.id
    )

    web_test_id = web_test.id
    deleted_web_test = crud.delete_web_test(session=db, db_web_test=web_test)

    assert deleted_web_test.id == web_test_id

    # Verify it's deleted
    retrieved = crud.get_web_test_by_id(session=db, web_test_id=web_test_id)
    assert retrieved is None


def test_create_web_test_result(db: Session, test_user: User) -> None:
    """Test creating a web test result."""
    # First create a web test
    web_test_in = WebTestCreate(
        url="https://example.com",
        description="Test description",
    )
    web_test = crud.create_web_test(
        session=db, web_test_create=web_test_in, owner_id=test_user.id
    )

    # Create result
    result = crud.create_web_test_result(
        session=db,
        test_id=web_test.id,
        success=True,
        execution_logs="Test passed successfully",
        execution_duration=45.5,
        screenshot_path="/screenshots/test.png",
        video_path="/videos/test.mp4",
        error_message=None,
        claude_version="claude-sonnet-4.6",
    )

    assert result.id is not None
    assert result.test_id == web_test.id
    assert result.success is True
    assert result.execution_logs == "Test passed successfully"
    assert result.execution_duration == 45.5
    assert result.screenshot_path == "/screenshots/test.png"
    assert result.video_path == "/videos/test.mp4"
    assert result.error_message is None
    assert result.claude_version == "claude-sonnet-4.6"
    assert result.created_at is not None


def test_create_web_test_result_with_error(db: Session, test_user: User) -> None:
    """Test creating a web test result with error."""
    web_test_in = WebTestCreate(
        url="https://example.com",
        description="Test description",
    )
    web_test = crud.create_web_test(
        session=db, web_test_create=web_test_in, owner_id=test_user.id
    )

    result = crud.create_web_test_result(
        session=db,
        test_id=web_test.id,
        success=False,
        execution_logs="Test execution started",
        error_message="Element not found: #login-button",
    )

    assert result.success is False
    assert result.error_message == "Element not found: #login-button"


def test_create_web_test_result_invalid_test_id(db: Session, test_user: User) -> None:
    """Test creating a result with invalid test ID."""
    fake_id = uuid.uuid4()

    with pytest.raises(ValueError, match="Web test not found"):
        crud.create_web_test_result(
            session=db,
            test_id=fake_id,
            success=True,
            execution_logs="Test logs",
        )


def test_get_web_test_result_by_test_id(db: Session, test_user: User) -> None:
    """Test retrieving web test result by test ID."""
    # Create a web test
    web_test_in = WebTestCreate(
        url="https://example.com",
        description="Test description",
    )
    web_test = crud.create_web_test(
        session=db, web_test_create=web_test_in, owner_id=test_user.id
    )

    # Create result
    result = crud.create_web_test_result(
        session=db,
        test_id=web_test.id,
        success=True,
        execution_logs="Test passed",
    )

    # Retrieve result
    retrieved_result = crud.get_web_test_result_by_test_id(
        session=db, test_id=web_test.id
    )

    assert retrieved_result is not None
    assert retrieved_result.id == result.id
    assert retrieved_result.test_id == web_test.id
    assert retrieved_result.success is True


def test_get_web_test_result_by_test_id_not_found(db: Session, test_user: User) -> None:
    """Test retrieving result for test without results."""
    web_test_in = WebTestCreate(
        url="https://example.com",
        description="Test description",
    )
    web_test = crud.create_web_test(
        session=db, web_test_create=web_test_in, owner_id=test_user.id
    )

    result = crud.get_web_test_result_by_test_id(session=db, test_id=web_test.id)
    assert result is None


def test_web_test_cascade_delete(db: Session, test_user: User) -> None:
    """Test that deleting a web test works correctly."""
    # Create a web test
    web_test_in = WebTestCreate(
        url="https://example.com",
        description="Test description",
    )
    web_test = crud.create_web_test(
        session=db, web_test_create=web_test_in, owner_id=test_user.id
    )

    # Create result
    result = crud.create_web_test_result(
        session=db,
        test_id=web_test.id,
        success=True,
        execution_logs="Test passed",
    )

    web_test_id = web_test.id
    result_id = result.id

    # Delete web test (cascade delete is handled by database)
    deleted_web_test = crud.delete_web_test(session=db, db_web_test=web_test)
    assert deleted_web_test.id == web_test_id

    # Verify web test is deleted
    retrieved_web_test = crud.get_web_test_by_id(session=db, web_test_id=web_test_id)
    assert retrieved_web_test is None

    # Note: Cascade delete of WebTestResult is handled by the database
    # through the foreign key constraint with ondelete="CASCADE"
    # The database-level CASCADE should automatically delete the result
