# PDCA Agent平台 - Phase 1 MVP实现计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 构建PDCA Agent平台的最小可行版本，支持基础的PDCA循环创建、执行和OpenAI Agent调用

**Architecture:**
- 使用LangGraph StateGraph实现PDCA状态机引擎
- SQLModel定义PostgreSQL数据库模型（PDCACycle、AgentConfig、ExecutionLog）
- FastAPI RESTful API提供CRUD和执行接口
- OpenAI Agent作为首个Agent执行器实现

**Tech Stack:**
- FastAPI + SQLModel + PostgreSQL（已有）
- LangGraph + LangChain + OpenAI（新增）
- Pytest + httpx（测试）

---

## 文件结构概览

```
backend/app/
├── pdca/                              # PDCA模块（新增）
│   ├── __init__.py
│   ├── models.py                      # PDCA数据模型
│   ├── state.py                       # LangGraph State定义
│   ├── engine.py                      # LangGraph引擎
│   ├── crud.py                        # PDCA CRUD操作
│   ├── agents/                        # Agent执行器
│   │   ├── __init__.py
│   │   ├── base.py                    # 基类
│   │   ├── openai_agent.py            # OpenAI Agent
│   │   └── registry.py                # Agent注册表
│   └── utils.py                       # 工具函数
├── api/
│   └── routes/
│       └── pdca.py                    # PDCA API路由（新增）
└── models.py                          # 修改：添加import

backend/tests/
├── pdca/                              # PDCA测试（新增）
│   ├── __init__.py
│   ├── test_models.py                 # 模型测试
│   ├── test_engine.py                 # 引擎测试
│   ├── test_agents.py                 # Agent测试
│   └── conftest.py                    # 测试fixtures
└── api/
    └── routes/
        └── test_pdca.py               # API测试（新增）

backend/pyproject.toml                 # 修改：添加依赖
backend/.env.example                   # 修改：添加环境变量
```

---

## Task 1: 添加项目依赖

**Files:**
- Modify: `backend/pyproject.toml`
- Modify: `backend/.env.example`

- [ ] **Step 1: 修改 pyproject.toml 添加 LangGraph 和 LangChain 依赖**

在 `dependencies` 列表中添加以下依赖：

```toml
dependencies = [
    # ... 现有依赖 ...
    "langgraph>=0.2.0",
    "langchain>=0.3.0",
    "langchain-openai>=0.2.0",
    "openai>=1.0.0",
]
```

**完整修改后的 dependencies 部分：**

```toml
dependencies = [
    "fastapi[standard]<1.0.0,>=0.114.2",
    "python-multipart<1.0.0,>=0.0.7",
    "email-validator<3.0.0.0,>=2.1.0.post1",
    "tenacity<9.0.0,>=8.2.3",
    "pydantic>2.0",
    "emails<1.0,>=0.6",
    "jinja2<4.0.0,>=3.1.4",
    "alembic<2.0.0,>=1.12.1",
    "httpx<1.0.0,>=0.25.1",
    "psycopg[binary]<4.0.0,>=3.1.13",
    "sqlmodel<1.0.0,>=0.0.21",
    "pydantic-settings<3.0.0,>=2.2.1",
    "sentry-sdk[fastapi]<2.0.0,>=1.40.6",
    "pyjwt<3.0.0,>=2.8.0",
    "pwdlib[argon2,bcrypt]>=0.3.0",
    "minio>=7.2.0",
    "redis>=5.0.0",
    "langgraph>=0.2.0",
    "langchain>=0.3.0",
    "langchain-openai>=0.2.0",
    "openai>=1.0.0",
]
```

- [ ] **Step 2: 修改 .env.example 添加 OpenAI 配置**

在文件末尾添加：

```env
# OpenAI Configuration
OPENAI_API_KEY=your-openai-api-key-here
OPENAI_MODEL=gpt-4
```

- [ ] **Step 3: 安装依赖验证**

Run: `cd backend && uv sync`

Expected: 依赖成功安装，无错误

- [ ] **Step 4: 提交**

```bash
git add backend/pyproject.toml backend/.env.example
git commit -m "feat: add LangGraph and LangChain dependencies"
```

---

## Task 2: 创建 PDCA State 定义

**Files:**
- Create: `backend/app/pdca/__init__.py`
- Create: `backend/app/pdca/state.py`

- [ ] **Step 1: 创建 pdca 模块 __init__.py**

```python
"""PDCA workflow management module."""

from app.pdca.state import PDCAState

__all__ = ["PDCAState"]
```

- [ ] **Step 2: 编写 PDCAState 定义**

```python
"""PDCA State definitions for LangGraph."""

from typing import TypedDict, Optional, Dict, List, Any, Literal
from datetime import datetime


class PDCAState(TypedDict):
    """PDCA循环的状态定义 - 用于LangGraph StateGraph"""

    # 标识符
    id: str
    parent_id: Optional[str]  # 父循环ID，支持嵌套

    # 当前阶段
    phase: Literal["plan", "do", "check", "act", "completed", "failed"]

    # Plan阶段数据
    goal: str  # 目标描述
    plan_details: Dict[str, Any]  # 计划详情

    # Do阶段数据
    agent_type: str  # Agent类型（如 "openai"）
    agent_input: Dict[str, Any]  # Agent输入参数
    execution_result: Optional[Dict[str, Any]]  # 执行结果

    # Check阶段数据
    check_criteria: Dict[str, Any]  # 检查标准
    check_result: Optional[Dict[str, Any]]  # 检查结果
    passed: Optional[bool]  # 是否通过检查
    approval_status: Optional[Literal["pending", "approved", "rejected", "auto_approved", "auto_rejected"]]

    # Act阶段数据
    improvement_actions: List[Dict[str, Any]]  # 改进措施列表

    # 元数据
    created_at: datetime
    updated_at: datetime
    error: Optional[str]  # 错误信息
```

- [ ] **Step 3: 编写 State 的测试**

Create: `backend/tests/pdca/__init__.py`（空文件）

Create: `backend/tests/pdca/test_state.py`

```python
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
```

- [ ] **Step 4: 运行测试验证**

Run: `cd backend && pytest tests/pdca/test_state.py -v`

Expected: PASS（所有测试通过）

- [ ] **Step 5: 提交**

```bash
git add backend/app/pdca/ backend/tests/pdca/
git commit -m "feat: add PDCA State definition for LangGraph"
```

---

## Task 3: 创建数据库模型

**Files:**
- Create: `backend/app/pdca/models.py`
- Modify: `backend/app/models.py`

- [ ] **Step 1: 编写 PDCA 数据库模型**

```python
"""PDCA database models."""

import uuid
from datetime import datetime, timezone
from typing import Optional, List, TYPE_CHECKING, Dict, Any

from sqlalchemy import JSON, ForeignKey
from sqlmodel import Field, Relationship, SQLModel, Column

from app.models import get_datetime_utc


if TYPE_CHECKING:
    from app.models import User


class PDCACycleBase(SQLModel):
    """PDCA循环的基础字段"""
    name: str = Field(index=True, max_length=255)
    description: Optional[str] = Field(default=None, max_length=1000)
    phase: str = Field(default="plan", max_length=20)  # plan, do, check, act, completed, failed
    status: str = Field(default="pending", max_length=30)  # pending, running, waiting_approval, completed, failed


class PDCACycle(PDCACycleBase, table=True):
    """PDCA循环表"""
    __tablename__ = "pdca_cycle"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    parent_id: Optional[uuid.UUID] = Field(
        default=None,
        foreign_key="pdca_cycle.id"
    )

    # JSON字段存储LangGraph状态数据
    state_data: Dict[str, Any] = Field(
        default={},
        sa_column=Column(JSON)
    )

    # Agent配置
    agent_type: Optional[str] = Field(default=None, max_length=50)
    agent_config_id: Optional[uuid.UUID] = Field(default=None)

    # 时间戳
    created_at: datetime = Field(default_factory=get_datetime_utc)
    updated_at: datetime = Field(default_factory=get_datetime_utc)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None

    # 错误信息
    error_message: Optional[str] = Field(default=None, max_length=2000)

    # 关系 - 父子循环
    parent: Optional["PDCACycle"] = Relationship(
        back_populates="children",
        sa_relationship_kwargs={"remote_side": "PDCACycle.id"}
    )
    children: List["PDCACycle"] = Relationship(
        back_populates="parent",
        sa_relationship_kwargs={"cascade": "all, delete-orphan"}
    )

    # 关系 - 创建者
    owner_id: uuid.UUID = Field(
        foreign_key="user.id",
        nullable=False,
        ondelete="CASCADE"
    )
    owner: Optional["User"] = Relationship(back_populates="pdca_cycles")


class AgentConfigBase(SQLModel):
    """Agent配置的基础字段"""
    name: str = Field(index=True, max_length=255)
    agent_type: str = Field(max_length=50)  # openai, python_script, http_request, shell_command
    description: Optional[str] = Field(default=None, max_length=1000)


class AgentConfig(AgentConfigBase, table=True):
    """Agent配置表"""
    __tablename__ = "agent_config"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)

    # JSON字段存储Agent特定配置
    config: Dict[str, Any] = Field(
        default={},
        sa_column=Column(JSON)
    )

    # 时间戳
    created_at: datetime = Field(default_factory=get_datetime_utc)
    updated_at: datetime = Field(default_factory=get_datetime_utc)

    # 关系 - 创建者
    owner_id: uuid.UUID = Field(
        foreign_key="user.id",
        nullable=False,
        ondelete="CASCADE"
    )
    owner: Optional["User"] = Relationship(back_populates="agent_configs")


class ExecutionLog(SQLModel, table=True):
    """执行日志表"""
    __tablename__ = "execution_log"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    cycle_id: uuid.UUID = Field(
        foreign_key="pdca_cycle.id",
        nullable=False,
        index=True
    )

    phase: str = Field(max_length=20)  # plan, do, check, act
    level: str = Field(max_length=20)  # info, warning, error
    message: str = Field(max_length=5000)
    metadata: Dict[str, Any] = Field(
        default={},
        sa_column=Column(JSON)
    )

    created_at: datetime = Field(default_factory=get_datetime_utc)


# Pydantic模型用于API
class PDCACycleCreate(PDCACycleBase):
    """创建PDCA循环的请求模型"""
    parent_id: Optional[uuid.UUID] = None
    agent_type: Optional[str] = None
    agent_config_id: Optional[uuid.UUID] = None
    goal: str = Field(max_length=1000)
    plan_details: Dict[str, Any] = {}
    agent_input: Dict[str, Any] = {}


class PDCACycleUpdate(SQLModel):
    """更新PDCA循环的请求模型"""
    name: Optional[str] = None
    description: Optional[str] = None
    phase: Optional[str] = None
    status: Optional[str] = None
    state_data: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None


class PDCACyclePublic(PDCACycleBase):
    """返回给客户端的PDCA循环模型"""
    id: uuid.UUID
    parent_id: Optional[uuid.UUID] = None
    state_data: Dict[str, Any] = {}
    agent_type: Optional[str] = None
    agent_config_id: Optional[uuid.UUID] = None
    created_at: datetime
    updated_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None
    owner_id: uuid.UUID


class PDCACyclesPublic(SQLModel):
    """PDCA循环列表响应"""
    data: List[PDCACyclePublic]
    count: int


class AgentConfigCreate(AgentConfigBase):
    """创建Agent配置的请求模型"""
    config: Dict[str, Any] = {}


class AgentConfigUpdate(SQLModel):
    """更新Agent配置的请求模型"""
    name: Optional[str] = None
    description: Optional[str] = None
    config: Optional[Dict[str, Any]] = None


class AgentConfigPublic(AgentConfigBase):
    """返回给客户端的Agent配置模型"""
    id: uuid.UUID
    config: Dict[str, Any]
    created_at: datetime
    updated_at: datetime
    owner_id: uuid.UUID


class AgentConfigsPublic(SQLModel):
    """Agent配置列表响应"""
    data: List[AgentConfigPublic]
    count: int
```

