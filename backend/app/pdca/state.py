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