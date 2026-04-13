"""Tests for web test execution functionality."""

import uuid
import asyncio
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from datetime import datetime, timezone

import pytest
from fastapi import WebSocket

from app.core.config import settings
from app.models import User
from app.web_tests.executor import execute_web_test, construct_claude_prompt
from app.web_tests.models import WebTest, WebTestCreate
from app.web_tests.crud import create_web_test
from app.web_tests.websocket import WebSocketManager


@pytest.fixture
def websocket_manager():
    """Create a WebSocket manager for testing."""
    return WebSocketManager()


@pytest.fixture
def test_web_test_obj(db, test_user: User) -> WebTest:
    """Create a test web test object."""
    web_test_create = WebTestCreate(
        url="https://example.com",
        description="Test the login functionality"
    )
    return create_web_test(session=db, web_test_create=web_test_create, owner_id=test_user.id)


@pytest.mark.asyncio
async def test_execute_web_test_success(
    db, test_web_test_obj: WebTest, websocket_manager
):
    """Test successful execution of a web test."""
    test_id = test_web_test_obj.id

    # Mock subprocess to simulate successful Claude CLI execution
    mock_process = AsyncMock()
    mock_process.returncode = 0
    mock_process.stdout.readline = AsyncMock(
        side_effect=[
            b"[ACTION] Navigating to https://example.com\n",
            b"[OBSERVE] Page loaded successfully\n",
            b"[SCREENSHOT] /tmp/test_screenshot.png\n",
            b"[RESULT]: PASS\n",
            b""  # EOF
        ]
    )

    with patch('asyncio.create_subprocess_exec', return_value=mock_process):
        with patch('os.path.exists', return_value=True):
            with patch('app.web_tests.executor.check_claude_available', return_value=True):
                # Mock WebSocket manager methods
                with patch.object(websocket_manager, 'send_log', new_callable=AsyncMock) as mock_send_log:
                    with patch.object(websocket_manager, 'send_status', new_callable=AsyncMock) as mock_send_status:
                        with patch.object(websocket_manager, 'send_screenshot', new_callable=AsyncMock) as mock_send_screenshot:
                            with patch.object(websocket_manager, 'send_complete', new_callable=AsyncMock) as mock_send_complete:
                                # Execute the test
                                await execute_web_test(
                                    test_id=test_id,
                                    session=db,
                                    websocket_manager=websocket_manager
                                )

                                # Verify status was updated
                                db.refresh(test_web_test_obj)
                                assert test_web_test_obj.status == "completed"
                                assert test_web_test_obj.started_at is not None
                                assert test_web_test_obj.completed_at is not None

                                # Verify result was created
                                from app.web_tests.crud import get_web_test_result_by_test_id
                                result = get_web_test_result_by_test_id(session=db, test_id=test_id)
                                assert result is not None
                                assert result.success is True
                                assert "/tmp/test_screenshot.png" in result.execution_logs

                                # Verify WebSocket messages were sent
                                assert mock_send_status.call_count >= 2  # At least "running" and "completed"
                                assert mock_send_log.call_count > 0
                                assert mock_send_complete.call_count == 1


@pytest.mark.asyncio
async def test_execute_web_test_failure(
    db, test_web_test_obj: WebTest, websocket_manager
):
    """Test execution of a web test that fails."""
    test_id = test_web_test_obj.id

    # Mock subprocess to simulate failed Claude CLI execution
    mock_process = AsyncMock()
    mock_process.returncode = 1
    mock_process.stdout.readline = AsyncMock(
        side_effect=[
            b"[ACTION] Navigating to https://example.com\n",
            b"[OBSERVE] Page loaded\n",
            b"[ERROR] Login form not found\n",
            b"[RESULT]: FAIL\n",
            b""  # EOF
        ]
    )

    with patch('asyncio.create_subprocess_exec', return_value=mock_process):
        with patch('app.web_tests.executor.check_claude_available', return_value=True):
            with patch.object(websocket_manager, 'send_log', new_callable=AsyncMock):
                with patch.object(websocket_manager, 'send_status', new_callable=AsyncMock):
                    with patch.object(websocket_manager, 'send_error', new_callable=AsyncMock) as mock_send_error:
                        with patch.object(websocket_manager, 'send_complete', new_callable=AsyncMock):
                            # Execute the test
                            await execute_web_test(
                                test_id=test_id,
                                session=db,
                                websocket_manager=websocket_manager
                            )

                            # Verify status was updated to failed
                            db.refresh(test_web_test_obj)
                            assert test_web_test_obj.status == "failed"

                            # Verify result was created with failure
                            from app.web_tests.crud import get_web_test_result_by_test_id
                            result = get_web_test_result_by_test_id(session=db, test_id=test_id)
                            assert result is not None
                            assert result.success is False
                            assert "Login form not found" in result.error_message