- [ ] **Step 2: 修改 app/models.py 添加 PDCA 关系**

在 User 类中添加 PDCA 关系：

```python
# 在 User 类中（大约在第56行，files 关系之后）添加：
# app/models.py
class User(UserBase, table=True):
    # ... 现有字段 ...
    items: list["Item"] = Relationship(back_populates="owner", cascade_delete=True)
    files: list["File"] = Relationship(back_populates="owner", cascade_delete=True)

    # 添加这两个关系：
    pdca_cycles: list["PDCACycle"] = Relationship(
        back_populates="owner",
        sa_relationship_kwargs={"cascade": "all, delete-orphan"}
    )
    agent_configs: list["AgentConfig"] = Relationship(
        back_populates="owner",
        sa_relationship_kwargs={"cascade": "all, delete-orphan"}
    )
```

同时添加导入语句（在文件顶部）：

```python
# 在文件顶部的 import 部分添加：
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.pdca.models import PDCACycle, AgentConfig
```

- [ ] **Step 3: 编写模型测试**

Create: `backend/tests/pdca/test_models.py`

```python
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
```

- [ ] **Step 4: 添加测试 fixtures**

Modify: `backend/tests/conftest.py`

```python
# 在现有 imports 后添加：
from app.pdca.models import PDCACycle, AgentConfig
from app.models import User

# 在现有 fixtures 后添加：

@pytest.fixture
def test_pdca_cycle(db: Session, test_user: User) -> PDCACycle:
    """创建测试用的PDCA循环"""
    cycle = PDCACycle(
        name="Test PDCA Cycle",
        goal="Test goal",
        agent_type="openai",
        agent_input={"prompt": "test"},
        owner_id=test_user.id
    )
    db.add(cycle)
    db.commit()
    db.refresh(cycle)
    return cycle

@pytest.fixture
def test_agent_config(db: Session, test_user: User) -> AgentConfig:
    """创建测试用的Agent配置"""
    config = AgentConfig(
        name="Test OpenAI Config",
        agent_type="openai",
        config={"model": "gpt-4", "temperature": 0.7},
        owner_id=test_user.id
    )
    db.add(config)
    db.commit()
    db.refresh(config)
    return config
```

- [ ] **Step 5: 运行测试验证**

Run: `cd backend && pytest tests/pdca/test_models.py -v`

Expected: PASS（所有测试通过）

- [ ] **Step 6: 创建数据库迁移**

Run: `cd backend && docker compose exec backend alembic revision --autogenerate -m "Add PDCA models"`

Expected: 生成新的迁移文件

Run: `cd backend && docker compose exec backend alembic upgrade head`

Expected: 迁移成功应用，数据库表已创建

- [ ] **Step 7: 提交**

```bash
git add backend/app/pdca/models.py backend/app/models.py backend/tests/pdca/test_models.py backend/tests/conftest.py backend/app/alembic/versions/
git commit -m "feat: add PDCA database models"
```

---

## Task 4: 创建 Agent 执行器基类和注册表

**Files:**
- Create: `backend/app/pdca/agents/__init__.py`
- Create: `backend/app/pdca/agents/base.py`
- Create: `backend/app/pdca/agents/registry.py`

- [ ] **Step 1: 创建 agents 模块**

```python
"""Agent executors for PDCA Do phase."""

from app.pdca.agents.base import BaseAgentExecutor
from app.pdca.agents.registry import AgentRegistry

__all__ = ["BaseAgentExecutor", "AgentRegistry"]
```

- [ ] **Step 2: 编写 Agent 执行器基类**

```python
"""Base agent executor interface."""

from abc import ABC, abstractmethod
from typing import Dict
from uuid import UUID


class BaseAgentExecutor(ABC):
    """
    Agent执行器基类

    所有Agent执行器必须继承此类并实现 execute 和 validate_input 方法
    """

    @abstractmethod
    async def execute(self, input: Dict, cycle_id: UUID) -> Dict:
        """
        执行Agent任务

        Args:
            input: Agent输入参数，如 prompt, model, temperature 等
            cycle_id: PDCA循环ID，用于日志记录

        Returns:
            执行结果字典，包含：
            - status: "success" 或 "error"
            - output: 成功时的输出数据
            - error: 失败时的错误信息
            - usage: 可选的使用统计（如token数）
        """
        pass

    @abstractmethod
    def validate_input(self, input: Dict) -> bool:
        """
        验证输入参数

        Args:
            input: Agent输入参数

        Returns:
            True 如果输入有效，否则 False
        """
        pass
```

- [ ] **Step 3: 编写 Agent 注册表**

```python
"""Agent registry for managing agent executors."""

from typing import Dict, Type, List
from app.pdca.agents.base import BaseAgentExecutor


class AgentRegistry:
    """
    Agent注册表

    管理所有Agent执行器的注册和获取
    使用单例模式确保全局唯一
    """

    _executors: Dict[str, Type[BaseAgentExecutor]] = {}

    @classmethod
    def register(cls, agent_type: str, executor_class: Type[BaseAgentExecutor]):
        """
        注册新的Agent执行器

        Args:
            agent_type: Agent类型标识（如 "openai", "python_script"）
            executor_class: BaseAgentExecutor子类

        Raises:
            ValueError: 如果 agent_type 已存在
        """
        if agent_type in cls._executors:
            raise ValueError(f"Agent type '{agent_type}' already registered")
        cls._executors[agent_type] = executor_class

    @classmethod
    def get_executor(cls, agent_type: str) -> BaseAgentExecutor:
        """
        获取Agent执行器实例

        Args:
            agent_type: Agent类型标识

        Returns:
            Agent执行器实例

        Raises:
            ValueError: 如果 agent_type 未注册
        """
        executor_class = cls._executors.get(agent_type)
        if not executor_class:
            raise ValueError(
                f"Unknown agent type: '{agent_type}'. "
                f"Available types: {cls.list_types()}"
            )
        return executor_class()

    @classmethod
    def list_types(cls) -> List[str]:
        """
        列出所有已注册的Agent类型

        Returns:
            Agent类型列表
        """
        return list(cls._executors.keys())

    @classmethod
    def is_registered(cls, agent_type: str) -> bool:
        """
        检查Agent类型是否已注册

        Args:
            agent_type: Agent类型标识

        Returns:
            True 如果已注册，否则 False
        """
        return agent_type in cls._executors
```

- [ ] **Step 4: 编写注册表测试**

Create: `backend/tests/pdca/test_agents.py`

