# PDCA 前端设计文档

## 概述

为 PDCA Agent Platform 设计和实现完整的 React 前端界面，支持 PDCA 循环的管理、执行、监控和分析。

**设计日期**: 2025-01-06
**状态**: 设计阶段

---

## 目标

为已完成的 PDCA 后端 API 创建功能完整、用户体验优秀的前端界面，使非技术用户也能轻松使用 PDCA 工作流管理系统。

---

## 核心功能

### 1. PDCA 循环管理（基础）
- 查看所有 PDCA 循环的树形结构
- 创建新循环（三步向导）
- 查看循环详细信息
- 编辑和删除循环
- 查看子循环关系

### 2. 执行与监控（核心）
- 启动 PDCA 循环执行
- 实时查看执行进度
- 监控四个阶段（Plan-Do-Check-Act）
- 查看详细执行日志
- 控制执行（取消、暂停、重试）
- 查看资源使用情况（执行时间、Token 消耗）

### 3. 分析功能（增强）
- 单个循环的详细分析
- 性能指标和趋势
- 父子循环对比
- 执行历史统计

---

## 架构设计

### 整体架构

```
┌─────────────────────────────────────────────────────┐
│                    侧边栏导航                          │
│  📊 PDCA 循环  │  📁 Items  │  📂 Files  │  ⚙️ Settings│
└─────────────────────────────────────────────────────┘
┌─────────────────────────────────────────────────────┐
│                     主内容区                          │
│  ┌──────────────────┐          ┌──────────────────┐ │
│  │   树形视图区域    │          │   详情抽屉        │ │
│  │  (左侧 45%)      │◀─────────│   (右侧 55%)      │ │
│  │                  │  点击     │                  │ │
│  │  🌳 循环层级     │          │  📋 详情选项卡    │ │
│  │     结构         │          │  ▶️ 执行选项卡    │ │
│  │                  │          │  📊 分析选项卡    │ │
│  │  [新建循环]      │          │  📝 日志选项卡    │ │
│  └──────────────────┘          │  👶 子循环选项卡  │ │
│                                └──────────────────┘ │
└─────────────────────────────────────────────────────┘
```

### 技术栈

- **框架**: React 19 + TypeScript
- **路由**: TanStack Router
- **状态管理**: TanStack Query (服务端) + React Context (本地)
- **UI 库**: Radix UI + Tailwind CSS
- **表单**: React Hook Form + Zod
- **数据获取**: 自动生成的 API 客户端 (@/client)
- **图表**: Recharts
- **实时更新**: 轮询 (未来可升级到 WebSocket)

---

## 页面结构

### 主路由

```
/_layout/pdca
```

### 抽屉选项卡

每个抽屉包含 5 个选项卡：

1. **详情** - 基本信息、PDCA 进度条、编辑/删除按钮
2. **执行** - 执行按钮、实时监控、资源使用、控制按钮
3. **分析** - 单个循环的详细分析、性能指标、对比数据
4. **日志** - 完整的执行日志、时间线
5. **子循环** - 子循环列表和状态

---

## 组件设计

### 1. CycleTree（树形视图）

**职责**: 显示 PDCA 循环的层级结构

**Props**:
```typescript
interface CycleTreeProps {
  cycles: PDCACycle[];
  onSelectCycle: (cycle: PDCACycle) => void;
  selectedId?: string;
}
```

**功能**:
- 递归渲染父子关系
- 显示状态标签（待开始、进行中、已完成）
- 点击节点触发回调
- 支持展开/折叠

**状态映射**:
- `pending` → 灰色标签 "待开始"
- `running` → 蓝色标签 "进行中"
- `completed` → 绿色标签 "已完成"
- `failed` → 红色标签 "失败"

### 2. CycleDrawer（详情抽屉）

**职责**: 显示选中循环的详细信息

**Props**:
```typescript
interface CycleDrawerProps {
  cycle: PDCACycle | null;
  isOpen: boolean;
  onClose: () => void;
  onExecute?: (cycleId: string) => void;
}
```

**功能**:
- 从右侧滑出（宽度 55%）
- 5 个选项卡（Tabs）
- 底部操作按钮
- 响应式设计（移动端全屏）

### 3. CreateWizard（创建向导）

**职责**: 三步创建新 PDCA 循环

**步骤**:
1. **基本信息** - 名称、目标、父循环、描述
2. **Agent 配置** - Agent 类型选择、Prompt 输入
3. **高级选项** - 检查标准、优先级、预计时间、标签

**Props**:
```typescript
interface CreateWizardProps {
  isOpen: boolean;
  onClose: () => void;
  onSuccess: () => void;
}
```

**验证规则**:
- 名称：必填，3-100 字符
- 目标：必填，10-500 字符
- Agent 类型：必选（默认 openai）
- Prompt：必填，如果 Agent 类型是 openai

### 4. ExecutionMonitor（执行监控）

**职责**: 实时显示 PDCA 执行状态

**状态**:
- `idle` - 未开始
- `running` - 执行中（显示脉冲动画）
- `completed` - 已完成（显示绿色勾）
- `failed` - 失败（显示红色叉）

**显示内容**:
- 当前阶段和进度百分比
- 水平进度条（Plan-Do-Check-Act）
- 资源使用（执行时间、Token 数量、重试次数）
- 实时日志（带颜色标记和时间戳）
- 控制按钮（取消、暂停、重试）

**轮询策略**:
- 执行中：每 2 秒轮询一次
- 暂停后：停止轮询

### 5. ProgressBar（PDCA 进度条）