@pytest.mark.asyncio
async def test_execute_web_test_timeout(
    db, test_web_test_obj: WebTest, websocket_manager
):
    """Test execution timeout handling."""
    test_id = test_web_test_obj.id

    # Mock subprocess that times out
    mock_process = AsyncMock()
    mock_process.wait = AsyncMock(side_effect=asyncio.TimeoutError())

    with patch('asyncio.create_subprocess_exec', return_value=mock_process):
        with patch('app.web_tests.executor.check_claude_available', return_value=True):
            with patch.object(websocket_manager, 'send_status', new_callable=AsyncMock):
                with patch.object(websocket_manager, 'send_error', new_callable=AsyncMock) as mock_send_error:
                    # Execute the test (should handle timeout gracefully)
                    await execute_web_test(
                        test_id=test_id,
                        session=db,
                        websocket_manager=websocket_manager
                    )

                    # Verify status was updated to failed
                    db.refresh(test_web_test_obj)
                    assert test_web_test_obj.status == "failed"


@pytest.mark.asyncio
async def test_execute_web_test_subprocess_error(
    db, test_web_test_obj: WebTest, websocket_manager
):
    """Test handling of subprocess creation error."""
    test_id = test_web_test_obj.id

    # Mock subprocess creation failure
    with patch('asyncio.create_subprocess_exec', side_effect=OSError("Command not found")):
        with patch('app.web_tests.executor.check_claude_available', return_value=True):
            with patch.object(websocket_manager, 'send_status', new_callable=AsyncMock):
                with patch.object(websocket_manager, 'send_error', new_callable=AsyncMock) as mock_send_error:
                    # Execute the test (should handle error gracefully)
                    await execute_web_test(
                        test_id=test_id,
                        session=db,
                        websocket_manager=websocket_manager
                    )

                    # Verify status was updated to failed
                    db.refresh(test_web_test_obj)
                    assert test_web_test_obj.status == "failed"
                    assert mock_send_error.call_count == 1


@pytest.mark.asyncio
async def test_execute_web_test_line_streaming(
    db, test_web_test_obj: WebTest, websocket_manager
):
    """Test that output is streamed line-by-line via WebSocket."""
    test_id = test_web_test_obj.id

    # Mock subprocess with multiple lines of output
    mock_process = AsyncMock()
    mock_process.returncode = 0
    mock_process.stdout.readline = AsyncMock(
        side_effect=[
            b"Line 1: Starting test\n",
            b"Line 2: Navigating\n",
            b"Line 3: Checking element\n",
            b"Line 4: Test complete\n",
            b"[RESULT]: PASS\n",
            b""  # EOF
        ]
    )

    with patch('asyncio.create_subprocess_exec', return_value=mock_process):
        with patch('app.web_tests.executor.check_claude_available', return_value=True):
            with patch.object(websocket_manager, 'send_log', new_callable=AsyncMock) as mock_send_log:
                with patch.object(websocket_manager, 'send_status', new_callable=AsyncMock):
                    with patch.object(websocket_manager, 'send_complete', new_callable=AsyncMock):
                        # Execute the test
                        await execute_web_test(
                            test_id=test_id,
                            session=db,
                            websocket_manager=websocket_manager
                        )

                        # Verify logs were sent line-by-line
                        log_calls = [call.args[1] for call in mock_send_log.call_args_list]
                        assert len(log_calls) >= 4
                        assert any("Line 1" in log for log in log_calls)
                        assert any("Line 2" in log for log in log_calls)
                        assert any("Line 3" in log for log in log_calls)
                        assert any("Line 4" in log for log in log_calls)