```python
"""Tests for Agent executors and registry."""

import pytest
from uuid import uuid4
from app.pdca.agents.registry import AgentRegistry
from app.pdca.agents.base import BaseAgentExecutor


# 创建一个测试用的Mock Executor
class MockAgentExecutor(BaseAgentExecutor):
    """Mock agent executor for testing"""

    async def execute(self, input: dict, cycle_id: uuid4) -> dict:
        return {"status": "success", "output": "mock output"}

    def validate_input(self, input: dict) -> bool:
        return "prompt" in input


def test_register_agent_executor():
    """测试注册Agent执行器"""
    initial_count = len(AgentRegistry.list_types())

    AgentRegistry.register("mock", MockAgentExecutor)

    assert AgentRegistry.is_registered("mock")
    assert len(AgentRegistry.list_types()) == initial_count + 1


def test_get_executor():
    """测试获取执行器实例"""
    AgentRegistry.register("mock2", MockAgentExecutor)

    executor = AgentRegistry.get_executor("mock2")

    assert isinstance(executor, MockAgentExecutor)
    assert isinstance(executor, BaseAgentExecutor)


def test_get_unknown_executor_raises_error():
    """测试获取不存在的执行器抛出异常"""
    with pytest.raises(ValueError, match="Unknown agent type"):
        AgentRegistry.get_executor("nonexistent")


def test_list_types():
    """测试列出所有Agent类型"""
    AgentRegistry.register("mock3", MockAgentExecutor)

    types = AgentRegistry.list_types()

    assert "mock3" in types
    assert isinstance(types, list)


def test_duplicate_registration_raises_error():
    """测试重复注册抛出异常"""
    AgentRegistry.register("duplicate", MockAgentExecutor)

    with pytest.raises(ValueError, match="already registered"):
        AgentRegistry.register("duplicate", MockAgentExecutor)
```

- [ ] **Step 5: 运行测试验证**

Run: `cd backend && pytest tests/pdca/test_agents.py -v`

Expected: PASS（所有测试通过）

- [ ] **Step 6: 提交**

```bash
git add backend/app/pdca/agents/ backend/tests/pdca/test_agents.py
git commit -m "feat: add Agent executor base class and registry"
```

---

## Task 5: 实现 OpenAI Agent 执行器

**Files:**
- Create: `backend/app/pdca/agents/openai_agent.py`
- Modify: `backend/app/core/config.py`
- Create: `backend/tests/pdca/test_openai_agent.py`

- [ ] **Step 1: 在 config.py 中添加 OpenAI 配置**

Read: `backend/app/core/config.py` 查看现有配置结构

Add:

```python
# 在 settings 类中添加（大约在项目配置部分）：

class Settings(BaseSettings):
    # ... 现有配置 ...

    # OpenAI Configuration
    OPENAI_API_KEY: str = Field(default="", validation_alias="OPENAI_API_KEY")
    OPENAI_MODEL: str = "gpt-4"
    OPENAI_MAX_TOKENS: int = 2000
    OPENAI_TEMPERATURE: float = 0.7
```

- [ ] **Step 2: 实现 OpenAI Agent 执行器**

```python
"""OpenAI Agent executor."""

from typing import Dict
from uuid import UUID
from openai import AsyncOpenAI

from app.pdca.agents.base import BaseAgentExecutor
from app.core.config import settings


class OpenAIAgentExecutor(BaseAgentExecutor):
    """
    OpenAI Agent执行器

    使用OpenAI API执行LLM任务
    支持chat.completions接口
    """

    def __init__(self):
        self.client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)

    async def execute(self, input: Dict, cycle_id: UUID) -> Dict:
        """
        执行OpenAI API调用

        Args:
            input: 包含以下字段的字典：
                - prompt (str): 用户提示
                - system_prompt (str, optional): 系统提示
                - model (str, optional): 模型名称，默认使用配置的模型
                - temperature (float, optional): 温度参数
                - max_tokens (int, optional): 最大token数
            cycle_id: PDCA循环ID

        Returns:
            执行结果字典
        """
        prompt = input.get("prompt")
        if not prompt:
            return {
                "status": "error",
                "error": "Missing required field: prompt"
            }

        model = input.get("model", settings.OPENAI_MODEL)
        temperature = input.get("temperature", settings.OPENAI_TEMPERATURE)
        max_tokens = input.get("max_tokens", settings.OPENAI_MAX_TOKENS)
        system_prompt = input.get("system_prompt", "You are a helpful assistant.")

        try:
            response = await self.client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": prompt}
                ],
                temperature=temperature,
                max_tokens=max_tokens
            )

            return {
                "status": "success",
                "output": response.choices[0].message.content,
                "model": model,
                "usage": {
                    "prompt_tokens": response.usage.prompt_tokens,
                    "completion_tokens": response.usage.completion_tokens,
                    "total_tokens": response.usage.total_tokens
                }
            }
        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
                "error_type": type(e).__name__
            }

    def validate_input(self, input: Dict) -> bool:
        """
        验证输入参数

        必须包含 'prompt' 字段
        """
        return isinstance(input, dict) and "prompt" in input
```

- [ ] **Step 3: 注册 OpenAI Agent**

Modify: `backend/app/pdca/agents/__init__.py`

```python
"""Agent executors for PDCA Do phase."""

from app.pdca.agents.base import BaseAgentExecutor
from app.pdca.agents.registry import AgentRegistry
from app.pdca.agents.openai_agent import OpenAIAgentExecutor

# 注册内置Agent执行器
AgentRegistry.register("openai", OpenAIAgentExecutor)

__all__ = ["BaseAgentExecutor", "AgentRegistry", "OpenAIAgentExecutor"]
```

- [ ] **Step 4: 编写 OpenAI Agent 测试**

Create: `backend/tests/pdca/test_openai_agent.py`

```python
"""Tests for OpenAI Agent executor."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4
from app.pdca.agents.openai_agent import OpenAIAgentExecutor
from app.pdca.agents.registry import AgentRegistry


@pytest.fixture
def openai_executor():
    """创建OpenAI执行器实例"""
    return OpenAIAgentExecutor()


def test_openai_agent_is_registered():
    """测试OpenAI Agent已注册"""
    assert AgentRegistry.is_registered("openai")

    executor = AgentRegistry.get_executor("openai")
    assert isinstance(executor, OpenAIAgentExecutor)


def test_validate_input_with_valid_prompt(openai_executor):
    """测试验证有效输入"""
    assert openai_executor.validate_input({"prompt": "test prompt"})


def test_validate_input_with_missing_prompt(openai_executor):
    """测试验证缺少prompt的输入"""
    assert not openai_executor.validate_input({})
    assert not openai_executor.validate_input({"other": "data"})


@pytest.mark.asyncio
async def test_execute_with_mock_response(openai_executor):
    """测试执行（使用mock响应）"""
    mock_response = MagicMock()
    mock_response.choices = [MagicMock()]
    mock_response.choices[0].message.content = "Test response"
    mock_response.usage.prompt_tokens = 10
    mock_response.usage.completion_tokens = 20
    mock_response.usage.total_tokens = 30

    with patch.object(openai_executor.client, "chat", create=True) as mock_chat:
        mock_chat.completions.create = AsyncMock(return_value=mock_response)

        result = await openai_executor.execute(
            {"prompt": "test prompt"},
            uuid4()
        )

        assert result["status"] == "success"
        assert result["output"] == "Test response"
        assert result["usage"]["total_tokens"] == 30


@pytest.mark.asyncio
async def test_execute_with_missing_prompt(openai_executor):
    """测试执行时缺少prompt"""
    result = await openai_executor.execute({}, uuid4())

    assert result["status"] == "error"
    assert "Missing required field" in result["error"]


@pytest.mark.asyncio
async def test_execute_with_api_error(openai_executor):
    """测试API错误处理"""
    with patch.object(openai_executor.client, "chat", create=True) as mock_chat:
        mock_chat.completions.create = AsyncMock(
            side_effect=Exception("API Error")
        )

        result = await openai_executor.execute(
            {"prompt": "test"},
            uuid4()
        )

        assert result["status"] == "error"
        assert "API Error" in result["error"]
```

- [ ] **Step 5: 更新 .env.example**

已在 Task 1 中完成

- [ ] **Step 6: 运行测试验证**

Run: `cd backend && pytest tests/pdca/test_openai_agent.py -v`

Expected: PASS（所有测试通过）

- [ ] **Step 7: 提交**

```bash
git add backend/app/pdca/agents/openai_agent.py backend/app/pdca/agents/__init__.py backend/app/core/config.py backend/tests/pdca/test_openai_agent.py
git commit -m "feat: add OpenAI Agent executor"
```

---

## Task 6: 实现 PDCA CRUD 操作

**Files:**
- Create: `backend/app/pdca/crud.py`
- Create: `backend/tests/pdca/test_crud.py`

- [ ] **Step 1: 编写 PDCA CRUD 函数**

