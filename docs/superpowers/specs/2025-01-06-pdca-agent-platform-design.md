# PDCA Agent平台设计文档

**日期：** 2025-01-06
**状态：** 待用户审批

---

## 1. 项目概述

构建一个以PDCA（Plan-Do-Check-Act）方法论为核心的Agent流程管理平台，所有Agent和Workflow的执行都遵循PDCA循环。

### 1.1 核心需求

- **PDCA流程管理平台**：以PDCA循环为核心进行流程管理
- **分层级嵌套PDCA**：支持多个PDCA循环并行或嵌套，支持不同粒度的管理
- **Agent作为执行单元**：Agent是Do阶段的执行者
- **多Agent类型**：支持OpenAI Agent、Python脚本、HTTP请求、Shell命令等
- **前端可视化**：提供PDCA树形结构、执行状态、日志的可视化界面
- **人工审批**：支持用户在Check阶段审批检查结果
- **调度与编排**：支持Agent调度、并发执行、重试机制、超时控制

### 1.2 技术选型

- **工作流引擎**：LangGraph（状态机、循环、嵌套图、人工审批）
- **后端框架**：FastAPI + SQLModel + PostgreSQL
- **前端框架**：React + TypeScript + Tailwind CSS + shadcn/ui
- **LLM集成**：LangChain + OpenAI
- **任务队列**：Celery + Redis（可选，用于异步任务）

---

## 2. 系统架构

### 2.1 整体架构图

```
┌─────────────────────────────────────────────────────────────┐
│                    Frontend (React)                         │
│  - PDCA树形可视化 (使用LangGraph的可视化)                    │
│  - 人工审批界面                                              │
│  - 执行状态监控                                              │
└─────────────────────────────────────────────────────────────┘
                          ↓ HTTP/WebSocket
┌─────────────────────────────────────────────────────────────┐
│                     API Layer (FastAPI)                     │
│  /api/v1/pdca/cycles/       - PDCA循环CRUD                  │
│  /api/v1/pdca/execute/      - 启动PDCA执行                  │
│  /api/v1/pdca/approve/      - 人工审批端点                  │
│  /api/v1/agents/            - Agent配置管理                 │
└─────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────┐
│                  PDCA Service Layer                         │
│  - PDCACycleService (循环管理)                              │
│  - AgentExecutorService (Agent执行)                         │
│  - ApprovalService (审批服务)                               │
└─────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────┐
│              LangGraph PDCA Engine                          │
│                                                             │
│  ┌─────────────────────────────────────────────────┐       │
│  │         StateGraph[PDCAState]                   │       │
│  │                                                 │       │
│  │   ┌──────┐    ┌──────┐    ┌──────┐    ┌──────┐│       │
│  │   │ Plan │ → │  Do  │ → │Check │ → │ Act  ││       │
│  │   └──────┘    └──────┘    └──────┘    └──────┘│       │
│  │        ↓           ↓           ↓           ↓    │       │
│  │    (嵌套子图)  (Agent执行) (人工审批)  (改进)  │       │
│  └─────────────────────────────────────────────────┘       │
│                                                             │
│  CheckpointSaver (PostgreSQL) - 状态持久化                 │
└─────────────────────────────────────────────────────────────┘
                          ↓
┌───────────────────────┬───────────────────────────────────┐
│    Agent Registry     │    LangChain Ecosystem            │
│  - OpenAI Agent       │  - LLM调用                         │
│  - Python Script      │  - Tool调用                       │
│  - HTTP Request       │  - Memory管理                     │
│  - Shell Command      │                                   │
└───────────────────────┴───────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────┐
│              Database (PostgreSQL)                          │
│  - pdca_cycle (循环表)                                      │
│  - pdca_checkpoint (LangGraph状态快照)                     │
│  - agent_config (Agent配置)                                │
│  - execution_log (执行日志)                                │
└─────────────────────────────────────────────────────────────┘
```

---

## 3. 数据模型设计

### 3.1 核心数据结构

