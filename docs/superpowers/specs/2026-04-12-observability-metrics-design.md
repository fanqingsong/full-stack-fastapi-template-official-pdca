# 业务指标监控系统设计文档

**日期**: 2026-04-12
**项目**: Full Stack FastAPI Template - PDCA
**目标**: 为项目添加基于 Prometheus + Grafana 的业务指标监控系统

## 1. 概述

本设计旨在为现有的 FastAPI + React 全栈应用添加全面的业务指标监控能力，重点关注 PDCA 业务流程、AI Agent 调用、API 请求和基础设施四大类指标。

### 1.1 设计目标

- **全面性**: 覆盖从基础设施到业务层的完整监控视图
- **实时性**: 秒级指标采集和展示
- **可扩展性**: 易于添加新的指标和 Dashboard
- **非侵入性**: 指标收集不影响主业务流程性能
- **云原生**: 遵循 Prometheus + Grafana 的云原生最佳实践

### 1.2 技术选型

- **指标存储**: Prometheus 2.x
- **可视化**: Grafana 10.x
- **客户端库**: prometheus_client (Python)
- **部署方式**: Docker Compose 集成部署
- **指标保留**: 15 天（可配置）

## 2. 系统架构

### 2.1 整体架构图

```
┌─────────────────────────────────────────────────────────────┐
│                      Docker Compose                          │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  ┌──────────────┐    ┌──────────────┐                      │
│  │   FastAPI    │    │   React      │                      │
│  │              │    │   Frontend   │                      │
│  │  /metrics    │    │              │                      │
│  └──────┬───────┘    └──────────────┘                      │
│         │                                                   │
│         │            ┌──────────────┐                      │
│         └───────────▶│  Prometheus  │                      │
│         scrape       │              │                      │
│                      └──────┬───────┘                      │
│                             │                               │
│                             ▼                               │
│                      ┌──────────────┐                      │
│                      │   Grafana    │                      │
│                      │              │                      │
│                      │  Dashboards  │                      │
│                      └──────────────┘                      │
│                                                               │
└─────────────────────────────────────────────────────────────┘
```

### 2.2 数据流设计

```
应用层                    中间件层                    Prometheus
   │                          │                           │
   │  业务逻辑执行             │                           │
   │  └─> pdca.crud.create    │                           │
   │       └─> metrics.pdca_  │                           │
   │          cycles_created  │                           │
   │          .inc()          │                           │
   │                          │                           │
   │  AI 调用                  │                           │
   │  └─> agent.generate      │                           │
   │       └─> metrics.ai_    │                           │
   │          requests_total   │                           │
   │          .inc()           │                           │
   │                          │                           │
   │  HTTP 请求                │                           │
   │  └─> middleware           │                           │
   │       └─> metrics.http_   │                           │
   │          requests_total   │                           │
   │          .inc()           │                           │
   │                          │                           │
   │  GET /metrics             │                           │
   │  <────────────────────────┼─────────── scrape ────────┤
   │  返回 Prometheus 格式      │                           │
```

## 3. 指标定义

### 3.1 API 请求指标

| 指标名称 | 类型 | 标签 | 说明 |
|---------|------|------|------|
| `http_requests_total` | Counter | method, path, status | HTTP 请求总数 |
| `http_request_duration_seconds` | Histogram | method, path, status | 请求耗时分布 |
| `http_requests_active` | Gauge | path | 当前活跃请求数 |

**用途**: 监控 API 性能、识别慢接口、追踪错误率

### 3.2 PDCA 业务指标

| 指标名称 | 类型 | 标签 | 说明 |
|---------|------|------|------|
| `pdca_cycles_created_total` | Counter | user_id, department | PDCA 循环创建总数 |
| `pdca_cycles_by_status` | Gauge | status, department | 各状态 PDCA 数量 |
| `pdca_stage_duration_seconds` | Histogram | stage, cycle_id | 各阶段耗时 |
| `pdca_completion_rate` | Gauge | department, time_range | 完成率 |

**用途**: 追踪 PDCA 业务效率、识别瓶颈、优化流程

### 3.3 AI Agent 调用指标

