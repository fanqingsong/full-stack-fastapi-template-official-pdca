"""Tests for PDCA engine."""

import pytest
from unittest.mock import Mock, patch
from datetime import datetime

from app.pdca.engine import PDCAEngine
from app.pdca.state import PDCAState


@pytest.fixture
def pdca_engine(db):
    """Create PDCAEngine fixture."""
    return PDCAEngine(db)


def test_plan_node(pdca_engine, test_pdca_cycle):
    """Test plan node execution."""
    # Create full PDCAState dict with all required fields
    state: PDCAState = {
        "id": str(test_pdca_cycle.id),
        "parent_id": None,
        "phase": "plan",
        "goal": "Test goal",
        "plan_details": {},
        "agent_type": "openai",
        "agent_input": {"prompt": "test prompt"},
        "execution_result": None,
        "check_criteria": {},
        "check_result": None,
        "passed": None,
        "approval_status": None,
        "improvement_actions": [],
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow(),
        "error": None
    }

    # Call plan node
    result = pdca_engine._plan_node(state)

    # Assertions
    assert result["phase"] == "plan"
    assert "plan_details" in result


def test_do_node_success(pdca_engine, test_pdca_cycle):
    """Test do node with successful agent execution."""
    # Create PDCAState with agent_input
    state: PDCAState = {
        "id": str(test_pdca_cycle.id),
        "parent_id": None,
        "phase": "do",
        "goal": "Test goal",
        "plan_details": {},
        "agent_type": "openai",
        "agent_input": {"prompt": "test prompt"},
        "execution_result": None,
        "check_criteria": {},
        "check_result": None,
        "passed": None,
        "approval_status": None,
        "improvement_actions": [],
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow(),
        "error": None
    }

    # Mock executor
    mock_executor = Mock()
    mock_executor.execute.return_value = {
        "status": "success",
        "output": "Test response"
    }

    # Patch AgentRegistry.get_executor to return mock
    with patch('app.pdca.engine.AgentRegistry.get_executor', return_value=mock_executor):
        result = pdca_engine._do_node(state)

    # Assertions
    assert result["phase"] == "do"
    assert result["execution_result"]["status"] == "success"


def test_check_node_passed(pdca_engine, test_pdca_cycle):
    """Test check node with passed execution."""
    # Create PDCAState with successful execution result
    state: PDCAState = {
        "id": str(test_pdca_cycle.id),
        "parent_id": None,
        "phase": "check",
        "goal": "Test goal",
        "plan_details": {},
        "agent_type": "openai",
        "agent_input": {"prompt": "test"},
        "execution_result": {"status": "success", "output": "Test output"},
        "check_criteria": {},
        "check_result": None,
        "passed": None,
        "approval_status": None,
        "improvement_actions": [],
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow(),
        "error": None
    }

    # Call check node
    result = pdca_engine._check_node(state)

    # Assertions
    assert result["phase"] == "check"
    assert result["passed"] is True
    assert result["approval_status"] == "auto_approved"


def test_should_continue_or_improve_continue(pdca_engine):
    """Test should_continue_or_improve returns continue when passed and approved."""
    state: PDCAState = {
        "id": "test-id",
        "parent_id": None,
        "phase": "check",
        "goal": "Test goal",
        "plan_details": {},
        "agent_type": "openai",
        "agent_input": {},
        "execution_result": {"status": "success"},
        "check_criteria": {},
        "check_result": {},
        "passed": True,
        "approval_status": "auto_approved",
        "improvement_actions": [],
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow(),
        "error": None
    }

    result = pdca_engine._should_continue_or_improve(state)

    assert result == "continue"


def test_should_continue_or_improve_act(pdca_engine):
    """Test should_continue_or_improve returns improve when failed."""
    state: PDCAState = {
        "id": "test-id",
        "parent_id": None,
        "phase": "check",
        "goal": "Test goal",
        "plan_details": {},
        "agent_type": "openai",
        "agent_input": {},
        "execution_result": {"status": "error"},
        "check_criteria": {},
        "check_result": {},
        "passed": False,
        "approval_status": "auto_rejected",
        "improvement_actions": [],
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow(),
        "error": None
    }

    result = pdca_engine._should_continue_or_improve(state)

    assert result == "improve"