```python
from typing import TypedDict, Optional, Dict, List, Any, Literal
from datetime import datetime
from uuid import UUID, uuid4

# PDCA循环状态（LangGraph State）
class PDCAState(TypedDict):
    """PDCA循环的状态定义"""
    id: str                          # 循环ID
    parent_id: Optional[str]         # 父循环ID（支持嵌套）
    phase: Literal["plan", "do", "check", "act", "completed", "failed"]

    # Plan阶段数据
    goal: str                        # 目标描述
    plan_details: Dict               # 计划详情

    # Do阶段数据
    agent_type: str                  # Agent类型
    agent_input: Dict                # Agent输入
    execution_result: Optional[Dict] # 执行结果

    # Check阶段数据
    check_criteria: Dict             # 检查标准
    check_result: Optional[Dict]     # 检查结果
    passed: Optional[bool]           # 是否通过
    approval_status: Optional[str]   # 审批状态（pending/approved/rejected）

    # Act阶段数据
    improvement_actions: List[Dict]  # 改进措施

    # 元数据
    created_at: datetime
    updated_at: datetime
    error: Optional[str]
```

### 3.2 数据库模型

```python
from typing import Optional, List, TYPE_CHECKING
from datetime import datetime
from uuid import UUID, uuid4
from sqlmodel import SQLModel, Field, Relationship, Column
from sqlalchemy import JSON, ForeignKey

if TYPE_CHECKING:
    from .pdca_cycle import PDCACycle

class PDCACycle(SQLModel, table=True):
    """PDCA循环表"""
    __tablename__ = "pdca_cycle"

    id: Optional[UUID] = Field(default_factory=uuid4, primary_key=True)
    parent_id: Optional[UUID] = Field(
        default=None,
        foreign_key="pdca_cycle.id"
    )
    name: str = Field(index=True)
    description: Optional[str] = None
    phase: str = Field(default="plan")  # plan, do, check, act, completed, failed
    status: str = Field(default="pending")  # pending, running, waiting_approval, completed, failed

    # JSON字段存储状态数据
    state_data: Dict[str, Any] = Field(
        default={},
        sa_column=Column(JSON)
    )

    # Agent配置
    agent_type: Optional[str] = None
    agent_config_id: Optional[UUID] = Field(default=None)

    # 时间戳
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None

    # 错误信息
    error_message: Optional[str] = None

    # 关系
    children: List["PDCACycle"] = Relationship(
        back_populates="parent",
        sa_relationship_kwargs={"cascade": "all, delete-orphan"}
    )
    parent: Optional["PDCACycle"] = Relationship(back_populates="children")


class AgentConfig(SQLModel, table=True):
    """Agent配置表"""
    __tablename__ = "agent_config"

    id: Optional[UUID] = Field(default_factory=uuid4, primary_key=True)
    name: str = Field(index=True)
    agent_type: str  # openai, python_script, http_request, shell_command
    config: Dict[str, Any] = Field(sa_column=Column(JSON))
    description: Optional[str] = None

    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class Approval(SQLModel, table=True):
    """审批记录表"""
    __tablename__ = "approval"

    id: Optional[UUID] = Field(default_factory=uuid4, primary_key=True)
    cycle_id: UUID = Field(foreign_key="pdca_cycle.id")
    requester_id: UUID = Field(foreign_key="user.id")
    approver_id: Optional[UUID] = Field(foreign_key="user.id")

    check_result: Dict[str, Any] = Field(sa_column=Column(JSON))
    status: str = Field(default="pending")  # pending, approved, rejected
    comment: Optional[str] = None

    created_at: datetime = Field(default_factory=datetime.utcnow)
    reviewed_at: Optional[datetime] = None


class ExecutionLog(SQLModel, table=True):
    """执行日志表"""
    __tablename__ = "execution_log"

    id: Optional[UUID] = Field(default_factory=uuid4, primary_key=True)
    cycle_id: UUID = Field(foreign_key="pdca_cycle.id", index=True)
    phase: str
    level: str  # info, warning, error
    message: str
    metadata: Dict[str, Any] = Field(default={}, sa_column=Column(JSON))

    created_at: datetime = Field(default_factory=datetime.utcnow)
```

---

## 4. LangGraph引擎实现

### 4.1 核心引擎类