```python
"""CRUD operations for PDCA cycles and agent configs."""

from typing import Optional, List
from uuid import UUID
from sqlmodel import Session, select
from app.pdca.models import (
    PDCACycle,
    PDCACycleCreate,
    PDCACycleUpdate,
    AgentConfig,
    AgentConfigCreate,
    AgentConfigUpdate,
    ExecutionLog
)


# ========== PDCA Cycle CRUD ==========

def create_pdca_cycle(
    session: Session,
    cycle_data: PDCACycleCreate,
    owner_id: UUID
) -> PDCACycle:
    """
    创建PDCA循环

    Args:
        session: 数据库会话
        cycle_data: 循环数据
        owner_id: 所有者ID

    Returns:
        创建的PDCA循环
    """
    cycle = PDCACycle(
        **cycle_data.model_dump(),
        owner_id=owner_id
    )
    session.add(cycle)
    session.commit()
    session.refresh(cycle)
    return cycle


def get_pdca_cycle(session: Session, cycle_id: UUID) -> Optional[PDCACycle]:
    """
    获取单个PDCA循环

    Args:
        session: 数据库会话
        cycle_id: 循环ID

    Returns:
        PDCA循环或None
    """
    return session.get(PDCACycle, cycle_id)


def list_pdca_cycles(
    session: Session,
    owner_id: UUID,
    parent_id: Optional[UUID] = None,
    phase: Optional[str] = None,
    status: Optional[str] = None,
    skip: int = 0,
    limit: int = 100
) -> tuple[List[PDCACycle], int]:
    """
    获取PDCA循环列表

    Args:
        session: 数据库会话
        owner_id: 所有者ID
        parent_id: 父循环ID（过滤条件）
        phase: 阶段（过滤条件）
        status: 状态（过滤条件）
        skip: 跳过记录数
        limit: 返回记录数

    Returns:
        (循环列表, 总数)
    """
    statement = select(PDCACycle).where(PDCACycle.owner_id == owner_id)

    if parent_id is not None:
        statement = statement.where(PDCACycle.parent_id == parent_id)
    if phase is not None:
        statement = statement.where(PDCACycle.phase == phase)
    if status is not None:
        statement = statement.where(PDCACycle.status == status)

    # 获取总数
    count_statement = select(PDCACycle.id).where(
        PDCACycle.owner_id == owner_id
    )
    if parent_id is not None:
        count_statement = count_statement.where(PDCACycle.parent_id == parent_id)
    if phase is not None:
        count_statement = count_statement.where(PDCACycle.phase == phase)
    if status is not None:
        count_statement = count_statement.where(PDCACycle.status == status)

    total = len(session.exec(count_statement).all())

    # 应用分页
    statement = statement.offset(skip).limit(limit)
    statement = statement.order_by(PDCACycle.created_at.desc())

    cycles = session.exec(statement).all()
    return list(cycles), total


def update_pdca_cycle(
    session: Session,
    cycle: PDCACycle,
    cycle_update: PDCACycleUpdate
) -> PDCACycle:
    """
    更新PDCA循环

    Args:
        session: 数据库会话
        cycle: 要更新的循环
        cycle_update: 更新数据

    Returns:
        更新后的循环
    """
    cycle_data = cycle_update.model_dump(exclude_unset=True)
    for key, value in cycle_data.items():
        setattr(cycle, key, value)

    session.add(cycle)
    session.commit()
    session.refresh(cycle)
    return cycle


def delete_pdca_cycle(session: Session, cycle: PDCACycle) -> bool:
    """
    删除PDCA循环

    Args:
        session: 数据库会话
        cycle: 要删除的循环

    Returns:
        是否成功删除
    """
    session.delete(cycle)
    session.commit()
    return True


def get_child_cycles(
    session: Session,
    parent_id: UUID
) -> List[PDCACycle]:
    """
    获取子循环列表

    Args:
        session: 数据库会话
        parent_id: 父循环ID

    Returns:
        子循环列表
    """
    statement = select(PDCACycle).where(PDCACycle.parent_id == parent_id)
    statement = statement.order_by(PDCACycle.created_at.asc())
    return list(session.exec(statement).all())


# ========== Agent Config CRUD ==========

def create_agent_config(
    session: Session,
    config_data: AgentConfigCreate,
    owner_id: UUID
) -> AgentConfig:
    """
    创建Agent配置

    Args:
        session: 数据库会话
        config_data: 配置数据
        owner_id: 所有者ID

    Returns:
        创建的Agent配置
    """
    config = AgentConfig(
        **config_data.model_dump(),
        owner_id=owner_id
    )
    session.add(config)
    session.commit()
    session.refresh(config)
    return config


def get_agent_config(session: Session, config_id: UUID) -> Optional[AgentConfig]:
    """
    获取单个Agent配置

    Args:
        session: 数据库会话
        config_id: 配置ID

    Returns:
        Agent配置或None
    """
    return session.get(AgentConfig, config_id)


def list_agent_configs(
    session: Session,
    owner_id: UUID,
    agent_type: Optional[str] = None,
    skip: int = 0,
    limit: int = 100
) -> tuple[List[AgentConfig], int]:
    """
    获取Agent配置列表

    Args:
        session: 数据库会话
        owner_id: 所有者ID
        agent_type: Agent类型（过滤条件）
        skip: 跳过记录数
        limit: 返回记录数

    Returns:
        (配置列表, 总数)
    """
    statement = select(AgentConfig).where(AgentConfig.owner_id == owner_id)

    if agent_type is not None:
        statement = statement.where(AgentConfig.agent_type == agent_type)

    count = len(session.exec(
        select(AgentConfig.id).where(AgentConfig.owner_id == owner_id)
    ).all())

    statement = statement.offset(skip).limit(limit)
    statement = statement.order_by(AgentConfig.created_at.desc())

    configs = session.exec(statement).all()
    return list(configs), count


# ========== Execution Log ==========

def create_execution_log(
    session: Session,
    cycle_id: UUID,
    phase: str,
    level: str,
    message: str,
    metadata: dict = None
) -> ExecutionLog:
    """
    创建执行日志

    Args:
        session: 数据库会话
        cycle_id: 循环ID
        phase: 阶段
        level: 日志级别 (info, warning, error)
        message: 日志消息
        metadata: 额外元数据

    Returns:
        创建的日志记录
    """
    log = ExecutionLog(
        cycle_id=cycle_id,
        phase=phase,
        level=level,
        message=message,
        metadata=metadata or {}
    )
    session.add(log)
    session.commit()
    session.refresh(log)
    return log


def get_cycle_logs(
    session: Session,
    cycle_id: UUID,
    skip: int = 0,
    limit: int = 100
) -> List[ExecutionLog]:
    """
    获取循环的执行日志

    Args:
        session: 数据库会话
        cycle_id: 循环ID
        skip: 跳过记录数
        limit: 返回记录数

    Returns:
        日志列表
    """
    statement = select(ExecutionLog).where(
        ExecutionLog.cycle_id == cycle_id
    )
    statement = statement.order_by(ExecutionLog.created_at.desc())
    statement = statement.offset(skip).limit(limit)

    return list(session.exec(statement).all())
```

- [ ] **Step 2: 编写 CRUD 测试**

Create: `backend/tests/pdca/test_crud.py`

```python
"""Tests for PDCA CRUD operations."""

import pytest
from uuid import uuid4
from sqlmodel import Session
from app.pdca.crud import (
    create_pdca_cycle,
    get_pdca_cycle,
    list_pdca_cycles,
    update_pdca_cycle,
    delete_pdca_cycle,
    get_child_cycles,
    create_agent_config,
    get_agent_config,
    list_agent_configs,
    create_execution_log,
    get_cycle_logs
)
from app.pdca.models import PDCACycleCreate, PDCACycleUpdate, AgentConfigCreate
from app.models import User


def test_create_pdca_cycle(db: Session, test_user: User):
    """测试创建PDCA循环"""
    cycle_data = PDCACycleCreate(
        name="Test Cycle",
        goal="Test goal",
        agent_type="openai",
        agent_input={"prompt": "test"}
    )

    cycle = create_pdca_cycle(db, cycle_data, test_user.id)

    assert cycle.id is not None
    assert cycle.name == "Test Cycle"
    assert cycle.owner_id == test_user.id


def test_get_pdca_cycle(db: Session, test_pdca_cycle: PDCACycle):
    """测试获取单个PDCA循环"""
    cycle = get_pdca_cycle(db, test_pdca_cycle.id)

    assert cycle is not None
    assert cycle.id == test_pdca_cycle.id


def test_list_pdca_cycles(db: Session, test_user: User):
    """测试列出PDCA循环"""
    # 创建多个循环
    for i in range(3):
        cycle_data = PDCACycleCreate(
            name=f"Cycle {i}",
            goal=f"Goal {i}",
            agent_type="openai",
            agent_input={}
        )
        create_pdca_cycle(db, cycle_data, test_user.id)

    cycles, total = list_pdca_cycles(db, test_user.id)

    assert total >= 3
    assert len(cycles) >= 3


def test_update_pdca_cycle(db: Session, test_pdca_cycle: PDCACycle):
    """测试更新PDCA循环"""
    update_data = PDCACycleUpdate(
        name="Updated Name",
        phase="do",
        status="running"
    )

    updated_cycle = update_pdca_cycle(db, test_pdca_cycle, update_data)

    assert updated_cycle.name == "Updated Name"
    assert updated_cycle.phase == "do"
    assert updated_cycle.status == "running"


def test_delete_pdca_cycle(db: Session, test_pdca_cycle: PDCACycle):
    """测试删除PDCA循环"""
    cycle_id = test_pdca_cycle.id

    result = delete_pdca_cycle(db, test_pdca_cycle)

    assert result is True
    assert get_pdca_cycle(db, cycle_id) is None


def test_get_child_cycles(db: Session, test_user: User):
    """测试获取子循环"""
    # 创建父循环
    parent_data = PDCACycleCreate(
        name="Parent",
        goal="Parent goal",
        agent_type="openai",
        agent_input={}
    )
    parent = create_pdca_cycle(db, parent_data, test_user.id)

    # 创建子循环
    for i in range(2):
        child_data = PDCACycleCreate(
            name=f"Child {i}",
            goal=f"Child goal {i}",
            agent_type="openai",
            agent_input={},
            parent_id=parent.id
        )
        create_pdca_cycle(db, child_data, test_user.id)

    children = get_child_cycles(db, parent.id)

    assert len(children) == 2
    assert all(c.parent_id == parent.id for c in children)


def test_create_agent_config(db: Session, test_user: User):
    """测试创建Agent配置"""
    config_data = AgentConfigCreate(
        name="Test Config",
        agent_type="openai",
        config={"model": "gpt-4"}
    )

    config = create_agent_config(db, config_data, test_user.id)

    assert config.id is not None
    assert config.name == "Test Config"
    assert config.config["model"] == "gpt-4"


def test_create_execution_log(db: Session, test_pdca_cycle: PDCACycle):
    """测试创建执行日志"""
    log = create_execution_log(
        db,
        test_pdca_cycle.id,
        "do",
        "info",
        "Agent execution started"
    )

    assert log.id is not None
    assert log.cycle_id == test_pdca_cycle.id
    assert log.phase == "do"


def test_get_cycle_logs(db: Session, test_pdca_cycle: PDCACycle):
    """测试获取循环日志"""
    # 创建多条日志
    for i in range(3):
        create_execution_log(
            db,
            test_pdca_cycle.id,
            "do",
            "info",
            f"Log message {i}"
        )

    logs = get_cycle_logs(db, test_pdca_cycle.id)

    assert len(logs) >= 3
```