| 指标名称 | 类型 | 标签 | 说明 |
|---------|------|------|------|
| `ai_requests_total` | Counter | provider, model, status | AI 调用总数 |
| `ai_request_duration_seconds` | Histogram | provider, model | 响应时间 |
| `ai_tokens_used_total` | Counter | provider, model, type | Token 消耗量 |
| `ai_cost_usd_total` | Counter | provider, model | 估算成本 |

**用途**: 监控 AI 服务质量、控制成本、优化 token 使用

### 3.4 基础设施指标

| 指标名称 | 类型 | 标签 | 说明 |
|---------|------|------|------|
| `db_connections_active` | Gauge | state | 数据库连接池 |
| `db_query_duration_seconds` | Histogram | operation, table | 查询耗时 |
| `minio_storage_bytes` | Gauge | bucket | 存储使用量 |

**用途**: 容量规划、性能优化、故障排查

## 4. 实现方案

### 4.1 目录结构

```
backend/app/
├── core/
│   ├── metrics.py          # 指标定义和收集逻辑
│   └── config.py           # 添加监控相关配置
├── api/
│   ├── middleware.py       # HTTP 请求监控中间件（新建）
│   └── main.py             # 添加 /metrics 端点
├── pdca/
│   ├── agents/
│   │   ├── openai_agent.py # OpenAI 指标埋点
│   │   ├── zhipu_agent.py  # 智谱 AI 指标埋点
│   │   └── base.py         # 基础指标记录方法
│   └── crud.py             # PDCA 业务指标埋点
└── core/
    └── db.py               # 数据库性能指标

prometheus/
├── prometheus.yml          # Prometheus 配置

grafana/
├── dashboards/             # Dashboard 定义
│   ├── api-overview.json
│   ├── pdca-analytics.json
│   ├── ai-performance.json
│   └── infrastructure.json
└── datasources/            # 数据源配置
    └── prometheus.yml
```

### 4.2 核心依赖

```toml
[project.dependencies]
prometheus-client = "^0.20.0"
psutil = "^5.9.0"
```

### 4.3 关键实现文件

#### 4.3.1 指标定义 (`backend/app/core/metrics.py`)

```python
from prometheus_client import Counter, Gauge, Histogram, Registry
from prometheus_client.exposition import generate_latest

# 创建自定义 Registry
registry = Registry()

# API 指标
http_requests_total = Counter(
    'http_requests_total',
    'Total HTTP requests',
    ['method', 'path', 'status'],
    registry=registry
)

http_request_duration = Histogram(
    'http_request_duration_seconds',
    'HTTP request duration',
    ['method', 'path', 'status'],
    registry=registry
)

# PDCA 业务指标
pdca_cycles_created = Counter(
    'pdca_cycles_created_total',
    'Total PDCA cycles created',
    ['user_id', 'department'],
    registry=registry
)

pdca_cycles_by_status = Gauge(
    'pdca_cycles_by_status',
    'PDCA cycles by status',
    ['status', 'department'],
    registry=registry
)

# AI Agent 指标
ai_requests_total = Counter(
    'ai_requests_total',
    'Total AI requests',
    ['provider', 'model', 'status'],
    registry=registry
)

ai_request_duration = Histogram(
    'ai_request_duration_seconds',
    'AI request duration',
    ['provider', 'model'],
    registry=registry
)

ai_tokens_used = Counter(
    'ai_tokens_used_total',
    'Total AI tokens used',
    ['provider', 'model', 'type'],
    registry=registry
)
```

#### 4.3.2 中间件 (`backend/app/api/middleware.py`)

```python
import time
import prometheus_client
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from app.core.metrics import http_requests_total, http_request_duration

class PrometheusMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        start_time = time.time()

        response = await call_next(request)

        # 记录请求耗时
        duration = time.time() - start_time
        http_request_duration.labels(
            method=request.method,
            path=request.url.path,
            status=response.status_code
        ).observe(duration)

        # 记录请求总数
        http_requests_total.labels(
            method=request.method,
            path=request.url.path,
            status=response.status_code
        ).inc()

        return response
```

#### 4.3.3 Docker Compose 配置

