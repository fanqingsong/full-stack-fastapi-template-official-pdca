import os
import subprocess
from dataclasses import dataclass
from urllib.parse import urlparse
from typing import Optional, List

# Claude CLI output format tags
TAG_SCREENSHOT = "[SCREENSHOT]"
TAG_RESULT = "[RESULT]"
TAG_ERROR = "[ERROR]"
TAG_ACTION = "[ACTION]"
TAG_OBSERVE = "[OBSERVE]"


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
