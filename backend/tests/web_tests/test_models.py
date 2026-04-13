import uuid
from datetime import datetime, timezone

from app.web_tests.models import WebTest, WebTestResult
from sqlmodel import Session
from app.models import User


def test_web_test_creation(session: Session, test_user: User):
    """Test creating a WebTest instance"""
    test = WebTest(
        url="https://example.com",
        description="Test the login functionality",
        status="pending",
        owner_id=test_user.id,
    )
    session.add(test)
    session.commit()
    session.refresh(test)

    assert test.id is not None
    assert test.url == "https://example.com"
    assert test.status == "pending"
    assert test.owner_id == test_user.id
    assert test.created_at is not None
    assert test.started_at is None
    assert test.completed_at is None


def test_web_test_result_creation(session: Session, test_user: User):
    """Test creating a WebTestResult instance"""
    # First create a test
    test = WebTest(
        url="https://example.com",
        description="Test description",
        status="completed",
        owner_id=test_user.id,
    )
    session.add(test)
    session.commit()
    session.refresh(test)

    # Create result
    result = WebTestResult(
        test_id=test.id,
        success=True,
        execution_logs="Test execution completed successfully",
        execution_duration=45.5,
    )
    session.add(result)
    session.commit()
    session.refresh(result)

    assert result.id is not None
    assert result.test_id == test.id
    assert result.success is True
    assert result.execution_logs is not None
    assert result.execution_duration == 45.5


def test_web_test_status_validation():
    """Test that only valid statuses are allowed"""
    valid_statuses = ["pending", "running", "completed", "failed", "cancelled"]
    test = WebTest(
        url="https://example.com",
        description="Test",
        status="pending",
        owner_id=uuid.uuid4(),
    )
    assert test.status in valid_statuses
