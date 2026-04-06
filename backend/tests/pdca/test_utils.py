"""Tests for PDCA utility functions."""

import pytest
from app.pdca.utils import (
    extract_execution_summary,
    calculate_cycle_progress,
    validate_agent_input,
    format_cycle_tree,
)
from app.pdca.models import PDCACycle


def test_extract_execution_summary_success():
    """Test extracting summary from successful execution result."""
    # Create result with status="success" and long output (>200 chars)
    long_output = "x" * 300  # 300 characters
    result = {
        "status": "success",
        "output": long_output,
    }

    summary = extract_execution_summary(result)

    # Assert summary starts with "Success:"
    assert summary.startswith("Success:")
    # Assert summary contains "..." (truncation indicator)
    assert "..." in summary
    # Assert summary is truncated to around 200 chars
    assert len(summary) < 220  # "Success: " + 200 chars + "..."


def test_extract_execution_summary_error():
    """Test extracting summary from failed execution result."""
    error_message = "Connection timeout"
    result = {
        "status": "error",
        "error": error_message,
    }

    summary = extract_execution_summary(result)

    # Assert error message is in summary
    assert error_message in summary
    assert summary.startswith("Error:")


def test_calculate_cycle_progress():
    """Test calculating cycle progress based on phase."""
    assert calculate_cycle_progress({"phase": "plan"}) == 25
    assert calculate_cycle_progress({"phase": "do"}) == 50
    assert calculate_cycle_progress({"phase": "check"}) == 75
    assert calculate_cycle_progress({"phase": "act"}) == 90
    assert calculate_cycle_progress({"phase": "completed"}) == 100
    assert calculate_cycle_progress({"phase": "failed"}) == 100
    assert calculate_cycle_progress({"phase": "unknown"}) == 0
    assert calculate_cycle_progress({}) == 25  # defaults to "plan"


def test_validate_agent_input_openai_valid():
    """Test validating valid OpenAI agent input."""
    input_data = {"prompt": "Test prompt"}
    is_valid, errors = validate_agent_input("openai", input_data)

    assert is_valid is True
    assert errors == []


def test_validate_agent_input_openai_invalid():
    """Test validating invalid OpenAI agent input."""
    input_data = {"model": "gpt-4"}  # Missing prompt
    is_valid, errors = validate_agent_input("openai", input_data)

    assert is_valid is False
    assert len(errors) == 1
    assert "prompt" in errors[0]


def test_validate_agent_input_http_valid():
    """Test validating valid HTTP request agent input."""
    input_data = {"url": "https://example.com", "method": "GET"}
    is_valid, errors = validate_agent_input("http_request", input_data)

    assert is_valid is True
    assert errors == []


def test_format_cycle_tree(db, test_user):
    """Test formatting cycles into tree structure."""
    # Create parent cycle
    parent = PDCACycle(
        name="Parent Cycle",
        goal="Parent goal",
        agent_type="openai",
        agent_input={"prompt": "test"},
        owner_id=test_user.id,
        phase="plan",
        status="pending",
    )
    db.add(parent)
    db.commit()
    db.refresh(parent)

    # Create child cycle
    child = PDCACycle(
        name="Child",
        goal="Child goal",
        agent_type="openai",
        agent_input={"prompt": "test"},
        owner_id=test_user.id,
        parent_id=parent.id,
        phase="do",
        status="running",
    )
    db.add(child)
    db.commit()
    db.refresh(child)

    # Format cycles into tree
    cycles = [parent, child]
    tree = format_cycle_tree(cycles)

    # Assert tree has 1 root
    assert len(tree) == 1

    # Assert root has 1 child
    root = tree[0]
    assert len(root["children"]) == 1

    # Assert child name is "Child"
    child_node = root["children"][0]
    assert child_node["name"] == "Child"
    assert child_node["phase"] == "do"
    assert child_node["status"] == "running"

    # Assert root properties
    assert root["name"] == "Parent Cycle"
    assert root["phase"] == "plan"
    assert root["status"] == "pending"