```python
# backend/app/pdca/engine.py

from typing import Dict, Any
from uuid import UUID
from datetime import datetime
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.postgres import PostgresCheckpointSaver
from sqlalchemy.ext.asyncio import AsyncSession

from .models import PDCAState
from .agents.registry import AgentRegistry
from .approval import ApprovalService

class PDCAEngine:
    """PDCA工作流引擎 - 基于LangGraph的状态机"""

    def __init__(self, db_session: AsyncSession):
        self.db_session = db_session
        self.checkpoint_saver = PostgresCheckpointSaver.from_conn_string(
            settings.DATABASE_URL
        )
        self.approval_service = ApprovalService(db_session)
        self.graph = self._build_graph()

    def _build_graph(self) -> StateGraph:
        """构建PDCA状态图"""
        workflow = StateGraph(PDCAState)

        # 添加节点
        workflow.add_node("plan_node", self._plan_node)
        workflow.add_node("do_node", self._do_node)
        workflow.add_node("check_node", self._check_node)
        workflow.add_node("act_node", self._act_node)

        # 定义入口
        workflow.set_entry_point("plan_node")

        # 定义边（状态转换）
        workflow.add_edge("plan_node", "do_node")
        workflow.add_edge("do_node", "check_node")

        # Check节点的条件分支
        workflow.add_conditional_edges(
            "check_node",
            self._should_continue_or_improve,
            {
                "continue": END,           # 检查通过，结束
                "improve": "act_node"      # 需要改进，进入Act
            }
        )

        # Act节点的条件分支
        workflow.add_conditional_edges(
            "act_node",
            self._should_create_child_cycle,
            {
                "create_child": "plan_node",  # 创建子循环
                "end": END
            }
        )

        return workflow.compile(
            checkpointer=self.checkpoint_saver
        )

    async def _plan_node(self, state: PDCAState) -> PDCAState:
        """Plan阶段：定义目标、制定计划"""
        # 1. 如果有子循环，先等待子循环完成
        if state.get("has_children"):
            await self._wait_for_children(state)

        # 2. 解析计划输入
        plan_details = await self._generate_plan(state)

        # 3. 创建子循环（如果需要分解）
        child_cycles = await self._create_child_cycles_if_needed(
            state, plan_details
        )

        return {
            **state,
            "phase": "plan",
            "plan_details": plan_details,
            "has_children": len(child_cycles) > 0
        }

    async def _do_node(self, state: PDCAState) -> PDCAState:
        """Do阶段：执行Agent"""
        agent_type = state.get("agent_type")
        agent_input = state.get("agent_input")

        # 执行Agent
        agent_executor = AgentRegistry.get_executor(agent_type)
        execution_result = await agent_executor.execute(
            input=agent_input,
            cycle_id=state["id"]
        )

        return {
            **state,
            "phase": "do",
            "execution_result": execution_result,
            "updated_at": datetime.utcnow()
        }

    async def _check_node(self, state: PDCAState) -> PDCAState:
        """Check阶段：检查结果"""
        # 1. 自动检查
        auto_check = await self._auto_check(state)

        # 2. 如果需要人工审批
        if auto_check.get("requires_human_approval"):
            await self.approval_service.request_approval(
                cycle_id=state["id"],
                check_result=auto_check
            )
            return {
                **state,
                "phase": "check",
                "check_result": auto_check,
                "approval_status": "pending"
            }

        # 3. 自动决策
        passed = auto_check.get("passed", False)
        return {
            **state,
            "phase": "check",
            "check_result": auto_check,
            "passed": passed,
            "approval_status": "auto_approved" if passed else "auto_rejected"
        }

    async def _act_node(self, state: PDCAState) -> PDCAState:
        """Act阶段：改进措施"""
        # 1. 分析Check阶段的结果
        # 2. 生成改进措施
        improvements = await self._generate_improvements(state)

        # 3. 标准化成功的流程
        if state.get("passed"):
            await self._standardize_process(state)

        return {
            **state,
            "phase": "act",
            "improvement_actions": improvements
        }

    def _should_continue_or_improve(self, state: PDCAState) -> str:
        """Check节点的条件分支判断"""
        if state.get("passed") and state.get("approval_status") in ["auto_approved", "approved"]:
            return "continue"
        return "improve"

    def _should_create_child_cycle(self, state: PDCAState) -> str:
        """Act节点的条件分支判断"""
        if state.get("improvement_requires_new_cycle"):
            return "create_child"
        return "end"
```

### 4.2 Agent执行器接口