```yaml
services:
  prometheus:
    image: prom/prometheus:v2.48.0
    volumes:
      - ./prometheus/prometheus.yml:/etc/prometheus/prometheus.yml
      - prometheus-data:/prometheus
    command:
      - '--config.file=/etc/prometheus/prometheus.yml'
      - '--storage.tsdb.path=/prometheus'
      - '--storage.tsdb.retention.time=15d'
    ports:
      - "9090:9090"
    networks:
      - backend-network

  grafana:
    image: grafana/grafana:10.2.2
    volumes:
      - grafana-data:/var/lib/grafana
      - ./grafana/provisioning:/etc/grafana/provisioning
    environment:
      - GF_SECURITY_ADMIN_USER=admin
      - GF_SECURITY_ADMIN_PASSWORD=admin
      - GF_SERVER_ROOT_URL=http://localhost:3000
    ports:
      - "3000:3000"
    networks:
      - backend-network
    depends_on:
      - prometheus

volumes:
  prometheus-data:
  grafana-data:
```

## 5. Grafana Dashboard 设计

### 5.1 API Overview Dashboard

**面板列表**:
1. 请求速率（Requests/sec）- 时间序列图
2. 错误率（Error Rate）- 单值面板
3. P50/P95/P99 延迟 - 热力图
4. Top 10 慢接口 - 表格
5. 按状态码分布的请求量 - 饼图

### 5.2 PDCA Analytics Dashboard

**面板列表**:
1. PDCA 创建趋势 - 时间序列图
2. 各状态分布 - 状态面板
3. 部门完成率对比 - 柱状图
4. 平均完成周期 - 单值面板
5. 各阶段平均耗时 - 横向条形图

### 5.3 AI Agent Performance Dashboard

**面板列表**:
1. AI 调用总量 - 时间序列图
2. 成功率 - 单值面板
3. Token 消耗趋势 - 时间序列图
4. 估算成本 - 单值面板
5. 响应时间分布 - 直方图
6. OpenAI vs 智谱 AI 对比 - 柱状图

### 5.4 Infrastructure Dashboard

**面板列表**:
1. 数据库连接池使用率 - 仪表盘
2. 慢查询 Top 10 - 表格
3. MinIO 存储使用量 - 仪表盘
4. 应用内存使用 - 时间序列图

## 6. 错误处理和容错

### 6.1 指标收集失败处理

**原则**: 指标收集失败不应影响主业务流程

```python
def safe_record_metric(metric_func):
    """装饰器：确保指标记录失败不影响业务"""
    def wrapper(*args, **kwargs):
        try:
            return metric_func(*args, **kwargs)
        except Exception as e:
            logger.warning(f"Failed to record metric: {e}")
    return wrapper
```

### 6.2 Prometheus 不可用处理

- 指标数据在应用内存中继续累积
- Prometheus 恢复后自动继续抓取
- 不影响应用正常运行

### 6.3 /metrics 端点保护

```python
@app.get("/metrics")
async def metrics():
    """Prometheus metrics endpoint"""
    if settings.ENVIRONMENT == "production":
        # 可选：添加认证或 IP 白名单
        pass
    return Response(content=generate_latest(registry), media_type="text/plain")
```

## 7. 测试策略

### 7.1 单元测试

**测试内容**:
- 指标初始化
- 指标值正确递增
- 标签正确设置
- Histogram 分位数计算

**示例测试**:
```python
def test_pdca_metrics_incremented():
    """测试 PDCA 创建指标正确记录"""
    initial_value = pdca_cycles_created.labels(
        user_id="test_user",
        department="engineering"
    )._value.get()

    create_test_pdca_cycle()

    final_value = pdca_cycles_created.labels(
        user_id="test_user",
        department="engineering"
    )._value.get()

    assert final_value == initial_value + 1
```

### 7.2 集成测试

**测试内容**:
- /metrics 端点可访问性
- Prometheus 配置正确性
- 指标抓取成功

**示例测试**:
```python
def test_metrics_endpoint():
    """测试 /metrics 端点"""
    response = client.get("/metrics")
    assert response.status_code == 200
    assert "http_requests_total" in response.text
    assert "pdca_cycles_created_total" in response.text
```

### 7.3 端到端测试

**测试场景**:
1. 启动完整 Docker Compose 栈
2. 创建测试 PDCA 循环
3. 调用 AI Agent
4. 发送 API 请求
5. 验证 Grafana Dashboard 显示数据

## 8. 部署和配置

### 8.1 开发环境部署