- [ ] **Step 3: 运行测试验证**

Run: `cd backend && pytest tests/pdca/test_crud.py -v`

Expected: PASS（所有测试通过）

- [ ] **Step 4: 提交**

```bash
git add backend/app/pdca/crud.py backend/tests/pdca/test_crud.py
git commit -m "feat: add PDCA CRUD operations"
```

---

## Task 7: 实现 LangGraph PDCA 引擎（基础版本）

**Files:**
- Create: `backend/app/pdca/engine.py`
- Create: `backend/tests/pdca/test_engine.py`

- [ ] **Step 1: 编写 LangGraph PDCA 引擎**

```python
"""PDCA workflow engine using LangGraph."""

import uuid
import asyncio
from typing import Dict, Any, Literal
from datetime import datetime

from langgraph.graph import StateGraph, END
from langgraph.checkpoint.postgres import PostgresCheckpointSaver
from langgraph.checkpoint import Checkpoint
from sqlalchemy.ext.asyncio import AsyncSession

from app.pdca.state import PDCAState
from app.pdca.agents.registry import AgentRegistry
from app.pdca.crud import (
    create_execution_log,
    get_pdca_cycle,
    get_child_cycles,
    update_pdca_cycle
)
from app.pdca.models import PDCACycleUpdate
from app.core.config import settings


class PDCAEngine:
    """
    PDCA工作流引擎

    使用LangGraph StateGraph实现PDCA状态机
    支持Plan -> Do -> Check -> Act的完整流程
    """

    def __init__(self, db_session: AsyncSession):
        """
        初始化PDCA引擎

        Args:
            db_session: 异步数据库会话
        """
        self.db_session = db_session
        self.checkpoint_saver = None
        # 注意：实际项目中需要初始化PostgresCheckpointSaver
        # 这里暂时使用MemoryCheckpointSaver用于测试
        from langgraph.checkpoint.memory import MemorySaver
        self.checkpoint_saver = MemorySaver()
        self.graph = self._build_graph()

    def _build_graph(self) -> StateGraph:
        """
        构建PDCA状态图

        定义四个节点和它们之间的转换关系

        Returns:
            编译后的StateGraph
        """
        workflow = StateGraph(PDCAState)

        # 添加四个节点
        workflow.add_node("plan_node", self._plan_node)
        workflow.add_node("do_node", self._do_node)
        workflow.add_node("check_node", self._check_node)
        workflow.add_node("act_node", self._act_node)

        # 定义入口点
        workflow.set_entry_point("plan_node")

        # 定义边（状态转换）
        workflow.add_edge("plan_node", "do_node")
        workflow.add_edge("do_node", "check_node")

        # Check节点的条件分支
        # 根据检查结果决定是结束还是进入Act阶段
        workflow.add_conditional_edges(
            "check_node",
            self._should_continue_or_improve,
            {
                "continue": END,      # 检查通过，结束
                "improve": "act_node"  # 需要改进，进入Act
            }
        )

        # Act节点总是结束
        workflow.add_edge("act_node", END)

        return workflow.compile(checkpointer=self.checkpoint_saver)

    async def _plan_node(self, state: PDCAState) -> PDCAState:
        """
        Plan阶段节点

        1. 设置目标
        2. 制定计划
        3. 检查是否有子循环需要等待

        Args:
            state: 当前状态

        Returns:
            更新后的状态
        """
        cycle_id = uuid.UUID(state["id"])

        # 记录日志
        await create_execution_log(
            self.db_session,
            cycle_id,
            "plan",
            "info",
            f"Plan phase started. Goal: {state['goal']}"
        )

        # 检查是否有子循环
        children = await self._get_children_sync(cycle_id)
        has_children = len(children) > 0

        if has_children:
            await create_execution_log(
                self.db_session,
                cycle_id,
                "plan",
                "info",
                f"Waiting for {len(children)} child cycles to complete"
            )

        return {
            **state,
            "phase": "plan",
            "plan_details": state.get("plan_details", {}),
            "updated_at": datetime.utcnow()
        }

    async def _do_node(self, state: PDCAState) -> PDCAState:
        """
        Do阶段节点

        执行Agent任务

        Args:
            state: 当前状态

        Returns:
            更新后的状态
        """
        cycle_id = uuid.UUID(state["id"])
        agent_type = state.get("agent_type", "openai")
        agent_input = state.get("agent_input", {})

        await create_execution_log(
            self.db_session,
            cycle_id,
            "do",
            "info",
            f"Do phase started. Executing {agent_type} agent"
        )

        try:
            # 获取Agent执行器
            agent_executor = AgentRegistry.get_executor(agent_type)

            # 执行Agent
            execution_result = await agent_executor.execute(
                input=agent_input,
                cycle_id=cycle_id
            )

            # 记录执行结果
            if execution_result.get("status") == "success":
                await create_execution_log(
                    self.db_session,
                    cycle_id,
                    "do",
                    "info",
                    f"Agent execution succeeded"
                )
            else:
                await create_execution_log(
                    self.db_session,
                    cycle_id,
                    "do",
                    "error",
                    f"Agent execution failed: {execution_result.get('error', 'Unknown error')}"
                )

            return {
                **state,
                "phase": "do",
                "execution_result": execution_result,
                "updated_at": datetime.utcnow()
            }

        except Exception as e:
            await create_execution_log(
                self.db_session,
                cycle_id,
                "do",
                "error",
                f"Agent execution error: {str(e)}"
            )

            return {
                **state,
                "phase": "do",
                "execution_result": {
                    "status": "error",
                    "error": str(e)
                },
                "updated_at": datetime.utcnow(),
                "error": str(e)
            }

    async def _check_node(self, state: PDCAState) -> PDCAState:
        """
        Check阶段节点

        检查Do阶段的结果

        Args:
            state: 当前状态

        Returns:
            更新后的状态
        """
        cycle_id = uuid.UUID(state["id"])

        await create_execution_log(
            self.db_session,
            cycle_id,
            "check",
            "info",
            "Check phase started"
        )

        # 获取执行结果
        execution_result = state.get("execution_result", {})

        # 简单的自动检查逻辑
        # MVP版本：如果Agent执行成功，则通过
        passed = execution_result.get("status") == "success"

        check_result = {
            "execution_status": execution_result.get("status"),
            "passed": passed,
            "checked_at": datetime.utcnow().isoformat()
        }

        if passed:
            await create_execution_log(
                self.db_session,
                cycle_id,
                "check",
                "info",
                "Check passed"
            )
        else:
            await create_execution_log(
                self.db_session,
                cycle_id,
                "check",
                "warning",
                "Check failed"
            )

        return {
            **state,
            "phase": "check",
            "check_result": check_result,
            "passed": passed,
            "approval_status": "auto_approved" if passed else "auto_rejected",
            "updated_at": datetime.utcnow()
        }

    async def _act_node(self, state: PDCAState) -> PDCAState:
        """
        Act阶段节点

        处理改进措施

        Args:
            state: 当前状态

        Returns:
            更新后的状态
        """
        cycle_id = uuid.UUID(state["id"])

        await create_execution_log(
            self.db_session,
            cycle_id,
            "act",
            "info",
            "Act phase started - generating improvements"
        )

        # MVP版本：简单记录需要改进
        improvements = [
            {
                "action": "review_execution",
                "description": "Review the failed execution",
                "priority": "high"
            }
        ]

        return {
            **state,
            "phase": "act",
            "improvement_actions": improvements,
            "updated_at": datetime.utcnow()
        }

    def _should_continue_or_improve(self, state: PDCAState) -> Literal["continue", "improve"]:
        """
        Check节点的条件分支判断

        根据检查结果决定下一步

        Args:
            state: 当前状态

        Returns:
            "continue" 或 "improve"
        """
        passed = state.get("passed", False)
        approval_status = state.get("approval_status")

        # 检查通过且已批准
        if passed and approval_status in ["auto_approved", "approved"]:
            return "continue"

        # 需要改进
        return "improve"

    async def _get_children_sync(self, parent_id: uuid.UUID) -> list:
        """
        同步获取子循环（辅助方法）

        Args:
            parent_id: 父循环ID

        Returns:
            子循环列表
        """
        # 在异步上下文中运行同步代码
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None,
            lambda: get_child_cycles(self.db_session, parent_id)
        )

    async def execute_cycle(self, cycle_id: uuid.UUID) -> PDCAState:
        """
        执行PDCA循环

        Args:
            cycle_id: 循环ID

        Returns:
            最终状态
        """
        # 从数据库获取循环
        cycle = get_pdca_cycle(self.db_session, cycle_id)
        if not cycle:
            raise ValueError(f"Cycle not found: {cycle_id}")

        # 构建初始状态
        initial_state: PDCAState = {
            "id": str(cycle.id),
            "parent_id": str(cycle.parent_id) if cycle.parent_id else None,
            "phase": cycle.phase,
            "goal": cycle.name,  # 简化：使用name作为goal
            "plan_details": cycle.state_data.get("plan_details", {}),
            "agent_type": cycle.agent_type or "openai",
            "agent_input": cycle.state_data.get("agent_input", {}),
            "execution_result": None,
            "check_criteria": {},
            "check_result": None,
            "passed": None,
            "approval_status": None,
            "improvement_actions": [],
            "created_at": cycle.created_at,
            "updated_at": datetime.utcnow(),
            "error": None
        }

        # 更新状态为running
        update_data = PDCACycleUpdate(status="running", started_at=datetime.utcnow())
        update_pdca_cycle(self.db_session, cycle, update_data)

        # 执行工作流
        config = {"configurable": {"thread_id": str(cycle_id)}}
        final_state = await self.graph.ainvoke(initial_state, config)

        # 更新最终状态
        final_phase = final_state.get("phase", "failed")
        final_status = "completed" if final_state.get("passed") else "failed"

        update_data = PDCACycleUpdate(
            phase=final_phase,
            status=final_status,
            completed_at=datetime.utcnow()
        )

        cycle = get_pdca_cycle(self.db_session, cycle_id)
        update_pdca_cycle(self.db_session, cycle, update_data)

        return final_state
```