```python
# backend/app/pdca/agents/base.py

from abc import ABC, abstractmethod
from typing import Dict
from uuid import UUID

class BaseAgentExecutor(ABC):
    """Agent执行器基类"""

    @abstractmethod
    async def execute(self, input: Dict, cycle_id: UUID) -> Dict:
        """
        执行Agent任务

        Args:
            input: Agent输入参数
            cycle_id: PDCA循环ID

        Returns:
            执行结果字典，包含status和output/error
        """
        pass

    @abstractmethod
    def validate_input(self, input: Dict) -> bool:
        """验证输入参数"""
        pass

# backend/app/pdca/agents/openai_agent.py

from openai import AsyncOpenAI
from app.core.config import settings

class OpenAIAgentExecutor(BaseAgentExecutor):
    """OpenAI Agent执行器"""

    def __init__(self):
        self.client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)

    async def execute(self, input: Dict, cycle_id: UUID) -> Dict:
        prompt = input.get("prompt")
        model = input.get("model", "gpt-4")

        try:
            response = await self.client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": input.get("system_prompt", "")},
                    {"role": "user", "content": prompt}
                ],
                temperature=input.get("temperature", 0.7)
            )

            return {
                "status": "success",
                "output": response.choices[0].message.content,
                "usage": {
                    "prompt_tokens": response.usage.prompt_tokens,
                    "completion_tokens": response.usage.completion_tokens
                }
            }
        except Exception as e:
            return {
                "status": "error",
                "error": str(e)
            }

    def validate_input(self, input: Dict) -> bool:
        return "prompt" in input

# backend/app/pdca/agents/registry.py

from typing import Dict, Type

class AgentRegistry:
    """Agent注册表"""

    _executors: Dict[str, Type[BaseAgentExecutor]] = {
        "openai": OpenAIAgentExecutor,
        "python_script": PythonScriptExecutor,
        "http_request": HTTPRequestExecutor,
        "shell_command": ShellCommandExecutor
    }

    @classmethod
    def get_executor(cls, agent_type: str) -> BaseAgentExecutor:
        """获取Agent执行器实例"""
        executor_class = cls._executors.get(agent_type)
        if not executor_class:
            raise ValueError(f"Unknown agent type: {agent_type}")
        return executor_class()

    @classmethod
    def register_executor(cls, agent_type: str, executor_class: Type[BaseAgentExecutor]):
        """注册新的Agent执行器"""
        cls._executors[agent_type] = executor_class

    @classmethod
    def list_types(cls) -> List[str]:
        """列出所有支持的Agent类型"""
        return list(cls._executors.keys())
```

---

## 5. API接口设计

### 5.1 RESTful API端点

```python
# backend/app/api/routes/pdca.py

from fastapi import APIRouter, Depends, WebSocket
from uuid import UUID
from typing import List, Optional

router = APIRouter(prefix="/api/v1/pdca", tags=["PDCA"])

# ========== PDCA循环管理 ==========

@router.post("/cycles", response_model=PDCACycleRead)
async def create_cycle(
    cycle_data: PDCACycleCreate,
    current_user: User = Depends(get_current_user)
):
    """创建新的PDCA循环"""
    ...

@router.get("/cycles", response_model=List[PDCACycleRead])
async def list_cycles(
    parent_id: Optional[UUID] = None,
    phase: Optional[str] = None,
    status: Optional[str] = None,
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_user)
):
    """获取PDCA循环列表"""
    ...

@router.get("/cycles/{cycle_id}", response_model=PDCACycleRead)
async def get_cycle(
    cycle_id: UUID,
    current_user: User = Depends(get_current_user)
):
    """获取单个循环详情"""
    ...

@router.post("/cycles/{cycle_id}/execute")
async def execute_cycle(
    cycle_id: UUID,
    current_user: User = Depends(get_current_user)
):
    """启动PDCA循环执行"""
    engine = get_pdca_engine()
    config = {"configurable": {"thread_id": str(cycle_id)}}
    result = await engine.ainvoke(
        {"id": str(cycle_id), "phase": "plan"},
        config=config
    )
    return result

@router.get("/cycles/{cycle_id}/children", response_model=List[PDCACycleRead])
async def get_child_cycles(
    cycle_id: UUID,
    current_user: User = Depends(get_current_user)
):
    """获取子循环（树形结构）"""
    ...

@router.get("/cycles/{cycle_id}/state")
async def get_cycle_state(
    cycle_id: UUID,
    current_user: User = Depends(get_current_user)
):
    """获取LangGraph状态快照"""
    ...

# ========== 审批接口 ==========

@router.get("/cycles/{cycle_id}/approval", response_model=ApprovalRead)
async def get_approval_request(
    cycle_id: UUID,
    current_user: User = Depends(get_current_user)
):
    """获取待审批请求"""
    ...

@router.post("/approvals/{approval_id}/approve")
async def approve_cycle(
    approval_id: UUID,
    approved: bool,
    comment: Optional[str] = None,
    current_user: User = Depends(get_current_user)
):
    """审批PDCA循环"""
    ...

@router.get("/approvals/pending", response_model=List[ApprovalRead])
async def list_pending_approvals(
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_user)
):
    """获取待审批列表"""
    ...

# ========== Agent配置管理 ==========

@router.get("/agents/types", response_model=List[str])
async def list_agent_types():
    """获取支持的Agent类型"""
    return AgentRegistry.list_types()

@router.post("/agents/configs", response_model=AgentConfigRead)
async def create_agent_config(
    config: AgentConfigCreate,
    current_user: User = Depends(get_current_user)
):
    """创建Agent配置"""
    ...

@router.get("/agents/configs", response_model=List[AgentConfigRead])
async def list_agent_configs(
    agent_type: Optional[str] = None,
    current_user: User = Depends(get_current_user)
):
    """获取Agent配置列表"""
    ...

# ========== WebSocket ==========

@router.websocket("/ws/cycles/{cycle_id}")
async def cycle_updates(
    cycle_id: UUID,
    websocket: WebSocket
):
    """PDCA执行状态实时推送"""
    await websocket.accept()

    async for update in stream_cycle_updates(cycle_id):
        await websocket.send_json(update)
```