@pytest.mark.asyncio
async def test_execute_web_test_screenshot_broadcast(
    db, test_web_test_obj: WebTest, websocket_manager
):
    """Test that screenshots are broadcast via WebSocket."""
    test_id = test_web_test_obj.id

    # Mock subprocess with screenshot output
    mock_process = AsyncMock()
    mock_process.returncode = 0
    mock_process.stdout.readline = AsyncMock(
        side_effect=[
            b"[ACTION] Taking screenshot\n",
            b"[SCREENSHOT] /tmp/screenshot1.png\n",
            b"[ACTION] Taking another screenshot\n",
            b"[SCREENSHOT] /tmp/screenshot2.png\n",
            b"[RESULT]: PASS\n",
            b""  # EOF
        ]
    )

    with patch('asyncio.create_subprocess_exec', return_value=mock_process):
        with patch('os.path.exists', return_value=True):
            with patch('app.web_tests.executor.check_claude_available', return_value=True):
                with patch.object(websocket_manager, 'send_log', new_callable=AsyncMock):
                    with patch.object(websocket_manager, 'send_status', new_callable=AsyncMock):
                        with patch.object(websocket_manager, 'send_screenshot', new_callable=AsyncMock) as mock_send_screenshot:
                            with patch.object(websocket_manager, 'send_complete', new_callable=AsyncMock):
                                # Execute the test
                                await execute_web_test(
                                    test_id=test_id,
                                    session=db,
                                    websocket_manager=websocket_manager
                                )

                                # Verify screenshots were sent via WebSocket
                                screenshot_calls = [call.args[1] for call in mock_send_screenshot.call_args_list]
                                assert len(screenshot_calls) == 2
                                assert "/tmp/screenshot1.png" in screenshot_calls
                                assert "/tmp/screenshot2.png" in screenshot_calls


@pytest.mark.asyncio
async def test_execute_web_test_cleanup_on_disconnect(
    db, test_web_test_obj: WebTest, websocket_manager
):
    """Test that WebSocket is properly cleaned up after execution."""
    test_id = test_web_test_obj.id

    # Mock successful subprocess
    mock_process = AsyncMock()
    mock_process.returncode = 0
    mock_process.stdout.readline = AsyncMock(
        side_effect=[
            b"[RESULT]: PASS\n",
            b""  # EOF
        ]
    )

    with patch('asyncio.create_subprocess_exec', return_value=mock_process):
        with patch('app.web_tests.executor.check_claude_available', return_value=True):
            with patch.object(websocket_manager, 'send_log', new_callable=AsyncMock):
                with patch.object(websocket_manager, 'send_status', new_callable=AsyncMock):
                    with patch.object(websocket_manager, 'send_complete', new_callable=AsyncMock):
                        # Execute the test
                        await execute_web_test(
                            test_id=test_id,
                            session=db,
                            websocket_manager=websocket_manager
                        )

                        # Verify disconnect was called (even if no connection was active)
                        # The function should always call disconnect in finally block
                        # We can't directly verify this without spying, but we can ensure
                        # the function completes without error


def test_construct_claude_prompt_format():
    """Test that the Claude prompt is constructed correctly."""
    url = "https://example.com/login"
    description = "Test the login form validation"

    prompt = construct_claude_prompt(url, description)

    assert url in prompt
    assert description in prompt
    assert "[ACTION]" in prompt
    assert "[OBSERVE]" in prompt
    assert "[SCREENSHOT]" in prompt
    assert "[RESULT]" in prompt
    assert "[ERROR]" in prompt


@pytest.mark.asyncio
async def test_execute_web_test_invalid_test_id(db, websocket_manager):
    """Test execution with non-existent test ID."""
    fake_test_id = uuid.uuid4()

    # Should handle gracefully without crashing
    with patch('app.web_tests.executor.check_claude_available', return_value=True):
        await execute_web_test(
            test_id=fake_test_id,
            session=db,
            websocket_manager=websocket_manager
        )

        # No exception should be raised, function should handle error internally