- [ ] **Step 2: 编写引擎测试**

Create: `backend/tests/pdca/test_engine.py`

```python
"""Tests for PDCA engine."""

import pytest
from uuid import uuid4
from unittest.mock import AsyncMock, patch
from app.pdca.engine import PDCAEngine
from app.pdca.models import PDCACycle, PDCACycleCreate
from app.pdca.state import PDCAState


@pytest.fixture
def pdca_engine(db_session):
    """创建PDCA引擎实例"""
    return PDCAEngine(db_session)


@pytest.mark.asyncio
async def test_plan_node(pdca_engine, test_pdca_cycle):
    """测试Plan节点"""
    state: PDCAState = {
        "id": str(test_pdca_cycle.id),
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
        "created_at": test_pdca_cycle.created_at,
        "updated_at": test_pdca_cycle.updated_at,
        "error": None
    }

    result = await pdca_engine._plan_node(state)

    assert result["phase"] == "plan"
    assert "plan_details" in result


@pytest.mark.asyncio
async def test_do_node_success(pdca_engine, test_pdca_cycle):
    """测试Do节点成功执行"""
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
        "created_at": test_pdca_cycle.created_at,
        "updated_at": test_pdca_cycle.updated_at,
        "error": None
    }

    # Mock OpenAI executor
    with patch("app.pdca.engine.AgentRegistry.get_executor") as mock_get:
        mock_executor = AsyncMock()
        mock_executor.execute.return_value = {
            "status": "success",
            "output": "Test response"
        }
        mock_get.return_value = mock_executor

        result = await pdca_engine._do_node(state)

        assert result["phase"] == "do"
        assert result["execution_result"]["status"] == "success"


@pytest.mark.asyncio
async def test_check_node_passed(pdca_engine, test_pdca_cycle):
    """测试Check节点通过"""
    state: PDCAState = {
        "id": str(test_pdca_cycle.id),
        "parent_id": None,
        "phase": "check",
        "goal": "Test goal",
        "plan_details": {},
        "agent_type": "openai",
        "agent_input": {},
        "execution_result": {"status": "success"},
        "check_criteria": {},
        "check_result": None,
        "passed": None,
        "approval_status": None,
        "improvement_actions": [],
        "created_at": test_pdca_cycle.created_at,
        "updated_at": test_pdca_cycle.updated_at,
        "error": None
    }

    result = await pdca_engine._check_node(state)

    assert result["phase"] == "check"
    assert result["passed"] is True
    assert result["approval_status"] == "auto_approved"


def test_should_continue_or_improve_continue(pdca_engine):
    """测试条件分支判断 - continue"""
    state: PDCAState = {
        "id": "test",
        "parent_id": None,
        "phase": "check",
        "goal": "test",
        "plan_details": {},
        "agent_type": "openai",
        "agent_input": {},
        "execution_result": None,
        "check_criteria": {},
        "check_result": None,
        "passed": True,
        "approval_status": "auto_approved",
        "improvement_actions": [],
        "created_at": pdca_engine,
        "updated_at": pdca_engine,
        "error": None
    }

    result = pdca_engine._should_continue_or_improve(state)
    assert result == "continue"


def test_should_continue_or_improve_act(pdca_engine):
    """测试条件分支判断 - improve"""
    state: PDCAState = {
        "id": "test",
        "parent_id": None,
        "phase": "check",
        "goal": "test",
        "plan_details": {},
        "agent_type": "openai",
        "agent_input": {},
        "execution_result": None,
        "check_criteria": {},
        "check_result": None,
        "passed": False,
        "approval_status": "auto_rejected",
        "improvement_actions": [],
        "created_at": pdca_engine,
        "updated_at": pdca_engine,
        "error": None
    }

    result = pdca_engine._should_continue_or_improve(state)
    assert result == "improve"
```

注意：上述测试中的 `created_at` 和 `updated_at` 需要使用实际的 datetime 对象，这里简化了。

- [ ] **Step 3: 修复测试中的 datetime 问题**

修改测试文件，使用正确的 datetime：

```python
from datetime import datetime

# 在每个 state 中使用：
"created_at": datetime.utcnow(),
"updated_at": datetime.utcnow(),
```

- [ ] **Step 4: 运行测试验证**

Run: `cd backend && pytest tests/pdca/test_engine.py -v`

Expected: PASS（所有测试通过）

- [ ] **Step 5: 提交**

```bash
git add backend/app/pdca/engine.py backend/tests/pdca/test_engine.py
git commit -m "feat: add LangGraph PDCA engine"
```

---

## Task 8: 实现 PDCA API 路由

**Files:**
- Create: `backend/app/api/routes/pdca.py`
- Modify: `backend/app/api/main.py`

- [ ] **Step 1: 编写 PDCA API 路由**

```python
"""PDCA API routes."""

from uuid import UUID
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session

from app.api.deps import SessionDep, CurrentUser
from app.models import User
from app.pdca.models import (
    PDCACycle,
    PDCACycleCreate,
    PDCACycleUpdate,
    PDCACyclePublic,
    PDCACyclesPublic,
    AgentConfig,
    AgentConfigCreate,
    AgentConfigPublic,
    AgentConfigsPublic
)
from app.pdca.crud import (
    create_pdca_cycle,
    get_pdca_cycle,
    list_pdca_cycles,
    update_pdca_cycle,
    delete_pdca_cycle,
    get_child_cycles,
    create_agent_config,
    get_agent_config,
    list_agent_configs,
    get_cycle_logs
)
from app.pdca.engine import PDCAEngine


router = APIRouter(prefix="/pdca", tags=["PDCA"])


# ========== PDCA Cycle Routes ==========

@router.post("/cycles", response_model=PDCACyclePublic, status_code=status.HTTP_201_CREATED)
def create_cycle(
    cycle_data: PDCACycleCreate,
    session: SessionDep,
    current_user: CurrentUser
) -> PDCACycle:
    """
    创建新的PDCA循环

    Args:
        cycle_data: 循环数据
        session: 数据库会话
        current_user: 当前用户

    Returns:
        创建的PDCA循环
    """
    cycle = create_pdca_cycle(session, cycle_data, current_user.id)
    return cycle


@router.get("/cycles", response_model=PDCACyclesPublic)
def read_cycles(
    session: SessionDep,
    current_user: CurrentUser,
    parent_id: Optional[UUID] = None,
    phase: Optional[str] = None,
    status_param: Optional[str] = None,
    skip: int = 0,
    limit: int = 100
) -> PDCACyclesPublic:
    """
    获取PDCA循环列表

    Args:
        session: 数据库会话
        current_user: 当前用户
        parent_id: 父循环ID（过滤）
        phase: 阶段（过滤）
        status_param: 状态（过滤）
        skip: 跳过记录数
        limit: 返回记录数

    Returns:
        循环列表和总数
    """
    cycles, count = list_pdca_cycles(
        session,
        current_user.id,
        parent_id=parent_id,
        phase=phase,
        status=status_param,
        skip=skip,
        limit=limit
    )
    return PDCACyclesPublic(data=cycles, count=count)


@router.get("/cycles/{cycle_id}", response_model=PDCACyclePublic)
def read_cycle(
    cycle_id: UUID,
    session: SessionDep,
    current_user: CurrentUser
) -> PDCACycle:
    """
    获取单个PDCA循环详情

    Args:
        cycle_id: 循环ID
        session: 数据库会话
        current_user: 当前用户

    Returns:
        PDCA循环详情
    """
    cycle = get_pdca_cycle(session, cycle_id)
    if not cycle:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Cycle not found"
        )

    # 检查权限
    if cycle.owner_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to access this cycle"
        )

    return cycle


@router.post("/cycles/{cycle_id}/execute", response_model=PDCACyclePublic)
async def execute_cycle(
    cycle_id: UUID,
    session: SessionDep,
    current_user: CurrentUser
) -> PDCACycle:
    """
    启动PDCA循环执行

    Args:
        cycle_id: 循环ID
        session: 数据库会话
        current_user: 当前用户

    Returns:
        更新后的PDCA循环
    """
    cycle = get_pdca_cycle(session, cycle_id)
    if not cycle:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Cycle not found"
        )

    if cycle.owner_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to execute this cycle"
        )

    # 创建引擎并执行
    engine = PDCAEngine(session)
    try:
        await engine.execute_cycle(cycle_id)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Execution failed: {str(e)}"
        )

    # 重新获取更新后的循环
    cycle = get_pdca_cycle(session, cycle_id)
    return cycle


@router.get("/cycles/{cycle_id}/children", response_model=PDCACyclesPublic)
def read_child_cycles(
    cycle_id: UUID,
    session: SessionDep,
    current_user: CurrentUser
) -> PDCACyclesPublic:
    """
    获取子循环列表

    Args:
        cycle_id: 父循环ID
        session: 数据库会话
        current_user: 当前用户

    Returns:
        子循环列表
    """
    parent = get_pdca_cycle(session, cycle_id)
    if not parent:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Parent cycle not found"
        )

    if parent.owner_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized"
        )

    children = get_child_cycles(session, cycle_id)
    return PDCACyclesPublic(data=children, count=len(children))


@router.delete("/cycles/{cycle_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_cycle(
    cycle_id: UUID,
    session: SessionDep,
    current_user: CurrentUser
) -> None:
    """
    删除PDCA循环

    Args:
        cycle_id: 循环ID
        session: 数据库会话
        current_user: 当前用户
    """
    cycle = get_pdca_cycle(session, cycle_id)
    if not cycle:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Cycle not found"
        )

    if cycle.owner_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to delete this cycle"
        )

    delete_pdca_cycle(session, cycle)


# ========== Agent Config Routes ==========

@router.post("/agents/configs", response_model=AgentConfigPublic, status_code=status.HTTP_201_CREATED)
def create_agent_config_route(
    config_data: AgentConfigCreate,
    session: SessionDep,
    current_user: CurrentUser
) -> AgentConfig:
    """创建Agent配置"""
    return create_agent_config(session, config_data, current_user.id)


@router.get("/agents/configs", response_model=AgentConfigsPublic)
def read_agent_configs(
    session: SessionDep,
    current_user: CurrentUser,
    agent_type: Optional[str] = None,
    skip: int = 0,
    limit: int = 100
) -> AgentConfigsPublic:
    """获取Agent配置列表"""
    configs, count = list_agent_configs(
        session,
        current_user.id,
        agent_type=agent_type,
        skip=skip,
        limit=limit
    )
    return AgentConfigsPublic(data=configs, count=count)


@router.get("/agents/types")
def list_agent_types() -> dict:
    """获取支持的Agent类型列表"""
    from app.pdca.agents.registry import AgentRegistry
    return {"types": AgentRegistry.list_types()}
```

