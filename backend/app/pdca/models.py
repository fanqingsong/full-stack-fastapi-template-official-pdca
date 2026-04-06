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
    log_metadata: Dict[str, Any] = Field(
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
