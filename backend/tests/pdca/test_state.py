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


def test_pdca_state_all_phases():
    """测试所有阶段的 PDCAState"""
    phases = ["plan", "do", "check", "act", "completed", "failed"]
    
    for phase in phases:
        state: PDCAState = {
            "id": f"test-{phase}",
            "parent_id": None,
            "phase": phase,
            "goal": f"Test goal for {phase}",
            "plan_details": {"strategy": "test"},
            "agent_type": "openai",
            "agent_input": {"prompt": f"test {phase}"},
            "execution_result": None if phase != "do" else {"result": "success"},
            "check_criteria": {"criteria": "test"},
            "check_result": None if phase not in ["check", "act"] else {"score": 90},
            "passed": None if phase not in ["check", "act"] else True,
            "approval_status": None if phase not in ["check", "act"] else "approved",
            "improvement_actions": [],
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
            "error": None,
        }
        
        assert state["phase"] == phase
        assert state["id"] == f"test-{phase}"


def test_pdca_state_approval_statuses():
    """测试所有审批状态的 PDCAState"""
    approval_statuses = ["pending", "approved", "rejected", "auto_approved", "auto_rejected"]
    
    for status in approval_statuses:
        state: PDCAState = {
            "id": f"test-approval-{status}",
            "parent_id": None,
            "phase": "check",
            "goal": "Test goal",
            "plan_details": {},
            "agent_type": "openai",
            "agent_input": {},
            "execution_result": None,
            "check_criteria": {},
            "check_result": {"score": 80},
            "passed": True,
            "approval_status": status,
            "improvement_actions": [],
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
            "error": None,
        }
        
        assert state["approval_status"] == status


def test_pdca_state_with_improvement_actions():
    """测试包含改进措施的 PDCAState"""
    improvement_actions = [
        {"action": "Improve process", "priority": "high"},
        {"action": "Update documentation", "priority": "medium"}
    ]
    
    state: PDCAState = {
        "id": "test-improvement",
        "parent_id": None,
        "phase": "act",
        "goal": "Test goal with improvements",
        "plan_details": {},
        "agent_type": "openai",
        "agent_input": {},
        "execution_result": None,
        "check_criteria": {},
        "check_result": {"score": 70},
        "passed": False,
        "approval_status": "rejected",
        "improvement_actions": improvement_actions,
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow(),
        "error": "Some error occurred",
    }

    assert state["improvement_actions"] == improvement_actions
    assert len(state["improvement_actions"]) == 2
    assert state["error"] == "Some error occurred"


def test_pdca_state_type_safety():
    """测试类型安全性 - 确保所有字段都有正确的类型"""
    state: PDCAState = {
        "id": "test-type-safety",
        "parent_id": "parent-id",
        "phase": "plan",
        "goal": "Test goal",
        "plan_details": {"key": "value", "number": 42},
        "agent_type": "openai",
        "agent_input": {"prompt": "test", "temperature": 0.7},
        "execution_result": None,
        "check_criteria": {"criteria": "quality", "threshold": 80},
        "check_result": None,
        "passed": None,
        "approval_status": None,
        "improvement_actions": [
            {"action": "Action 1", "priority": "high"},
            {"action": "Action 2", "priority": "low"}
        ],
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow(),
        "error": None,
    }

    # 验证嵌套字典的类型
    assert isinstance(state["plan_details"], dict)
    assert isinstance(state["agent_input"], dict)
    assert isinstance(state["improvement_actions"], list)
    
    # 验证嵌套内容的类型
    assert isinstance(state["improvement_actions"][0], dict)
    assert isinstance(state["improvement_actions"][0]["action"], str)
    assert isinstance(state["improvement_actions"][0]["priority"], str)