```bash
# 1. 更新 .env 配置
echo "METRICS_ENABLED=true" >> .env

# 2. 启动监控服务
docker-compose up -d prometheus grafana

# 3. 访问 Grafana
# URL: http://localhost:3000
# 用户名: admin
# 密码: admin
```

### 8.2 环境变量配置

```bash
# .env
METRICS_ENABLED=true
PROMETHEUS_RETENTION_DAYS=15
GRAFANA_ADMIN_PASSWORD=admin  # 生产环境请修改
```

### 8.3 Prometheus 配置

```yaml
# prometheus/prometheus.yml
global:
  scrape_interval: 15s
  evaluation_interval: 15s

scrape_configs:
  - job_name: 'fastapi-backend'
    static_configs:
      - targets: ['backend:8000']
    metrics_path: '/api/v1/metrics'
```

## 9. 性能影响评估

### 9.1 预期性能开销

| 项目 | 预期影响 |
|------|---------|
| 内存开销 | +10-20 MB（指标数据） |
| CPU 开销 | <1%（指标计算） |
| 请求延迟 | +1-2ms（中间件） |
| /metrics 请求 | 10-50ms（取决于指标数量） |

### 9.2 优化策略

- 使用 Counter 而非 Gauge 减少计算
- 合理设置 Histogram 分桶
- 避免高基数标签（如 user_id）
- 定期审查和清理无用指标

## 10. 未来扩展方向

### 10.1 短期优化（1-3 个月）

- [ ] 添加告警规则（AlertManager）
- [ ] 实现指标数据导出
- [ ] 优化 Dashboard 布局
- [ ] 添加性能基准测试

### 10.2 长期规划（3-6 个月）

- [ ] 实现分布式追踪（Jaeger/Zipkin）
- [ ] 集成日志聚合（ELK/Loki）
- [ ] 实现自动化成本报告
- [ ] 添加机器学习异常检测

### 10.3 可选增强

- [ ] 实现指标 API 供前端调用
- [ ] 添加实时监控大屏
- [ ] 实现自定义告警通道
- [ ] 支持 Grafana Cloud 托管

## 11. 安全考虑

### 11.1 访问控制

- /metrics 端点在生产环境应限制访问
- Grafana 默认密码必须修改
- 考虑使用反向代理添加认证

### 11.2 数据安全

- 避免在指标标签中包含敏感信息
- 成本数据可能包含商业敏感信息
- 考虑指标数据加密存储

## 12. 运维指南

### 12.1 常见问题排查

**问题**: Prometheus 抓取失败
- 检查 /metrics 端点是否可访问
- 验证网络连接
- 查看 Prometheus 日志

**问题**: Grafana 无数据显示
- 确认 Prometheus 有数据
- 检查数据源配置
- 验证时间范围选择

### 12.2 维护操作

```bash
# 查看 Prometheus 目标状态
curl http://localhost:9090/api/v1/targets

# 重启 Prometheus
docker-compose restart prometheus

# 备份 Grafana Dashboard
docker-compose exec grafana grafana-cli admin export-dashboard > backup.json
```

## 13. 验收标准

### 13.1 功能验收

- [ ] 所有 4 类指标正确收集
- [ ] Grafana 4 个 Dashboard 正常显示
- [ ] /metrics 端点返回正确格式
- [ ] Prometheus 成功抓取指标

### 13.2 性能验收

- [ ] API 请求延迟增加 <5ms
- [ ] 内存开销 <50MB
- [ ] /metrics 端点响应 <100ms

### 13.3 稳定性验收

- [ ] 指标收集失败不影响业务
- [ ] Prometheus 重启后数据正常
- [ ] 长时间运行无内存泄漏

## 14. 总结

本设计实现了一个全面的业务指标监控系统，覆盖了从基础设施到业务层的完整视图。通过 Prometheus + Grafana 的云原生架构，系统具有良好的可扩展性和可维护性。

**关键优势**:
- ✅ 全面的业务洞察
- ✅ 实时性能监控
- ✅ 成本可控
- ✅ 易于扩展
- ✅ 非侵入式设计

**预期收益**:
- 快速发现性能瓶颈
- 数据驱动的业务决策
- 降低 AI 调用成本
- 提升系统稳定性