---

## 6. 前端架构设计

### 6.1 目录结构

```
frontend/src/features/pdca/
├── components/
│   ├── PDCAViewer.tsx          # PDCA树形可视化
│   ├── PDCANode.tsx            # 单个循环节点
│   ├── PhaseBadge.tsx          # 阶段标签
│   ├── ExecutionLog.tsx        # 执行日志
│   ├── ApprovalModal.tsx       # 审批弹窗
│   ├── AgentConfigForm.tsx     # Agent配置表单
│   └── CycleCreator.tsx        # 循环创建器
├── pages/
│   ├── PDCAListPage.tsx        # 循环列表页
│   ├── PDCADetailPage.tsx      # 循环详情页
│   └── AgentConfigPage.tsx     # Agent配置页
├── hooks/
│   ├── usePDCAExecution.ts     # 执行状态Hook
│   ├── useApproval.ts          # 审批Hook
│   └── usePCATree.ts           # 树形数据Hook
├── services/
│   └── pdcaApi.ts              # API调用
└── types/
    └── pdca.ts                 # TypeScript类型定义
```

### 6.2 核心组件示例

```typescript
// frontend/src/features/pdca/components/PDCAViewer.tsx

import { useQuery } from "@tanstack/react-query";
import { useWebSocket } from "@/hooks/useWebSocket";
import { PDCANode } from "./PDCANode";
import { PhaseBadge } from "./PhaseBadge";

interface PDCAViewerProps {
  cycleId: string;
}

export function PDCAViewer({ cycleId }: PDCAViewerProps) {
  const { data: cycle } = useQuery({
    queryKey: ["pdca", cycleId],
    queryFn: () => pdcaApi.getCycle(cycleId),
    refetchInterval: 5000  // 每5秒轮询
  });

  const { data: state } = useWebSocket(`/ws/cycles/${cycleId}`);

  if (!cycle) return <div>Loading...</div>;

  return (
    <div className="pdca-viewer">
      <div className="mb-4">
        <h2 className="text-2xl font-bold">{cycle.name}</h2>
        <PhaseBadge phase={cycle.phase} status={cycle.status} />
      </div>

      {/* 树形结构 */}
      <div className="border rounded-lg p-4">
        <Tree
          data={buildPDCATree(cycle)}
          renderNode={(node) => <PDCANode data={node} realtimeState={state} />}
        />
      </div>

      {/* 执行日志 */}
      <ExecutionLog logs={state?.logs || []} />
    </div>
  );
}

// frontend/src/features/pdca/components/ApprovalModal.tsx

interface ApprovalModalProps {
  approval: Approval;
  onApprove: (approved: boolean, comment?: string) => void;
}

export function ApprovalModal({ approval, onApprove }: ApprovalModalProps) {
  const [comment, setComment] = useState("");
  const [loading, setLoading] = useState(false);

  const handleApprove = async (approved: boolean) => {
    setLoading(true);
    try {
      await onApprove(approved, comment);
    } finally {
      setLoading(false);
    }
  };

  return (
    <Dialog open={true}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>审批PDCA循环</DialogTitle>
        </DialogHeader>

        <div className="py-4">
          <h3 className="font-semibold mb-2">检查结果</h3>
          <pre className="bg-gray-100 p-4 rounded">
            {JSON.stringify(approval.check_result, null, 2)}
          </pre>

          <Textarea
            placeholder="添加审批意见..."
            value={comment}
            onChange={(e) => setComment(e.target.value)}
            className="mt-4"
          />
        </div>

        <DialogFooter>
          <Button
            variant="destructive"
            onClick={() => handleApprove(false)}
            disabled={loading}
          >
            拒绝
          </Button>
          <Button
            onClick={() => handleApprove(true)}
            disabled={loading}
          >
            批准
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
```

