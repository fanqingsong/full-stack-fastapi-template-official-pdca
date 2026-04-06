"""Tests for PDCA State definitions."""

import pytest
from datetime import datetime
from app.pdca.state import PDCAState


def test_pdca_state_minimal():
    """测试最小 PDCAState 创建"""
    state: PDCAState = {
        "id": "test-123",
        "parent_id": None,
        "phase": "plan",
        "goal": "Test goal",
        "plan_details": {},
        "agent_type": "openai",
        "agent_input": {},
        "execution_result": None,
        "check_criteria": {},
        "check_result": None,
        "passed": None,
        "approval_status": None,
        "improvement_actions": [],
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow(),
        "error": None,
    }

    assert state["id"] == "test-123"
    assert state["phase"] == "plan"
    assert state["parent_id"] is None


def test_pdca_state_with_parent():
    """测试带父循环的 PDCAState"""
    state: PDCAState = {
        "id": "child-123",
        "parent_id": "parent-456",
        "phase": "do",
        "goal": "Child goal",
        "plan_details": {},
        "agent_type": "openai",
        "agent_input": {"prompt": "test"},
        "execution_result": None,
        "check_criteria": {},
        "check_result": None,
        "passed": None,
        "approval_status": None,
        "improvement_actions": [],
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow(),
        "error": None,
    }

    assert state["parent_id"] == "parent-456"
    assert state["phase"] == "do"