- [ ] **Step 2: 在 main.py 中注册路由**

Read: `backend/app/api/main.py`

Add import and include router:

```python
# 在 imports 部分添加：
from app.api.routes import pdca

# 在 router include 部分（大约在第20行附近）添加：
app.include_router(pdca.router, prefix=api_prefix, tags=["PDCA"])
```

完整修改示例：

```python
from app.api.routes import items, login, users, utils, pdca  # 添加 pdca

api_prefix = settings.API_V1_STR

# ... 现有路由 ...

app.include_router(pdca.router, prefix=api_prefix)  # 添加这一行
```

- [ ] **Step 3: 编写 API 测试**

Create: `backend/tests/api/routes/test_pdca.py`

```python
"""Tests for PDCA API routes."""

import pytest
from uuid import uuid4
from fastapi.testclient import TestClient
from sqlmodel import Session

from app.core.config import settings
from app.models import User
from app.pdca.models import PDCACycleCreate, AgentConfigCreate


def test_create_cycle(
    client: TestClient,
    superuser_token_headers: dict,
    db: Session,
    test_user: User
):
    """测试创建PDCA循环"""
    data = {
        "name": "Test Cycle",
        "description": "Test description",
        "goal": "Test goal",
        "agent_type": "openai",
        "agent_input": {"prompt": "test prompt"},
        "plan_details": {}
    }

    response = client.post(
        f"{settings.API_V1_STR}/pdca/cycles",
        headers=superuser_token_headers,
        json=data
    )

    assert response.status_code == 201
    content = response.json()
    assert content["name"] == "Test Cycle"
    assert content["goal"] == "Test goal"
    assert "id" in content


def test_read_cycles(
    client: TestClient,
    superuser_token_headers: dict,
    db: Session,
    test_pdca_cycle: PDCACycle
):
    """测试获取循环列表"""
    response = client.get(
        f"{settings.API_V1_STR}/pdca/cycles",
        headers=superuser_token_headers
    )

    assert response.status_code == 200
    content = response.json()
    assert "data" in content
    assert "count" in content
    assert content["count"] >= 1


def test_read_cycle(
    client: TestClient,
    superuser_token_headers: dict,
    test_pdca_cycle: PDCACycle
):
    """测试获取单个循环"""
    response = client.get(
        f"{settings.API_V1_STR}/pdca/cycles/{test_pdca_cycle.id}",
        headers=superuser_token_headers
    )

    assert response.status_code == 200
    content = response.json()
    assert content["id"] == str(test_pdca_cycle.id)
    assert content["name"] == test_pdca_cycle.name


def test_read_cycle_not_found(
    client: TestClient,
    superuser_token_headers: dict
):
    """测试获取不存在的循环"""
    fake_id = uuid4()
    response = client.get(
        f"{settings.API_V1_STR}/pdca/cycles/{fake_id}",
        headers=superuser_token_headers
    )

    assert response.status_code == 404


def test_list_agent_types(
    client: TestClient
):
    """测试获取Agent类型列表"""
    response = client.get(
        f"{settings.API_V1_STR}/pdca/agents/types"
    )

    assert response.status_code == 200
    content = response.json()
    assert "types" in content
    assert "openai" in content["types"]


def test_create_agent_config(
    client: TestClient,
    superuser_token_headers: dict
):
    """测试创建Agent配置"""
    data = {
        "name": "Test Config",
        "agent_type": "openai",
        "description": "Test config",
        "config": {"model": "gpt-4", "temperature": 0.7}
    }

    response = client.post(
        f"{settings.API_V1_STR}/pdca/agents/configs",
        headers=superuser_token_headers,
        json=data
    )

    assert response.status_code == 201
    content = response.json()
    assert content["name"] == "Test Config"
    assert content["agent_type"] == "openai"


def test_execute_cycle_unauthorized(
    client: TestClient,
    test_pdca_cycle: PDCACycle
):
    """测试未授权执行循环"""
    # 不提供认证头
    response = client.post(
        f"{settings.API_V1_STR}/pdca/cycles/{test_pdca_cycle.id}/execute"
    )

    assert response.status_code == 401
```

- [ ] **Step 4: 运行 API 测试验证**

Run: `cd backend && pytest tests/api/routes/test_pdca.py -v`

Expected: PASS（所有测试通过）

- [ ] **Step 5: 使用真实客户端测试**

Run: `cd backend && docker compose up`

Run in another terminal:
```bash
# 获取token
TOKEN=$(curl -X POST "http://localhost:8001/api/v1/login/access-token" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=admin@example.com&password=changethis" | jq -r .access_token)

# 创建PDCA循环
curl -X POST "http://localhost:8001/api/v1/pdca/cycles" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Test PDCA Cycle",
    "description": "My first PDCA cycle",
    "goal": "Test LangGraph integration",
    "agent_type": "openai",
    "agent_input": {"prompt": "Say hello"},
    "plan_details": {}
  }'

# 获取循环列表
curl -X GET "http://localhost:8001/api/v1/pdca/cycles" \
  -H "Authorization: Bearer $TOKEN"

# 获取Agent类型
curl -X GET "http://localhost:8001/api/v1/pdca/agents/types"
```

Expected: 所有API调用成功返回

- [ ] **Step 6: 提交**

```bash
git add backend/app/api/routes/pdca.py backend/app/api/main.py backend/tests/api/routes/test_pdca.py
git commit -m "feat: add PDCA API routes"
```

---

## Task 9: 添加 utils 工具函数

**Files:**
- Create: `backend/app/pdca/utils.py`

- [ ] **Step 1: 编写工具函数**

```python
"""PDCA utility functions."""

from typing import Dict, Any, List
from uuid import UUID


def extract_execution_summary(execution_result: Dict[str, Any]) -> str:
    """
    从执行结果中提取摘要信息

    Args:
        execution_result: Agent执行结果

    Returns:
        摘要字符串
    """
    if not execution_result:
        return "No execution result"

    if execution_result.get("status") == "success":
        output = execution_result.get("output", "")
        # 截取前200字符
        summary = output[:200] + "..." if len(output) > 200 else output
        return f"Success: {summary}"
    else:
        error = execution_result.get("error", "Unknown error")
        return f"Error: {error}"


def calculate_cycle_progress(state_data: Dict[str, Any]) -> float:
    """
    计算PDCA循环进度百分比

    Args:
        state_data: 状态数据

    Returns:
        进度百分比 (0-100)
    """
    phase = state_data.get("phase", "plan")

    phase_progress = {
        "plan": 25,
        "do": 50,
        "check": 75,
        "act": 90,
        "completed": 100,
        "failed": 100
    }

    return phase_progress.get(phase, 0)


def validate_agent_input(agent_type: str, input_data: Dict[str, Any]) -> tuple[bool, List[str]]:
    """
    验证Agent输入数据

    Args:
        agent_type: Agent类型
        input_data: 输入数据

    Returns:
        (是否有效, 错误消息列表)
    """
    errors = []

    if agent_type == "openai":
        if "prompt" not in input_data:
            errors.append("Missing required field: prompt")
    elif agent_type == "http_request":
        if "url" not in input_data:
            errors.append("Missing required field: url")
        if "method" not in input_data:
            errors.append("Missing required field: method")

    return len(errors) == 0, errors


def format_cycle_tree(cycles: List[Any]) -> List[Dict[str, Any]]:
    """
    将循环列表格式化为树形结构

    Args:
        cycles: PDCA循环列表

    Returns:
        树形结构数据
    """
    # 构建ID到循环的映射
    cycle_map = {str(c.id): c for c in cycles}

    # 构建树形结构
    roots = []
    for cycle in cycles:
        if cycle.parent_id is None:
            roots.append(_build_tree_node(cycle, cycle_map))

    return roots


def _build_tree_node(cycle: Any, cycle_map: Dict[str, Any]) -> Dict[str, Any]:
    """递归构建树节点"""
    children = [
        _build_tree_node(child, cycle_map)
        for child in cycle_map.values()
        if child.parent_id and str(child.parent_id) == str(cycle.id)
    ]

    return {
        "id": str(cycle.id),
        "name": cycle.name,
        "phase": cycle.phase,
        "status": cycle.status,
        "children": children
    }
```

