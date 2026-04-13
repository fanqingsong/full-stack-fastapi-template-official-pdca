import asyncio
import logging
import os
import subprocess
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from urllib.parse import urlparse
from typing import Optional, List

from sqlmodel import Session

from app.core.config import settings
from app.web_tests import crud
from app.web_tests.websocket import WebSocketManager

# Claude CLI output format tags
TAG_SCREENSHOT = "[SCREENSHOT]"
TAG_RESULT = "[RESULT]"
TAG_ERROR = "[ERROR]"
TAG_ACTION = "[ACTION]"
TAG_OBSERVE = "[OBSERVE]"

logger = logging.getLogger(__name__)


@dataclass
class ParsedResult:
    """Result of parsing Claude CLI output"""
    success: bool
    screenshots: List[str]
    error: Optional[str] = None


def check_claude_available() -> bool:
    """Check if Claude CLI is available on the system"""
    try:
        result = subprocess.run(
            ["claude", "--version"],
            capture_output=True,
            check=True,
            timeout=30
        )
        return result.returncode == 0
    except (subprocess.CalledProcessError, FileNotFoundError, subprocess.TimeoutExpired):
        return False


def validate_url(url: str) -> bool:
    """Validate that a URL is properly formatted and uses HTTP/HTTPS"""
    try:
        result = urlparse(url)
        return all([
            result.scheme in ('http', 'https'),
            result.netloc,
        ])
    except Exception:
        return False


def parse_claude_output(logs: str) -> ParsedResult:
    """Parse Claude CLI output to extract structured information"""
    result = ParsedResult(success=False, screenshots=[], error=None)

    for line in logs.split('\n'):
        line = line.strip()
        if line.startswith(TAG_SCREENSHOT):
            screenshot_path = line.split(TAG_SCREENSHOT)[1].strip()
            # Validate path exists and is secure
            if os.path.exists(screenshot_path) and os.path.isfile(screenshot_path):
                result.screenshots.append(screenshot_path)
        elif line.startswith(TAG_RESULT):
            result.success = 'PASS' in line.upper()
        elif line.startswith(TAG_ERROR):
            result.error = line.split(TAG_ERROR)[1].strip()

    return result


def construct_claude_prompt(url: str, description: str) -> str:
    """Construct the prompt to send to Claude CLI"""
    return f"""Use browser automation to test this website: {url}

Test description:
{description}

Please:
1. Navigate to the URL
2. Perform the tests described above
3. Report results clearly
4. Take screenshots of important steps

Format your response:
- Start each action with {TAG_ACTION}
- Start each observation with {TAG_OBSERVE}
- Start each screenshot with {TAG_SCREENSHOT} followed by the file path
- End with {TAG_RESULT}: PASS or FAIL
- If failed, include {TAG_ERROR}: description"""