**职责**: 显示 PDCA 四阶段进度

**Props**:
```typescript
interface ProgressBarProps {
  phase: 'plan' | 'do' | 'check' | 'act' | 'completed' | 'failed';
  status: 'pending' | 'running' | 'completed' | 'failed';
}
```

**阶段映射**:
- `plan` → 25%
- `do` → 50%
- `check` → 75%
- `act` → 90%
- `completed` → 100%

### 6. AnalyticsTab（分析选项卡）

**职责**: 显示单个循环的详细分析

**显示内容**:
- 执行时间趋势图
- Token 使用量
- 阶段完成率
- 与父循环的对比
- 历史执行记录

---

## 数据流

### 1. 获取循环列表

```
用户进入页面
  → useSuspenseQuery(['pdca-cycles'])
  → GET /api/v1/pdca/cycles
  → 渲染 CycleTree
```

### 2. 查看循环详情

```
用户点击树节点
  → setCycle(cycle)
  → 抽屉打开
  → useQuery(['pdca-cycle', id])
  → GET /api/v1/pdca/cycles/{id}
  → 渲染详情选项卡
```

### 3. 执行循环

```
用户点击执行按钮
  → executeCycle(cycleId)
  → POST /api/v1/pdca/cycles/{id}/execute
  → 开始轮询状态
  → GET /api/v1/pdca/cycles/{id} (每 2 秒)
  → 更新 ExecutionMonitor
  → 完成后停止轮询
```

### 4. 创建循环

```
用户点击新建按钮
  → 打开 CreateWizard
  → 三步表单填写
  → POST /api/v1/pdca/cycles
  → 成功后刷新列表
  → 关闭向导
```

---

## 错误处理

### 网络错误
- 显示 toast 通知（使用 sonner）
- 提供重试按钮
- 保持本地状态不变

### 验证错误
- 实时显示字段错误
- 禁用提交按钮直到有效
- 清晰的错误消息

### 执行失败
- 在 ExecutionMonitor 中显示错误信息
- 允许重试
- 记录到日志选项卡

---

## API 集成

### 使用自动生成的客户端

```typescript
import { pdcaReadCycles, pdcaExecuteCycle } from "@/client/services.gen";

// 获取循环列表
const { data } = useSuspenseQuery({
  queryKey: ['pdca-cycles'],
  queryFn: async () => {
    const response = await pdcaReadCycles({
      query: { skip: 0, limit: 100 }
    });
    if (response.error) throw response.error;
    return response.data;
  }
});

// 执行循环
const execute = async (id: string) => {
  const response = await pdcaExecuteCycle({
    path: { cycle_id: id }
  });
  if (response.error) {
    toast.error('执行失败: ' + response.error.detail);
  } else {
    toast.success('执行已启动');
  }
};
```

---

## 性能优化

### 1. 缓存策略
- 使用 TanStack Query 的默认缓存
- 列表数据缓存 5 分钟
- 详情数据缓存 1 分钟

### 2. 懒加载
- 抽屉内容懒加载
- 分析选项卡按需加载

### 3. 防抖/节流
- 树节点点击防抖（300ms）
- 搜索输入节流（500ms）

---

## 文件组织

```
frontend/src/
├── routes/
│   └── _layout/
│       └── pdca.tsx                    # PDCA 主页面
├── components/
│   └── PDCA/
│       ├── CycleTree.tsx               # 树形视图组件
│       ├── CycleDrawer.tsx             # 详情抽屉
│       ├── CreateWizard/
│       │   ├── index.tsx               # 向导主组件
│       │   ├── Step1BasicInfo.tsx      # 步骤 1：基本信息
│       │   ├── Step2AgentConfig.tsx    # 步骤 2：Agent 配置
│       │   └── Step3Advanced.tsx       # 步骤 3：高级选项
│       ├── ExecutionMonitor.tsx         # 执行监控
│       ├── ProgressBar.tsx              # PDCA 进度条组件
│       ├── AnalyticsTab.tsx             # 分析选项卡
│       ├── LogsTab.tsx                  # 日志选项卡
│       ├── ChildrenTab.tsx              # 子循环选项卡
│       └── DetailTab.tsx                # 详情选项卡
├── hooks/
│   ├── usePdcaExecution.ts              # 执行状态管理
│   └── useCycleTree.ts                 # 树形数据管理
└── lib/
    └── pdca-utils.ts                   # PDCA 工具函数
```

---

## 实现优先级

### Phase 1: 核心（必须）
1. 主页面布局 + 树形视图
2. 详情抽屉（详情选项卡）
3. 创建向导
4. 基本的 CRUD 操作

### Phase 2: 执行（重要）
5. 执行选项卡 + 执行监控
6. 实时日志显示
7. PDCA 进度条

### Phase 3: 增强（可选）
8. 分析选项卡
9. 日志选项卡
10. 子循环选项卡
11. 数据可视化图表

---

## 设计原则

1. **一致性** - 遵循现有项目的 UI/UX 模式
2. **简洁性** - 避免过度设计，保持界面清晰
3. **可访问性** - 支持键盘导航，提供适当的 ARIA 标签
4. **响应式** - 支持移动端和桌面端
5. **性能** - 快速加载，流畅交互

---

## 未来增强

1. **WebSocket 支持** - 真正的实时更新（而非轮询）
2. **批量操作** - 多选循环进行批量执行/删除
3. **搜索和过滤** - 按状态、日期、标签过滤循环
4. **导出功能** - 导出执行报告为 PDF/CSV
5. **协作功能** - 评论、@提及、共享循环
