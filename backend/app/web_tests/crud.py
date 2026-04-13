"""CRUD operations for web automation testing."""

import uuid
from datetime import datetime, timezone

from sqlmodel import Session, select

from app.web_tests.models import WebTest, WebTestCreate, WebTestResult


def get_datetime_utc() -> datetime:
    """Get current datetime in UTC."""
    return datetime.now(timezone.utc)


def create_web_test(*, session: Session, web_test_create: WebTestCreate, owner_id: uuid.UUID) -> WebTest:
    """
    Create a new web test.

    Args:
        session: Database session
        web_test_create: Web test creation data
        owner_id: ID of the user who owns this test

    Returns:
        Created WebTest instance

    Raises:
        ValueError: If URL format is invalid
    """
    # Validate URL format
    url = web_test_create.url.strip()
    if not url.startswith(("http://", "https://")):
        raise ValueError("Invalid URL format")

    db_obj = WebTest.model_validate(
        web_test_create, update={"owner_id": owner_id}
    )
    session.add(db_obj)
    session.commit()
    session.refresh(db_obj)
    return db_obj


def get_web_test_by_id(*, session: Session, web_test_id: uuid.UUID) -> WebTest | None:
    """
    Get a web test by ID.

    Args:
        session: Database session
        web_test_id: ID of the web test to retrieve

    Returns:
        WebTest instance if found, None otherwise
    """
    statement = select(WebTest).where(WebTest.id == web_test_id)
    session_web_test = session.exec(statement).first()
    return session_web_test


def get_web_tests_by_owner(
    *, session: Session, owner_id: uuid.UUID, skip: int = 0, limit: int = 100
) -> list[WebTest]:
    """
    Get all web tests for a specific owner.

    Args:
        session: Database session
        owner_id: ID of the user who owns the tests
        skip: Number of records to skip (for pagination)
        limit: Maximum number of records to return

    Returns:
        List of WebTest instances
    """
    statement = (
        select(WebTest)
        .where(WebTest.owner_id == owner_id)
        .offset(skip)
        .limit(limit)
        .order_by(WebTest.created_at.desc())
    )
    return list(session.exec(statement).all())


def count_web_tests_by_owner(*, session: Session, owner_id: uuid.UUID) -> int:
    """
    Count all web tests for a specific owner.

    Args:
        session: Database session
        owner_id: ID of the user who owns the tests

    Returns:
        Count of web tests
    """
    statement = select(WebTest).where(WebTest.owner_id == owner_id)
    return len(session.exec(statement).all())


def count_web_tests_by_status(
    *, session: Session, owner_id: uuid.UUID, status: str
) -> int:
    """
    Count web tests by status for a specific owner.

    Args:
        session: Database session
        owner_id: ID of the user who owns the tests
        status: Status to filter by (pending, running, completed, failed, cancelled)

    Returns:
        Count of web tests with the specified status

    Raises:
        ValueError: If status is invalid
    """
    # Validate status
    valid_statuses = ["pending", "running", "completed", "failed", "cancelled"]
    if status not in valid_statuses:
        raise ValueError(f"Invalid status. Must be one of {valid_statuses}")

    statement = select(WebTest).where(
        WebTest.owner_id == owner_id, WebTest.status == status
    )
    return len(session.exec(statement).all())


def update_web_test_status(
    *, session: Session, db_web_test: WebTest, status: str
) -> WebTest:
    """
    Update the status of a web test.

    Automatically updates started_at when status changes to "running"
    and completed_at when status changes to "completed" or "failed".

    Args:
        session: Database session
        db_web_test: WebTest instance to update
        status: New status value

    Returns:
        Updated WebTest instance

    Raises:
        ValueError: If status is invalid
    """
    # Validate status
    valid_statuses = ["pending", "running", "completed", "failed", "cancelled"]
    if status not in valid_statuses:
        raise ValueError(f"Invalid status. Must be one of {valid_statuses}")

    # Update status
    db_web_test.status = status

    # Update timestamps based on status
    if status == "running" and db_web_test.started_at is None:
        db_web_test.started_at = get_datetime_utc()
    elif status in ["completed", "failed", "cancelled"] and db_web_test.completed_at is None:
        db_web_test.completed_at = get_datetime_utc()

    session.add(db_web_test)
    session.commit()
    session.refresh(db_web_test)
    return db_web_test


def delete_web_test(*, session: Session, db_web_test: WebTest) -> WebTest:
    """
    Delete a web test.

    Args:
        session: Database session
        db_web_test: WebTest instance to delete

    Returns:
        Deleted WebTest instance
    """
    session.delete(db_web_test)
    session.commit()
    return db_web_test


def create_web_test_result(
    *,
    session: Session,
    test_id: uuid.UUID,
    success: bool,
    execution_logs: str,
    error_message: str | None = None,
    screenshot_path: str | None = None,
    video_path: str | None = None,
    execution_duration: float | None = None,
    claude_version: str | None = None,
) -> WebTestResult:
    """
    Create a new web test result.

    Args:
        session: Database session
        test_id: ID of the associated web test
        success: Whether the test passed
        execution_logs: Test execution logs
        error_message: Error message if test failed
        screenshot_path: Path to screenshot
        video_path: Path to video recording
        execution_duration: Test execution duration in seconds
        claude_version: Version of Claude used

    Returns:
        Created WebTestResult instance

    Raises:
        ValueError: If the web test doesn't exist
    """
    # Verify that the web test exists
    web_test = get_web_test_by_id(session=session, web_test_id=test_id)
    if not web_test:
        raise ValueError("Web test not found")

    db_obj = WebTestResult(
        test_id=test_id,
        success=success,
        execution_logs=execution_logs,
        error_message=error_message,
        screenshot_path=screenshot_path,
        video_path=video_path,
        execution_duration=execution_duration,
        claude_version=claude_version,
    )
    session.add(db_obj)
    session.commit()
    session.refresh(db_obj)
    return db_obj


def get_web_test_result_by_test_id(
    *, session: Session, test_id: uuid.UUID
) -> WebTestResult | None:
    """
    Get the result for a web test.

    Args:
        session: Database session
        test_id: ID of the web test

    Returns:
        WebTestResult instance if found, None otherwise
    """
    statement = select(WebTestResult).where(WebTestResult.test_id == test_id)
    session_result = session.exec(statement).first()
    return session_result