async def execute_web_test(
    *,
    test_id: uuid.UUID,
    session: Session,
    websocket_manager: WebSocketManager
) -> None:
    """
    Execute a web test using Claude CLI in a background task.

    This async function:
    - Updates test status to "running"
    - Constructs Claude prompt
    - Starts asyncio subprocess for claude command
    - Streams stdout line-by-line with timeout
    - Parses output for screenshots, status, errors
    - Saves result to database
    - Updates test status to "completed" or "failed"
    - Sends WebSocket messages throughout
    - Handles errors and cleanup

    Args:
        test_id: UUID of the web test to execute
        session: Database session
        websocket_manager: WebSocket manager for real-time updates

    Returns:
        None (results are saved to database)
    """
    process = None
    logs_buffer = []
    started_at = None

    try:
        # Get the web test from database
        web_test = crud.get_web_test_by_id(session=session, web_test_id=test_id)
        if not web_test:
            logger.error(f"Web test {test_id} not found")
            return

        # Update status to running
        web_test = crud.update_web_test_status(
            session=session,
            db_web_test=web_test,
            status="running"
        )
        await websocket_manager.send_status(test_id, "running")

        # Construct Claude prompt
        prompt = construct_claude_prompt(web_test.url, web_test.description)

        # Log start time
        started_at = datetime.now(timezone.utc)

        # Start Claude CLI subprocess
        try:
            process = await asyncio.create_subprocess_exec(
                "claude",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                stdin=asyncio.subprocess.PIPE
            )

            # Send prompt to Claude
            process.stdin.write(prompt.encode())
            await process.stdin.drain()
            process.stdin.close()

        except OSError as e:
            logger.error(f"Failed to start Claude CLI: {e}")
            await websocket_manager.send_error(
                test_id,
                f"Failed to start Claude CLI: {e}"
            )
            web_test = crud.update_web_test_status(
                session=session,
                db_web_test=web_test,
                status="failed"
            )
            return

        # Stream output line-by-line with timeout
        timeout = settings.WEB_TEST_TIMEOUT
        start_time = asyncio.get_event_loop().time()

        while True:
            try:
                # Wait for output with 1-second timeout
                line = await asyncio.wait_for(
                    process.stdout.readline(),
                    timeout=1.0
                )

                if not line:
                    # EOF reached
                    break

                # Decode and log
                line_text = line.decode('utf-8', errors='ignore').strip()
                if line_text:
                    logs_buffer.append(line_text)
                    logger.info(f"[Test {test_id}] {line_text}")

                    # Send log via WebSocket
                    await websocket_manager.send_log(test_id, line_text)

                    # Check for screenshot tag
                    if line_text.startswith(TAG_SCREENSHOT):
                        screenshot_path = line_text.split(TAG_SCREENSHOT)[1].strip()
                        if os.path.exists(screenshot_path) and os.path.isfile(screenshot_path):
                            await websocket_manager.send_screenshot(test_id, screenshot_path)

                # Check for timeout
                elapsed = asyncio.get_event_loop().time() - start_time
                if elapsed > timeout:
                    logger.warning(f"Test {test_id} timed out after {elapsed} seconds")
                    raise asyncio.TimeoutError(f"Test execution exceeded {timeout} seconds")

            except asyncio.TimeoutError:
                logger.warning(f"Timeout reading output from test {test_id}")
                break
            except Exception as e:
                logger.error(f"Error reading output from test {test_id}: {e}")
                break

        # Wait for process to complete (with timeout)
        try:
            await asyncio.wait_for(process.wait(), timeout=5.0)
        except asyncio.TimeoutError:
            logger.warning(f"Process wait timeout for test {test_id}, terminating")
            process.terminate()
            try:
                await asyncio.wait_for(process.wait(), timeout=5.0)
            except asyncio.TimeoutError:
                process.kill()
                await process.wait()

        # Parse output
        logs_text = "\n".join(logs_buffer)
        parsed = parse_claude_output(logs_text)

        # Calculate duration
        completed_at = datetime.now(timezone.utc)
        duration = (completed_at - started_at).total_seconds() if started_at else None

        # Create result in database
        try:
            crud.create_web_test_result(
                session=session,
                test_id=test_id,
                success=parsed.success,
                execution_logs=logs_text,
                error_message=parsed.error,
                screenshot_path=parsed.screenshots[0] if parsed.screenshots else None,
                execution_duration=duration,
                claude_version="claude-cli"  # TODO: Get actual version
            )
        except Exception as e:
            logger.error(f"Failed to create result for test {test_id}: {e}")

        # Update test status
        final_status = "completed" if parsed.success else "failed"
        web_test = crud.update_web_test_status(
            session=session,
            db_web_test=web_test,
            status=final_status
        )

        # Send completion message
        await websocket_manager.send_complete(
            test_id,
            {
                "success": parsed.success,
                "duration": duration,
                "screenshot_count": len(parsed.screenshots)
            }
        )
        await websocket_manager.send_status(test_id, final_status)

    except Exception as e:
        logger.error(f"Unexpected error executing test {test_id}: {e}", exc_info=True)

        # Try to update status to failed
        try:
            web_test = crud.get_web_test_by_id(session=session, web_test_id=test_id)
            if web_test:
                web_test = crud.update_web_test_status(
                    session=session,
                    db_web_test=web_test,
                    status="failed"
                )
        except Exception as update_error:
            logger.error(f"Failed to update test status: {update_error}")

        # Send error message
        try:
            await websocket_manager.send_error(test_id, str(e))
        except Exception as ws_error:
            logger.error(f"Failed to send error via WebSocket: {ws_error}")

    finally:
        # Ensure cleanup
        if process and process.returncode is None:
            try:
                process.terminate()
                await asyncio.wait_for(process.wait(), timeout=5.0)
            except Exception:
                process.kill()
                await process.wait()

        # Always disconnect WebSocket (even if no connection was active)
        websocket_manager.disconnect(test_id)

        logger.info(f"Test {test_id} execution completed")
