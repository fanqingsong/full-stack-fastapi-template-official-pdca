import uuid
import pytest
from unittest.mock import Mock, AsyncMock, patch

from app.web_tests.executor import (
    check_claude_available,
    validate_url,
    parse_claude_output,
    ParsedResult
)


def test_check_claude_available():
    """Test Claude CLI availability check"""
    with patch('subprocess.run') as mock_run:
        mock_run.return_value = Mock(returncode=0)
        assert check_claude_available() is True

        mock_run.side_effect = FileNotFoundError()
        assert check_claude_available() is False


def test_validate_url_valid():
    """Test URL validation with valid URLs"""
    assert validate_url("https://example.com") is True
    assert validate_url("http://test.com/path") is True
    assert validate_url("https://example.com:8080/test") is True


def test_validate_url_invalid():
    """Test URL validation with invalid URLs"""
    assert validate_url("not-a-url") is False
    assert validate_url("ftp://example.com") is False
    assert validate_url("") is False
    assert validate_url("example.com") is False


def test_parse_claude_output_success():
    """Test parsing Claude output for successful test"""
    logs = """
[ACTION] Navigating to https://example.com
[OBSERVE] Page loaded
[SCREENSHOT] /tmp/screenshot1.png
[RESULT]: PASS
"""
    result = parse_claude_output(logs)

    assert result.success is True
    assert len(result.screenshots) == 1
    assert result.screenshots[0] == "/tmp/screenshot1.png"
    assert result.error is None


def test_parse_claude_output_failure():
    """Test parsing Claude output for failed test"""
    logs = """
[ACTION] Navigating to https://example.com
[OBSERVE] Page loaded
[ERROR] Login form not found
[RESULT]: FAIL
"""
    result = parse_claude_output(logs)

    assert result.success is False
    assert result.error == "Login form not found"