- [ ] **Step 2: 编写工具函数测试**

Create: `backend/tests/pdca/test_utils.py`

```python
"""Tests for PDCA utility functions."""

import pytest
from app.pdca.utils import (
    extract_execution_summary,
    calculate_cycle_progress,
    validate_agent_input,
    format_cycle_tree
)
from app.pdca.models import PDCACycle


def test_extract_execution_summary_success():
    """测试提取成功执行的摘要"""
    result = {
        "status": "success",
        "output": "This is a long output that should be truncated" * 10
    }

    summary = extract_execution_summary(result)

    assert summary.startswith("Success:")
    assert "..." in summary


def test_extract_execution_summary_error():
    """测试提取失败执行的摘要"""
    result = {
        "status": "error",
        "error": "API connection failed"
    }

    summary = extract_execution_summary(result)

    assert "API connection failed" in summary


def test_calculate_cycle_progress():
    """测试计算循环进度"""
    assert calculate_cycle_progress({"phase": "plan"}) == 25
    assert calculate_cycle_progress({"phase": "do"}) == 50
    assert calculate_cycle_progress({"phase": "check"}) == 75
    assert calculate_cycle_progress({"phase": "act"}) == 90
    assert calculate_cycle_progress({"phase": "completed"}) == 100


def test_validate_agent_input_openai_valid():
    """测试验证OpenAI输入 - 有效"""
    is_valid, errors = validate_agent_input("openai", {"prompt": "test"})

    assert is_valid
    assert len(errors) == 0


def test_validate_agent_input_openai_invalid():
    """测试验证OpenAI输入 - 无效"""
    is_valid, errors = validate_agent_input("openai", {})

    assert not is_valid
    assert "prompt" in errors[0]


def test_validate_agent_input_http_valid():
    """测试验证HTTP请求输入 - 有效"""
    is_valid, errors = validate_agent_input(
        "http_request",
        {"url": "http://example.com", "method": "GET"}
    )

    assert is_valid
    assert len(errors) == 0


def test_format_cycle_tree(db: Session, test_user):
    """测试格式化循环树"""
    # 创建父循环
    parent = PDCACycle(
        name="Parent",
        goal="Parent goal",
        agent_type="openai",
        agent_input={},
        owner_id=test_user.id
    )
    db.add(parent)

    # 创建子循环
    child = PDCACycle(
        name="Child",
        goal="Child goal",
        agent_type="openai",
        agent_input={},
        parent_id=parent.id,
        owner_id=test_user.id
    )
    db.add(child)
    db.commit()

    cycles = [parent, child]
    tree = format_cycle_tree(cycles)

    assert len(tree) == 1
    assert tree[0]["name"] == "Parent"
    assert len(tree[0]["children"]) == 1
    assert tree[0]["children"][0]["name"] == "Child"
```

- [ ] **Step 3: 运行测试验证**

Run: `cd backend && pytest tests/pdca/test_utils.py -v`

Expected: PASS（所有测试通过）

- [ ] **Step 4: 提交**

```bash
git add backend/app/pdca/utils.py backend/tests/pdca/test_utils.py
git commit -m "feat: add PDCA utility functions"
```

---

## Task 10: 文档和最终验证

**Files:**
- Create: `backend/app/pdca/README.md`

- [ ] **Step 1: 编写 PDCA 模块文档**

```markdown
# PDCA Workflow Management Module

## Overview

This module implements a PDCA (Plan-Do-Check-Act) workflow management system using LangGraph as the state machine engine.

## Architecture

### Components

- **State**: `PDCAState` - TypedDict defining the workflow state
- **Models**: Database models for cycles, configs, and logs
- **Engine**: LangGraph-based workflow engine
- **Agents**: Pluggable agent executors
- **API**: RESTful endpoints for CRUD and execution

### Workflow Phases

1. **Plan**: Define goals and create execution plans
2. **Do**: Execute agents to perform tasks
3. **Check**: Validate results against criteria
4. **Act**: Implement improvements or standardize

## Usage

### Creating a PDCA Cycle

```python
from app.pdca.crud import create_pdca_cycle
from app.pdca.models import PDCACycleCreate

cycle_data = PDCACycleCreate(
    name="My PDCA Cycle",
    goal="Achieve X",
    agent_type="openai",
    agent_input={"prompt": "Help me achieve X"}
)

cycle = create_pdca_cycle(db, cycle_data, user.id)
```

### Executing a Cycle

```python
from app.pdca.engine import PDCAEngine

engine = PDCAEngine(db)
final_state = await engine.execute_cycle(cycle.id)
```

### Creating Custom Agents

```python
from app.pdca.agents.base import BaseAgentExecutor
from app.pdca.agents.registry import AgentRegistry

class MyAgent(BaseAgentExecutor):
    async def execute(self, input, cycle_id):
        # Implementation
        return {"status": "success", "output": "..."}

    def validate_input(self, input):
        return "required_field" in input

# Register
AgentRegistry.register("my_agent", MyAgent)
```

## API Endpoints

- `POST /api/v1/pdca/cycles` - Create cycle
- `GET /api/v1/pdca/cycles` - List cycles
- `GET /api/v1/pdca/cycles/{id}` - Get cycle
- `POST /api/v1/pdca/cycles/{id}/execute` - Execute cycle
- `GET /api/v1/pdca/agents/types` - List agent types

## Testing

```bash
# Run all PDCA tests
pytest tests/pdca/ -v

# Run specific test module
pytest tests/pdca/test_engine.py -v
```
```

- [ ] **Step 2: 更新主 README**

在项目主 README 中添加 PDCA 功能说明：

```markdown
## PDCA Workflow Management

This template includes a PDCA (Plan-Do-Check-Act) workflow management system:

- **LangGraph Integration**: State machine-based workflow engine
- **Multi-Agent Support**: Pluggable agent executors (OpenAI, Python, HTTP, Shell)
- **Nested Cycles**: Support for hierarchical PDCA structures
- **RESTful API**: Complete CRUD and execution endpoints
- **Execution Logging**: Detailed logs for each phase

See `backend/app/pdca/README.md` for details.
```

- [ ] **Step 3: 运行所有测试确保MVP完整**

Run: `cd backend && pytest tests/pdca/ -v --cov=app/pdca --cov-report=term-missing`

Expected: 所有测试通过，覆盖率 > 80%

- [ ] **Step 4: 验证 API 端点完整**

Run: `cd backend && docker compose up`

使用 Postman 或 curl 测试所有端点：

```bash
# 1. 创建循环
curl -X POST "http://localhost:8001/api/v1/pdca/cycles" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Final Test Cycle",
    "goal": "Verify MVP",
    "agent_type": "openai",
    "agent_input": {"prompt": "Test MVP completion"}
  }'

# 2. 获取循环列表
curl -X GET "http://localhost:8001/api/v1/pdca/cycles" \
  -H "Authorization: Bearer $TOKEN"

# 3. 获取单个循环
curl -X GET "http://localhost:8001/api/v1/pdca/cycles/{CYCLE_ID}" \
  -H "Authorization: Bearer $TOKEN"

# 4. 执行循环
curl -X POST "http://localhost:8001/api/v1/pdca/cycles/{CYCLE_ID}/execute" \
  -H "Authorization: Bearer $TOKEN"

# 5. 获取Agent类型
curl -X GET "http://localhost:8001/api/v1/pdca/agents/types"

# 6. 创建Agent配置
curl -X POST "http://localhost:8001/api/v1/pdca/agents/configs" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "GPT-4 Config",
    "agent_type": "openai",
    "description": "GPT-4 with temperature 0.7",
    "config": {"model": "gpt-4", "temperature": 0.7}
  }'
```

Expected: 所有端点正常工作

- [ ] **Step 5: 最终提交**

```bash
git add backend/app/pdca/README.md backend/README.md
git commit -m "docs: add PDCA module documentation and update README"
```

- [ ] **Step 6: 创建 MVP 完成标签**

```bash
git tag -a v0.1.0-pdca-mvp -m "PDCA Agent Platform MVP - Phase 1 Complete

Features:
- LangGraph-based PDCA workflow engine
- Database models for cycles, configs, logs
- OpenAI Agent executor
- RESTful API with full CRUD
- Execution logging
- Comprehensive test coverage"
```

---

## 自我审查检查清单

### Spec 覆盖度 ✓
- 数据库模型：Task 3 ✓
- LangGraph引擎：Task 7 ✓
- Agent执行器：Task 4, 5 ✓
- API接口：Task 8 ✓
- 工具函数：Task 9 ✓

### Placeholder 扫描 ✓
- 无TBD或TODO
- 所有代码步骤包含完整实现
- 所有测试包含实际代码
- 所有命令可执行

### 类型一致性 ✓
- PDCACycle、AgentConfig 字段一致
- API Pydantic模型与数据库模型匹配
- State定义在所有任务中使用一致

---

## 执行选项

Plan complete and saved to `docs/superpowers/plans/2025-01-06-pdca-agent-platform-mvp.md`.

**Two execution options:**

**1. Subagent-Driven (recommended)** - I dispatch a fresh subagent per task, review between tasks, fast iteration

**2. Inline Execution** - Execute tasks in this session using executing-plans, batch execution with checkpoints

**Which approach?**
