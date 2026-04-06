"""Tests for PDCA database models."""

import pytest
from datetime import datetime
from sqlmodel import Session
from app.pdca.models import PDCACycle, PDCACycleCreate, AgentConfig
from app.models import User


def test_create_pdca_cycle(db: Session, test_user: User):
    """测试创建PDCA循环"""
    cycle_data = PDCACycleCreate(
        name="Test PDCA Cycle",
        description="Test description",
        goal="Test goal",
        agent_type="openai",
        agent_input={"prompt": "test prompt"}
    )

    cycle = PDCACycle(
        **cycle_data.model_dump(),
        owner_id=test_user.id
    )

    db.add(cycle)
    db.commit()
    db.refresh(cycle)

    assert cycle.id is not None
    assert cycle.name == "Test PDCA Cycle"
    assert cycle.phase == "plan"
    assert cycle.status == "pending"
    assert cycle.owner_id == test_user.id


def test_pdca_cycle_with_parent(db: Session, test_user: User):
    """测试带父循环的PDCA循环"""
    # 创建父循环
    parent = PDCACycle(
        name="Parent Cycle",
        goal="Parent goal",
        agent_type="openai",
        agent_input={},
        owner_id=test_user.id
    )
    db.add(parent)
    db.commit()
    db.refresh(parent)

    # 创建子循环
    child = PDCACycle(
        name="Child Cycle",
        goal="Child goal",
        agent_type="openai",
        agent_input={},
        parent_id=parent.id,
        owner_id=test_user.id
    )
    db.add(child)
    db.commit()
    db.refresh(child)

    assert child.parent_id == parent.id
    assert len(parent.children) == 1
    assert parent.children[0].id == child.id


def test_create_agent_config(db: Session, test_user: User):
    """测试创建Agent配置"""
    config = AgentConfig(
        name="OpenAI GPT-4",
        agent_type="openai",
        description="GPT-4 model configuration",
        config={
            "model": "gpt-4",
            "temperature": 0.7,
            "max_tokens": 2000
        },
        owner_id=test_user.id
    )

    db.add(config)
    db.commit()
    db.refresh(config)

    assert config.id is not None
    assert config.name == "OpenAI GPT-4"
    assert config.agent_type == "openai"
    assert config.config["model"] == "gpt-4"