---

## 7. 目录结构

### 7.1 后端目录

```
backend/app/
├── pdca/                          # PDCA模块
│   ├── __init__.py
│   ├── engine.py                  # LangGraph引擎
│   ├── models.py                  # PDCA数据模型
│   ├── crud.py                    # PDCA CRUD操作
│   ├── agents/                    # Agent执行器
│   │   ├── __init__.py
│   │   ├── base.py                # 基类
│   │   ├── openai_agent.py        # OpenAI Agent
│   │   ├── python_agent.py        # Python脚本
│   │   ├── http_agent.py          # HTTP请求
│   │   ├── shell_agent.py         # Shell命令
│   │   └── registry.py            # Agent注册表
│   ├── approval.py                # 审批服务
│   ├── checkpoints.py             # Checkpoint管理
│   └── utils.py                   # 工具函数
├── api/
│   └── routes/
│       ├── pdca.py                # PDCA API路由
│       ├── agents.py              # Agent配置API
│       └── approvals.py           # 审批API
└── core/
    └── config.py                  # 配置（添加LangGraph相关）
```

### 7.2 前端目录

```
frontend/src/
├── features/
│   └── pdca/
│       ├── components/            # PDCA组件
│       ├── pages/                 # PDCA页面
│       ├── hooks/                 # 自定义Hooks
│       ├── services/              # API服务
│       └── types/                 # 类型定义
└── router/
    └── index.tsx                  # 路由配置
```

---

## 8. 依赖项

### 8.1 后端依赖

```txt
# pyproject.toml 添加

[project.dependencies]
langgraph = "^0.2.0"
langchain = "^0.3.0"
langchain-openai = "^0.2.0"
openai = "^1.0.0"
celery = {version = "^5.3.0", optional = true}
redis = {version = "^5.0.0", optional = true}
```

### 8.2 环境变量

```env
# .env

# LangGraph Checkpoint
LANGGRAPH_CHECKPOINT_DATABASE_URL=postgresql+asyncpg://...

# OpenAI
OPENAI_API_KEY=sk-...

# Celery (可选)
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0
```

---

## 9. 实现优先级

### Phase 1: 核心引擎（MVP）
1. 数据库模型实现
2. LangGraph引擎基础实现
3. 基础API端点（CRUD）
4. 单个Agent执行器（OpenAI）

### Phase 2: 完整功能
1. 嵌套循环支持
2. 人工审批流程
3. 多Agent类型支持
4. 执行日志记录

### Phase 3: 前端界面
1. PDCA列表页
2. 详情页与树形可视化
3. 审批界面
4. 实时状态更新（WebSocket）

### Phase 4: 高级功能
1. 任务调度与重试
2. Agent配置管理
3. 性能优化
4. 监控与告警

---

## 10. 非功能性需求

### 10.1 性能
- 单个PDCA循环启动时间 < 1s
- 支持至少1000个并发循环
- WebSocket消息延迟 < 100ms

### 10.2 可靠性
- 所有状态持久化到PostgreSQL
- Agent执行失败自动重试（最多3次）
- 支持从任意checkpoint恢复

### 10.3 可扩展性
- 通过AgentRegistry轻松添加新的Agent类型
- LangGraph图结构可配置化
- 支持水平扩展（通过Celery）

### 10.4 安全性
- 所有API需要认证
- Agent执行沙箱化（Python脚本、Shell命令）
- 审批权限控制

---

## 11. 总结

本设计采用LangGraph作为核心工作流引擎，通过状态机模式实现PDCA循环的流程管理。核心特点：

1. **状态驱动**：使用LangGraph的StateGraph管理PDCA状态转换
2. **嵌套支持**：通过父子关系实现分层级嵌套
3. **人工审批**：集成审批服务，支持Check阶段的人工干预
4. **可扩展性**：Agent注册表模式，易于添加新的Agent类型
5. **持久化**：PostgreSQL checkpoint支持，状态可恢复

该设计充分利用了LangGraph的能力，同时保持了系统的简洁性和可维护性。
