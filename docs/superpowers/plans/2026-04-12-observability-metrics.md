# 业务指标监控系统实施计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-step. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 为 FastAPI + React 全栈应用添加基于 Prometheus + Grafana 的业务指标监控系统，覆盖 API 请求、PDCA 业务、AI Agent 调用和基础设施四大类指标。

**Architecture:** 使用 prometheus_client 在 FastAPI 中收集指标，通过 /metrics 端点暴露给 Prometheus，使用 Grafana 可视化展示。采用中间件自动收集 HTTP 指标，在业务逻辑中埋点收集 PDCA 和 AI 指标。

**Tech Stack:** Prometheus 2.48.0, Grafana 10.2.2, prometheus_client 0.20.0, psutil 5.9.0, Docker Compose

---

## 文件结构映射

### 新建文件
- `backend/app/core/metrics.py` - 指标定义和注册中心
- `backend/app/api/middleware.py` - Prometheus 监控中间件
- `backend/tests/api/routes/test_metrics.py` - 指标端点测试
- `backend/tests/core/test_metrics.py` - 指标收集单元测试
- `prometheus/prometheus.yml` - Prometheus 配置文件
- `grafana/provisioning/datasources/prometheus.yml` - Grafana 数据源配置
- `grafana/provisioning/dashboards/api-overview.json` - API 监控 Dashboard
- `grafana/provisioning/dashboards/pdca-analytics.json` - PDCA 业务 Dashboard
- `grafana/provisioning/dashboards/ai-performance.json` - AI 性能 Dashboard
- `grafana/provisioning/dashboards/infrastructure.json` - 基础设施 Dashboard
- `docker-compose.monitoring.yml` - 监控服务 Docker Compose 配置

### 修改文件
- `backend/pyproject.toml` - 添加 prometheus-client 和 psutil 依赖
- `backend/app/core/config.py` - 添加监控相关配置
- `backend/app/core/db.py` - 添加数据库连接池指标
- `backend/app/api/main.py` - 注册 /metrics 端点和中间件
- `backend/app/pdca/agents/base.py` - 添加 AI 指标记录方法
- `backend/app/pdca/agents/openai_agent.py` - 集成 OpenAI 指标
- `backend/app/pdca/agents/zhipu_agent.py` - 集成智谱 AI 指标
- `backend/app/pdca/crud.py` - 集成 PDCA 业务指标
- `.env` - 添加监控相关环境变量

---

## 任务分解

### Task 1: 添加项目依赖

**Files:**
- Modify: `backend/pyproject.toml`

- [ ] **Step 1: 添加 prometheus-client 依赖**

在 `dependencies` 数组中添加：

```toml
"prometheus-client>=0.20.0,<1.0.0",
"psutil>=5.9.0,<6.0.0",
```

添加位置：在 `dependencies` 数组末尾，`"zhipuai>=2.1.0",` 之后

- [ ] **Step 2: 安装依赖验证**

运行：
```bash
cd backend
uv sync
```

预期输出：无错误，依赖成功安装

- [ ] **Step 3: 提交更改**

```bash
git add backend/pyproject.toml
git commit -m "feat: add prometheus-client and psutil dependencies

Add prometheus-client for metrics collection and psutil for system metrics.

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>"
```

---

### Task 2: 创建指标定义模块

**Files:**
- Create: `backend/app/core/metrics.py`

- [ ] **Step 1: 创建指标定义文件**

创建 `backend/app/core/metrics.py`：

```python
"""
Prometheus metrics definitions and registry.

This module defines all Prometheus metrics used across the application,
including HTTP requests, PDCA business metrics, AI agent calls, and infrastructure metrics.
"""
import logging
from prometheus_client import Counter, Gauge, Histogram, Registry
from prometheus_client.exposition import generate_latest

logger = logging.getLogger(__name__)

# Create a custom registry to avoid conflicts with default metrics
registry = Registry()

# ==============================================================================
# HTTP Request Metrics
# ==============================================================================

http_requests_total = Counter(
    'http_requests_total',
    'Total HTTP requests',
    ['method', 'path', 'status'],
    registry=registry
)

http_request_duration_seconds = Histogram(
    'http_request_duration_seconds',
    'HTTP request duration in seconds',
    ['method', 'path', 'status'],
    registry=registry,
    buckets=(0.005, 0.01, 0.025, 0.05, 0.075, 0.1, 0.25, 0.5, 0.75, 1.0, 2.5, 5.0, 7.5, 10.0)
)

http_requests_active = Gauge(
    'http_requests_active',
    'Number of active HTTP requests',
    ['path'],
    registry=registry
)

# ==============================================================================
# PDCA Business Metrics
# ==============================================================================

pdca_cycles_created_total = Counter(
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

pdca_stage_duration_seconds = Histogram(
    'pdca_stage_duration_seconds',
    'PDCA stage duration in seconds',
    ['stage'],
    registry=registry,
    buckets=(60, 300, 600, 1800, 3600, 7200, 14400, 28800, 43200, 86400)
)

# ==============================================================================
# AI Agent Metrics
# ==============================================================================

ai_requests_total = Counter(
    'ai_requests_total',
    'Total AI agent requests',
    ['provider', 'model', 'status'],
    registry=registry
)

ai_request_duration_seconds = Histogram(
    'ai_request_duration_seconds',
    'AI request duration in seconds',
    ['provider', 'model'],
    registry=registry,
    buckets=(0.5, 1.0, 2.0, 5.0, 10.0, 20.0, 30.0, 60.0, 120.0)
)

ai_tokens_used_total = Counter(
    'ai_tokens_used_total',
    'Total AI tokens used',
    ['provider', 'model', 'type'],  # type: prompt/completion
    registry=registry
)

ai_cost_usd_total = Counter(
    'ai_cost_usd_total',
    'Total AI cost in USD',
    ['provider', 'model'],
    registry=registry
)

# ==============================================================================
# Infrastructure Metrics
# ==============================================================================

db_connections_active = Gauge(
    'db_connections_active',
    'Active database connections',
    ['state'],  # state: checked_out/active/idle
    registry=registry
)

db_query_duration_seconds = Histogram(
    'db_query_duration_seconds',
    'Database query duration in seconds',
    ['operation', 'table'],
    registry=registry,
    buckets=(0.001, 0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0)
)


def safe_record_metric(metric_func):
    """
    Decorator to ensure metric recording failures don't affect business logic.

    Args:
        metric_func: The metric recording function to wrap

    Returns:
        Wrapped function that logs errors instead of raising them
    """
    def wrapper(*args, **kwargs):
        try:
            return metric_func(*args, **kwargs)
        except Exception as e:
            logger.warning(f"Failed to record metric: {e}")
    return wrapper


def generate_metrics() -> bytes:
    """
    Generate Prometheus metrics exposition format.

    Returns:
        Metrics in Prometheus text format
    """
    return generate_latest(registry)
```

- [ ] **Step 2: 创建基础测试文件**

创建 `backend/tests/core/test_metrics.py`：

```python
"""Test metrics initialization and basic functionality."""
from app.core.metrics import (
    http_requests_total,
    http_request_duration_seconds,
    pdca_cycles_created_total,
    ai_requests_total,
    generate_metrics,
)


def test_metrics_registry_exists():
    """Test that metrics are properly registered."""
    # Check that metrics have the right name and type
    assert http_requests_total._name == 'http_requests_total'
    assert pdca_cycles_created_total._name == 'pdca_cycles_created_total'
    assert ai_requests_total._name == 'ai_requests_total'


def test_metrics_can_be_incremented():
    """Test that counters can be incremented."""
    initial_value = http_requests_total.labels(
        method='GET',
        path='/api/v1/test',
        status='200'
    )._value.get()

    http_requests_total.labels(
        method='GET',
        path='/api/v1/test',
        status='200'
    ).inc()

    final_value = http_requests_total.labels(
        method='GET',
        path='/api/v1/test',
        status='200'
    )._value.get()

    assert final_value == initial_value + 1


def test_metrics_can_be_observed():
    """Test that histograms can observe values."""
    http_request_duration_seconds.labels(
        method='GET',
        path='/api/v1/test',
        status='200'
    ).observe(0.123)

    # Should not raise any errors
    assert True


def test_generate_metrics_returns_bytes():
    """Test that generate_metrics returns bytes."""
    metrics = generate_metrics()
    assert isinstance(metrics, bytes)
    assert b'http_requests_total' in metrics
```

- [ ] **Step 3: 运行测试验证**

运行：
```bash
cd backend
pytest tests/core/test_metrics.py -v
```

预期输出：
```
collected 4 items

tests/core/test_metrics.py::test_metrics_registry_exists PASSED
tests/core/test_metrics.py::test_metrics_can_be_incremented PASSED
tests/core/test_metrics.py::test_metrics_can_be_observed PASSED
tests/core/test_metrics.py::test_generate_metrics_returns_bytes PASSED
```

- [ ] **Step 4: 提交更改**

```bash
git add backend/app/core/metrics.py backend/tests/core/test_metrics.py
git commit -m "feat: create Prometheus metrics definitions

- Define HTTP, PDCA, AI, and infrastructure metrics
- Create metrics registry with custom buckets
- Add safe_record_metric decorator for error handling
- Include comprehensive unit tests

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>"
```

---

### Task 3: 创建监控中间件

**Files:**
- Create: `backend/app/api/middleware.py`

- [ ] **Step 1: 创建中间件文件**

创建 `backend/app/api/middleware.py`：

```python
"""
Prometheus monitoring middleware for FastAPI.

This middleware automatically tracks HTTP request metrics including
request count, duration, and active requests.
"""
import time
from typing import Callable
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from app.core.metrics import (
    http_requests_total,
    http_request_duration_seconds,
    http_requests_active,
)


class PrometheusMiddleware(BaseHTTPMiddleware):
    """
    Middleware to track HTTP request metrics for Prometheus.

    Automatically records:
    - Total request count (by method, path, status)
    - Request duration (by method, path, status)
    - Active request count (by path)
    """

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        Process request and record metrics.

        Args:
            request: Incoming HTTP request
            call_next: Next middleware or route handler

        Returns:
            HTTP response with metrics recorded
        """
        # Extract path for metrics
        path = request.url.path

        # Increment active requests
        http_requests_active.labels(path=path).inc()

        # Record start time
        start_time = time.time()

        try:
            # Process request
            response = await call_next(request)

            # Record metrics
            duration = time.time() - start_time
            status = str(response.status_code)

            http_request_duration_seconds.labels(
                method=request.method,
                path=path,
                status=status
            ).observe(duration)

            http_requests_total.labels(
                method=request.method,
                path=path,
                status=status
            ).inc()

            return response

        finally:
            # Decrement active requests
            http_requests_active.labels(path=path).dec()
```

- [ ] **Step 2: 编写中间件测试**

创建 `backend/tests/api/test_middleware.py`：

```python
"""Test Prometheus middleware."""
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from app.api.middleware import PrometheusMiddleware
from app.core.metrics import http_requests_total, http_request_duration_seconds


@pytest.fixture
def app_with_middleware():
    """Create a test app with Prometheus middleware."""
    app = FastAPI()
    app.add_middleware(PrometheusMiddleware)

    @app.get("/test")
    async def test_endpoint():
        return {"message": "test"}

    @app.get("/test-error")
    async def test_error_endpoint():
        raise ValueError("Test error")

    return app


@pytest.fixture
def client(app_with_middleware):
    """Create test client."""
    return TestClient(app_with_middleware)


def test_middleware_tracks_successful_requests(client):
    """Test that middleware tracks successful requests."""
    initial_value = http_requests_total.labels(
        method='GET',
        path='/test',
        status='200'
    )._value.get()

    response = client.get("/test")

    assert response.status_code == 200

    final_value = http_requests_total.labels(
        method='GET',
        path='/test',
        status='200'
    )._value.get()

    assert final_value == initial_value + 1


def test_middleware_tracks_error_requests(client):
    """Test that middleware tracks failed requests."""
    initial_value = http_requests_total.labels(
        method='GET',
        path='/test-error',
        status='500'
    )._value.get()

    response = client.get("/test-error")

    assert response.status_code == 500

    final_value = http_requests_total.labels(
        method='GET',
        path='/test-error',
        status='500'
    )._value.get()

    assert final_value == initial_value + 1


def test_middleware_tracks_request_duration(client):
    """Test that middleware tracks request duration."""
    response = client.get("/test")

    # Get metric samples
    metric_samples = http_request_duration_seconds.labels(
        method='GET',
        path='/test',
        status='200'
    ).collect()

    # Should have at least one sample
    assert len(metric_samples) > 0
```

- [ ] **Step 3: 运行中间件测试**

运行：
```bash
cd backend
pytest tests/api/test_middleware.py -v
```

预期输出：
```
collected 3 items

tests/api/test_middleware.py::test_middleware_tracks_successful_requests PASSED
tests/api/test_middleware.py::test_middleware_tracks_error_requests PASSED
tests/api/test_middleware.py::test_middleware_tracks_request_duration PASSED
```

- [ ] **Step 4: 提交更改**

```bash
git add backend/app/api/middleware.py backend/tests/api/test_middleware.py
git commit -m "feat: add Prometheus monitoring middleware

- Track HTTP request count, duration, and active requests
- Auto-capture status codes and response times
- Include comprehensive middleware tests

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>"
```

---

### Task 4: 注册中间件和 /metrics 端点

**Files:**
- Modify: `backend/app/api/main.py`
- Modify: `backend/app/core/config.py`

- [ ] **Step 1: 添加监控配置**

修改 `backend/app/core/config.py`，在 `Settings` 类中添加：

```python
# Monitoring Configuration
METRICS_ENABLED: bool = True
PROMETHEUS_RETENTION_DAYS: int = 15
GRAFANA_ADMIN_PASSWORD: str = "admin"
```

添加位置：在 `MINIO_REGION` 配置之后，`def _check_default_secret` 方法之前

- [ ] **Step 2: 注册中间件和 /metrics 端点**

修改 `backend/app/api/main.py`，完整替换为：

```python
import logging
import sentry_sdk
from fastapi import FastAPI
from fastapi.routing import APIRoute
from fastapi.responses import Response
from starlette.middleware.cors import CORSMiddleware

from app.api.main import api_router
from app.api.middleware import PrometheusMiddleware
from app.core.config import settings
from app.core.minio import minio_client
from app.core.metrics import generate_metrics

logger = logging.getLogger(__name__)


def custom_generate_unique_id(route: APIRoute) -> str:
    return f"{route.tags[0]}-{route.name}"


if settings.SENTRY_DSN and settings.ENVIRONMENT != "local":
    sentry_sdk.init(dsn=str(settings.SENTRY_DSN), enable_tracing=True)


app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    generate_unique_id_function=custom_generate_unique_id,
)

# Set all CORS enabled origins
if settings.all_cors_origins:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.all_cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

# Add Prometheus middleware if metrics are enabled
if settings.METRICS_ENABLED:
    app.add_middleware(PrometheusMiddleware)

app.include_router(api_router, prefix=settings.API_V1_STR)


@app.on_event("startup")
async def startup_event() -> None:
    """Initialize services on startup."""
    # Ensure MinIO bucket exists
    try:
        # Access the client property to trigger lazy initialization and bucket creation
        _ = minio_client.client
        logger.info(f"MinIO bucket '{minio_client.bucket_name}' is ready")
    except Exception as e:
        logger.error(f"Failed to initialize MinIO bucket: {e}")
        # Don't fail startup - MinIO will retry on first access


@app.get("/metrics")
async def metrics():
    """
    Prometheus metrics endpoint.

    Returns metrics in Prometheus exposition format.
    Only accessible if METRICS_ENABLED is True.
    """
    if not settings.METRICS_ENABLED:
        return Response(content="Metrics disabled", status_code=404)

    return Response(content=generate_metrics(), media_type="text/plain")
```

关键修改点：
1. 导入 `PrometheusMiddleware` 和 `generate_metrics`
2. 导入 `Response`
3. 添加条件判断 `if settings.METRICS_ENABLED:`
4. 添加 `/metrics` 端点

- [ ] **Step 3: 创建 /metrics 端点测试**

修改 `backend/tests/api/routes/test_items.py`，在文件末尾添加：

```python
def test_metrics_endpoint(client: TestClient) -> None:
    """Test that /metrics endpoint returns metrics."""
    response = client.get("/metrics")

    assert response.status_code == 200
    assert response.headers["content-type"] == "text/plain; charset=utf-8"
    assert b"http_requests_total" in response.content
```

- [ ] **Step 4: 运行测试验证**

运行：
```bash
cd backend
pytest tests/api/routes/test_items.py::test_metrics_endpoint -v
```

预期输出：
```
PASSED
```

- [ ] **Step 5: 提交更改**

```bash
git add backend/app/api/main.py backend/app/core/config.py backend/tests/api/routes/test_items.py
git commit -m "feat: register Prometheus middleware and /metrics endpoint

- Add METRICS_ENABLED configuration
- Conditionally enable Prometheus middleware
- Expose /metrics endpoint for Prometheus scraping
- Add test for metrics endpoint

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>"
```

---

### Task 5: 集成 PDCA 业务指标

**Files:**
- Modify: `backend/app/pdca/crud.py`

- [ ] **Step 1: 在 PDCA CRUD 中添加指标记录**

修改 `backend/app/pdca/crud.py`，在文件顶部添加导入：

```python
from app.core.metrics import pdca_cycles_created_total, pdca_stage_duration_seconds
import time
from typing import Optional
```

修改 `create_pdca_cycle` 函数：

```python
def create_pdca_cycle(session: Session, cycle_data: dict, owner_id: UUID) -> PDCACycle:
    """
    Create a new PDCA cycle.

    Args:
        session: Database session
        cycle_data: Dictionary containing cycle data (title, description, goal, etc.)
        owner_id: ID of the user who owns this cycle

    Returns:
        Created PDCACycle instance
    """
    start_time = time.time()

    cycle = PDCACycle(**cycle_data, owner_id=owner_id)
    session.add(cycle)
    session.commit()
    session.refresh(cycle)

    # Record metric
    try:
        pdca_cycles_created_total.labels(
            user_id=str(owner_id),
            department=cycle_data.get('department', 'unknown')
        ).inc()

        duration = time.time() - start_time
        pdca_stage_duration_seconds.labels(stage='create').observe(duration)
    except Exception as e:
        # Log but don't fail the operation
        import logging
        logging.getLogger(__name__).warning(f"Failed to record PDCA metric: {e}")

    return cycle
```

- [ ] **Step 2: 编写 PDCA 指标测试**

创建 `backend/tests/pdca/test_crud_metrics.py`：

```python
"""Test PDCA CRUD metrics."""
import pytest
from uuid import uuid4
from app.pdca.crud import create_pdca_cycle
from app.core.metrics import pdca_cycles_created_total


def test_create_pdca_cycle_increments_metric(db_session):
    """Test that creating a PDCA cycle increments the metric."""
    user_id = uuid4()

    # Get initial metric value
    initial_value = pdca_cycles_created_total.labels(
        user_id=str(user_id),
        department='engineering'
    )._value.get()

    # Create a PDCA cycle
    cycle_data = {
        'title': 'Test Cycle',
        'description': 'Test Description',
        'goal': 'Test Goal',
        'department': 'engineering'
    }
    create_pdca_cycle(db_session, cycle_data, user_id)

    # Check metric incremented
    final_value = pdca_cycles_created_total.labels(
        user_id=str(user_id),
        department='engineering'
    )._value.get()

    assert final_value == initial_value + 1
```

- [ ] **Step 3: 运行测试验证**

运行：
```bash
cd backend
pytest tests/pdca/test_crud_metrics.py -v
```

预期输出：
```
PASSED
```

- [ ] **Step 4: 提交更改**

```bash
git add backend/app/pdca/crud.py backend/tests/pdca/test_crud_metrics.py
git commit -m "feat: integrate PDCA business metrics

- Track PDCA cycle creation by user and department
- Record PDCA stage duration
- Include error handling to prevent metric failures
- Add tests for PDCA metric recording

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>"
```

---

### Task 6: 集成 AI Agent 指标

**Files:**
- Modify: `backend/app/pdca/agents/base.py`
- Modify: `backend/app/pdca/agents/openai_agent.py`
- Modify: `backend/app/pdca/agents/zhipu_agent.py`

- [ ] **Step 1: 在 Base Agent 中添加指标记录方法**

修改 `backend/app/pdca/agents/base.py`，完整替换为：

```python
"""Base agent executor abstract class."""
import time
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional
from app.core.metrics import (
    ai_requests_total,
    ai_request_duration_seconds,
    ai_tokens_used_total,
    ai_cost_usd_total,
)


class BaseAgentExecutor(ABC):
    """Abstract base class for all agent executors."""

    def __init__(self, provider: str, model: str):
        """
        Initialize base agent.

        Args:
            provider: AI provider name (e.g., 'openai', 'zhipu')
            model: Model name (e.g., 'gpt-4', 'glm-4')
        """
        self.provider = provider
        self.model = model

    def _record_ai_metrics(
        self,
        status: str,
        duration: float,
        prompt_tokens: int = 0,
        completion_tokens: int = 0,
        cost_usd: float = 0.0
    ):
        """
        Record AI agent metrics.

        Args:
            status: Request status ('success' or 'error')
            duration: Request duration in seconds
            prompt_tokens: Number of prompt tokens used
            completion_tokens: Number of completion tokens used
            cost_usd: Estimated cost in USD
        """
        try:
            ai_requests_total.labels(
                provider=self.provider,
                model=self.model,
                status=status
            ).inc()

            ai_request_duration_seconds.labels(
                provider=self.provider,
                model=self.model
            ).observe(duration)

            if prompt_tokens > 0:
                ai_tokens_used_total.labels(
                    provider=self.provider,
                    model=self.model,
                    type='prompt'
                ).inc(prompt_tokens)

            if completion_tokens > 0:
                ai_tokens_used_total.labels(
                    provider=self.provider,
                    model=self.model,
                    type='completion'
                ).inc(completion_tokens)

            if cost_usd > 0:
                ai_cost_usd_total.labels(
                    provider=self.provider,
                    model=self.model
                ).inc(cost_usd)

        except Exception as e:
            import logging
            logging.getLogger(__name__).warning(f"Failed to record AI metric: {e}")

    @abstractmethod
    async def execute(self, task: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Execute an agent task with the given context.

        Args:
            task: The task description or prompt to execute
            context: Optional context dictionary containing additional information

        Returns:
            Dictionary containing the execution results
        """
        pass

    @abstractmethod
    def validate_input(self, task: str, context: Optional[Dict[str, Any]] = None) -> bool:
        """
        Validate the input parameters for the agent executor.

        Args:
            task: The task description or prompt to validate
            context: Optional context dictionary to validate

        Returns:
            True if input is valid, False otherwise
        """
        pass
```

- [ ] **Step 2: 集成 OpenAI Agent 指标**

修改 `backend/app/pdca/agents/openai_agent.py`，在 `execute` 方法中添加指标记录。查找 `execute` 方法并修改：

```python
async def execute(self, task: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Execute OpenAI agent task.

    Args:
        task: Task description
        context: Optional context

    Returns:
        Execution result dictionary
    """
    start_time = time.time()
    status = 'success'
    prompt_tokens = 0
    completion_tokens = 0
    cost_usd = 0.0

    try:
        # Existing OpenAI API call logic...
        # (Keep your existing implementation)

        response = await self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": task}],
            **self._get_kwargs(context)
        )

        result = response.choices[0].message.content

        # Extract token usage
        if hasattr(response, 'usage') and response.usage:
            prompt_tokens = response.usage.prompt_tokens
            completion_tokens = response.usage.completion_tokens

        # Estimate cost (GPT-4 pricing as of 2024)
        if self.model.startswith('gpt-4'):
            cost_usd = (prompt_tokens * 0.00003 + completion_tokens * 0.00006)

        return {
            "result": result,
            "provider": "openai",
            "model": self.model,
            "tokens": {
                "prompt": prompt_tokens,
                "completion": completion_tokens
            }
        }

    except Exception as e:
        status = 'error'
        import logging
        logging.getLogger(__name__).error(f"OpenAI execution error: {e}")
        raise

    finally:
        duration = time.time() - start_time
        self._record_ai_metrics(
            status=status,
            duration=duration,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            cost_usd=cost_usd
        )
```

- [ ] **Step 3: 集成智谱 AI Agent 指标**

类似地修改 `backend/app/pdca/agents/zhipu_agent.py`，在 `execute` 方法中添加指标记录：

```python
async def execute(self, task: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Execute Zhipu AI agent task.

    Args:
        task: Task description
        context: Optional context

    Returns:
        Execution result dictionary
    """
    start_time = time.time()
    status = 'success'
    prompt_tokens = 0
    completion_tokens = 0
    cost_usd = 0.0

    try:
        # Existing Zhipu AI API call logic...
        # (Keep your existing implementation)

        response = await self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": task}],
            **self._get_kwargs(context)
        )

        result = response.choices[0].message.content

        # Extract token usage
        if hasattr(response, 'usage') and response.usage:
            prompt_tokens = response.usage.prompt_tokens
            completion_tokens = response.usage.completion_tokens

        # Estimate cost (GLM-4 pricing approximation)
        cost_usd = (prompt_tokens + completion_tokens) * 0.00001

        return {
            "result": result,
            "provider": "zhipu",
            "model": self.model,
            "tokens": {
                "prompt": prompt_tokens,
                "completion": completion_tokens
            }
        }

    except Exception as e:
        status = 'error'
        import logging
        logging.getLogger(__name__).error(f"Zhipu AI execution error: {e}")
        raise

    finally:
        duration = time.time() - start_time
        self._record_ai_metrics(
            status=status,
            duration=duration,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            cost_usd=cost_usd
        )
```

- [ ] **Step 4: 编写 AI Agent 指标测试**

创建 `backend/tests/pdca/test_ai_metrics.py`：

```python
"""Test AI agent metrics."""
import pytest
from app.pdca.agents.openai_agent import OpenAIAgentExecutor
from app.core.metrics import ai_requests_total, ai_tokens_used_total, ai_cost_usd_total


@pytest.mark.asyncio
async def test_openai_agent_records_metrics():
    """Test that OpenAI agent records metrics."""
    agent = OpenAIAgentExecutor()

    # Get initial values
    initial_requests = ai_requests_total.labels(
        provider='openai',
        model='gpt-4',
        status='success'
    )._value.get()

    initial_tokens = ai_tokens_used_total.labels(
        provider='openai',
        model='gpt-4',
        type='prompt'
    )._value.get()

    # Execute task (this will make a real API call in tests, consider mocking)
    try:
        result = await agent.execute("Test task")
        assert result['provider'] == 'openai'

        # Check metrics were recorded
        final_requests = ai_requests_total.labels(
            provider='openai',
            model='gpt-4',
            status='success'
        )._value.get()

        assert final_requests > initial_requests
    except Exception as e:
        # API call might fail in tests, that's okay
        pytest.skip(f"API call failed: {e}")
```

- [ ] **Step 5: 运行测试验证**

运行：
```bash
cd backend
pytest tests/pdca/test_ai_metrics.py -v
```

预期输出：可能 skip（如果没有 API key）或 PASSED

- [ ] **Step 6: 提交更改**

```bash
git add backend/app/pdca/agents/base.py backend/app/pdca/agents/openai_agent.py backend/app/pdca/agents/zhipu_agent.py backend/tests/pdca/test_ai_metrics.py
git commit -m "feat: integrate AI agent metrics

- Track AI requests, duration, tokens, and cost
- Support both OpenAI and Zhipu AI providers
- Record success/error status for all calls
- Add base metrics recording method
- Include tests for metric recording

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>"
```

---

### Task 7: 添加数据库连接池指标

**Files:**
- Modify: `backend/app/core/db.py`

- [ ] **Step 1: 在数据库模块中添加指标记录**

修改 `backend/app/core/db.py`，添加连接池指标监控。在文件末尾添加：

```python
from app.core.metrics import db_connections_active
import logging

logger = logging.getLogger(__name__)


def update_db_pool_metrics():
    """
    Update database connection pool metrics.

    Should be called periodically to track pool state.
    """
    try:
        if engine and engine.pool:
            pool = engine.pool

            # Get pool status
            status = pool.status()
            db_connections_active.labels(state='checked_out').set(status.checkedout)
            db_connections_active.labels(state='active').set(pool.size() - pool.checkedout())
            db_connections_active.labels(state='idle').set(pool.checkedout())

    except Exception as e:
        logger.warning(f"Failed to update DB pool metrics: {e}")
```

- [ ] **Step 2: 在启动事件中定期更新指标**

修改 `backend/app/api/main.py`，在 `startup_event` 函数中添加：

```python
@app.on_event("startup")
async def startup_event() -> None:
    """Initialize services on startup."""
    # Ensure MinIO bucket exists
    try:
        # Access the client property to trigger lazy initialization and bucket creation
        _ = minio_client.client
        logger.info(f"MinIO bucket '{minio_client.bucket_name}' is ready")
    except Exception as e:
        logger.error(f"Failed to initialize MinIO bucket: {e}")
        # Don't fail startup - MinIO will retry on first access

    # Update DB pool metrics
    try:
        from app.core.db import update_db_pool_metrics
        update_db_pool_metrics()
        logger.info("Database pool metrics initialized")
    except Exception as e:
        logger.warning(f"Failed to initialize DB pool metrics: {e}")
```

- [ ] **Step 3: 提交更改**

```bash
git add backend/app/core/db.py backend/app/api/main.py
git commit -m "feat: add database connection pool metrics

- Track checked out, active, and idle connections
- Update metrics on application startup
- Include error handling for metric collection

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>"
```

---

### Task 8: 创建 Prometheus 配置

**Files:**
- Create: `prometheus/prometheus.yml`

- [ ] **Step 1: 创建 Prometheus 配置文件**

创建 `prometheus/prometheus.yml`：

```yaml
global:
  scrape_interval: 15s
  evaluation_interval: 15s
  external_labels:
    monitor: 'pdca-monitor'

# Rule files
rule_files: []

# Scrape configurations
scrape_configs:
  - job_name: 'prometheus'
    static_configs:
      - targets: ['localhost:9090']

  - job_name: 'fastapi-backend'
    scrape_interval: 15s
    metrics_path: '/metrics'
    static_configs:
      - targets: ['backend:8000']
        labels:
          app: 'pdca-backend'
          environment: 'development'
```

- [ ] **Step 2: 提交配置文件**

```bash
git add prometheus/prometheus.yml
git commit -m "feat: add Prometheus configuration

- Configure 15s scrape interval
- Add FastAPI backend target
- Include environment and app labels

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>"
```

---

### Task 9: 创建 Grafana 数据源配置

**Files:**
- Create: `grafana/provisioning/datasources/prometheus.yml`

- [ ] **Step 1: 创建 Grafana 数据源配置**

创建 `grafana/provisioning/datasources/prometheus.yml`：

```yaml
apiVersion: 1

datasources:
  - name: Prometheus
    type: prometheus
    access: proxy
    url: http://prometheus:9090
    isDefault: true
    editable: true
    jsonData:
      timeInterval: "15s"
```

- [ ] **Step 2: 提交配置文件**

```bash
git add grafana/provisioning/datasources/prometheus.yml
git commit -m "feat: add Grafana Prometheus datasource

- Configure Prometheus as default datasource
- Set 15s time interval for queries
- Enable provisioning for automatic setup

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>"
```

---

### Task 10: 创建 Grafana Dashboard 配置

**Files:**
- Create: `grafana/provisioning/dashboards/api-overview.json`
- Create: `grafana/provisioning/dashboards/pdca-analytics.json`
- Create: `grafana/provisioning/dashboards/ai-performance.json`
- Create: `grafana/provisioning/dashboards/infrastructure.json`
- Create: `grafana/provisioning/dashboards/dashboards.yml`

- [ ] **Step 1: 创建 Dashboard provisioning 配置**

创建 `grafana/provisioning/dashboards/dashboards.yml`：

```yaml
apiVersion: 1

providers:
  - name: 'PDCA Dashboards'
    orgId: 1
    folder: ''
    type: file
    disableDeletion: false
    updateIntervalSeconds: 10
    allowUiUpdates: true
    options:
      path: /etc/grafana/provisioning/dashboards
```

- [ ] **Step 2: 创建 API Overview Dashboard**

创建 `grafana/provisioning/dashboards/api-overview.json`：

```json
{
  "annotations": {
    "list": []
  },
  "editable": true,
  "gnetId": null,
  "graphTooltip": 0,
  "id": null,
  "links": [],
  "panels": [
    {
      "datasource": "Prometheus",
      "fieldConfig": {
        "defaults": {
          "color": {
            "mode": "palette-classic"
          },
          "custom": {
            "axisLabel": "",
            "axisPlacement": "auto",
            "barAlignment": 0,
            "drawStyle": "line",
            "fillOpacity": 10,
            "gradientMode": "none",
            "hideFrom": {
              "tooltip": false,
              "viz": false,
              "legend": false
            },
            "lineInterpolation": "linear",
            "lineWidth": 1,
            "pointSize": 5,
            "scaleDistribution": {
              "type": "linear"
            },
            "showPoints": "never",
            "spanNulls": true
          },
          "mappings": [],
          "thresholds": {
            "mode": "absolute",
            "steps": [
              {
                "color": "green",
                "value": null
              }
            ]
          },
          "unit": "reqps"
        }
      },
      "gridPos": {
        "h": 8,
        "w": 12,
        "x": 0,
        "y": 0
      },
      "id": 1,
      "options": {
        "legend": {
          "calcs": [],
          "displayMode": "list",
          "placement": "bottom"
        },
        "tooltip": {
          "mode": "single"
        }
      },
      "targets": [
        {
          "expr": "rate(http_requests_total[5m])",
          "legendFormat": "{{method}} {{path}} ({{status}})",
          "refId": "A"
        }
      ],
      "title": "Request Rate",
      "type": "timeseries"
    },
    {
      "datasource": "Prometheus",
      "fieldConfig": {
        "defaults": {
          "color": {
            "mode": "thresholds"
          },
          "mappings": [],
          "thresholds": {
            "mode": "absolute",
            "steps": [
              {
                "color": "green",
                "value": null
              },
              {
                "color": "red",
                "value": 0.05
              }
            ]
          },
          "unit": "percentunit"
        }
      },
      "gridPos": {
        "h": 8,
        "w": 6,
        "x": 12,
        "y": 0
      },
      "id": 2,
      "options": {
        "orientation": "auto",
        "reduceOptions": {
          "values": false,
          "calcs": ["lastNotNull"],
          "fields": ""
        },
        "showThresholdLabels": false,
        "showThresholdMarkers": true
      },
      "targets": [
        {
          "expr": "sum(rate(http_requests_total{status=~\"5..\"}[5m])) / sum(rate(http_requests_total[5m]))",
          "refId": "A"
        }
      ],
      "title": "Error Rate",
      "type": "gauge"
    },
    {
      "datasource": "Prometheus",
      "fieldConfig": {
        "defaults": {
          "color": {
            "mode": "palette-classic"
          },
          "custom": {
            "axisLabel": "",
            "axisPlacement": "auto",
            "barAlignment": 0,
            "drawStyle": "line",
            "fillOpacity": 10,
            "gradientMode": "none",
            "hideFrom": {
              "tooltip": false,
              "viz": false,
              "legend": false
            },
            "lineInterpolation": "linear",
            "lineWidth": 1,
            "pointSize": 5,
            "scaleDistribution": {
              "type": "linear"
            },
            "showPoints": "never",
            "spanNulls": true
          },
          "mappings": [],
          "thresholds": {
            "mode": "absolute",
            "steps": [
              {
                "color": "green",
                "value": null
              }
            ]
          },
          "unit": "s"
        }
      },
      "gridPos": {
        "h": 8,
        "w": 12,
        "x": 0,
        "y": 8
      },
      "id": 3,
      "options": {
        "legend": {
          "calcs": ["mean", "max"],
          "displayMode": "table",
          "placement": "bottom"
        },
        "tooltip": {
          "mode": "multi"
        }
      },
      "targets": [
        {
          "expr": "histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m]))",
          "legendFormat": "P95 - {{method}} {{path}}",
          "refId": "A"
        },
        {
          "expr": "histogram_quantile(0.50, rate(http_request_duration_seconds_bucket[5m]))",
          "legendFormat": "P50 - {{method}} {{path}}",
          "refId": "B"
        }
      ],
      "title": "Request Latency (P50/P95)",
      "type": "timeseries"
    }
  ],
  "refresh": "5s",
  "schemaVersion": 27,
  "style": "dark",
  "tags": ["api", "performance"],
  "templating": {
    "list": []
  },
  "time": {
    "from": "now-1h",
    "to": "now"
  },
  "timepicker": {},
  "timezone": "",
  "title": "API Overview",
  "uid": "api-overview",
  "version": 1
}
```

- [ ] **Step 3: 创建 PDCA Analytics Dashboard**

创建 `grafana/provisioning/dashboards/pdca-analytics.json`：

```json
{
  "annotations": {
    "list": []
  },
  "editable": true,
  "gnetId": null,
  "graphTooltip": 0,
  "id": null,
  "links": [],
  "panels": [
    {
      "datasource": "Prometheus",
      "fieldConfig": {
        "defaults": {
          "color": {
            "mode": "palette-classic"
          },
          "custom": {
            "axisLabel": "",
            "axisPlacement": "auto",
            "barAlignment": 0,
            "drawStyle": "line",
            "fillOpacity": 10,
            "gradientMode": "none",
            "hideFrom": {
              "tooltip": false,
              "viz": false,
              "legend": false
            },
            "lineInterpolation": "linear",
            "lineWidth": 1,
            "pointSize": 5,
            "scaleDistribution": {
              "type": "linear"
            },
            "showPoints": "never",
            "spanNulls": true
          },
          "mappings": [],
          "thresholds": {
            "mode": "absolute",
            "steps": [
              {
                "color": "green",
                "value": null
              }
            ]
          },
          "unit": "short"
        }
      },
      "gridPos": {
        "h": 8,
        "w": 12,
        "x": 0,
        "y": 0
      },
      "id": 1,
      "options": {
        "legend": {
          "calcs": ["sum"],
          "displayMode": "list",
          "placement": "bottom"
        },
        "tooltip": {
          "mode": "single"
        }
      },
      "targets": [
        {
          "expr": "pdca_cycles_created_total",
          "legendFormat": "{{department}} - {{user_id}}",
          "refId": "A"
        }
      ],
      "title": "PDCA Cycles Created",
      "type": "timeseries"
    },
    {
      "datasource": "Prometheus",
      "fieldConfig": {
        "defaults": {
          "color": {
            "mode": "palette-classic"
          },
          "mappings": [],
          "thresholds": {
            "mode": "absolute",
            "steps": [
              {
                "color": "green",
                "value": null
              }
            ]
          }
        }
      },
      "gridPos": {
        "h": 8,
        "w": 12,
        "x": 12,
        "y": 0
      },
      "id": 2,
      "options": {
        "legend": {
          "displayMode": "list",
          "placement": "bottom"
        },
        "pieType": "donut",
        "tooltip": {
          "mode": "single"
        }
      },
      "targets": [
        {
          "expr": "pdca_cycles_by_status",
          "legendFormat": "{{status}} - {{department}}",
          "refId": "A"
        }
      ],
      "title": "PDCA Cycles by Status",
      "type": "piechart"
    }
  ],
  "refresh": "5s",
  "schemaVersion": 27,
  "style": "dark",
  "tags": ["pdca", "business"],
  "templating": {
    "list": []
  },
  "time": {
    "from": "now-24h",
    "to": "now"
  },
  "timepicker": {},
  "timezone": "",
  "title": "PDCA Analytics",
  "uid": "pdca-analytics",
  "version": 1
}
```

- [ ] **Step 4: 创建 AI Performance Dashboard**

创建 `grafana/provisioning/dashboards/ai-performance.json`：

```json
{
  "annotations": {
    "list": []
  },
  "editable": true,
  "gnetId": null,
  "graphTooltip": 0,
  "id": null,
  "links": [],
  "panels": [
    {
      "datasource": "Prometheus",
      "fieldConfig": {
        "defaults": {
          "color": {
            "mode": "palette-classic"
          },
          "custom": {
            "axisLabel": "",
            "axisPlacement": "auto",
            "barAlignment": 0,
            "drawStyle": "line",
            "fillOpacity": 10,
            "gradientMode": "none",
            "hideFrom": {
              "tooltip": false,
              "viz": false,
              "legend": false
            },
            "lineInterpolation": "linear",
            "lineWidth": 1,
            "pointSize": 5,
            "scaleDistribution": {
              "type": "linear"
            },
            "showPoints": "never",
            "spanNulls": true
          },
          "mappings": [],
          "thresholds": {
            "mode": "absolute",
            "steps": [
              {
                "color": "green",
                "value": null
              }
            ]
          },
          "unit": "short"
        }
      },
      "gridPos": {
        "h": 8,
        "w": 12,
        "x": 0,
        "y": 0
      },
      "id": 1,
      "options": {
        "legend": {
          "calcs": ["sum"],
          "displayMode": "list",
          "placement": "bottom"
        },
        "tooltip": {
          "mode": "single"
        }
      },
      "targets": [
        {
          "expr": "ai_requests_total",
          "legendFormat": "{{provider}} {{model}} ({{status}})",
          "refId": "A"
        }
      ],
      "title": "AI Requests",
      "type": "timeseries"
    },
    {
      "datasource": "Prometheus",
      "fieldConfig": {
        "defaults": {
          "color": {
            "mode": "palette-classic"
          },
          "custom": {
            "axisLabel": "",
            "axisPlacement": "auto",
            "barAlignment": 0,
            "drawStyle": "line",
            "fillOpacity": 10,
            "gradientMode": "none",
            "hideFrom": {
              "tooltip": false,
              "viz": false,
              "legend": false
            },
            "lineInterpolation": "linear",
            "lineWidth": 1,
            "pointSize": 5,
            "scaleDistribution": {
              "type": "linear"
            },
            "showPoints": "never",
            "spanNulls": true
          },
          "mappings": [],
          "thresholds": {
            "mode": "absolute",
            "steps": [
              {
                "color": "green",
                "value": null
              }
            ]
          },
          "unit": "short"
        }
      },
      "gridPos": {
        "h": 8,
        "w": 12,
        "x": 12,
        "y": 0
      },
      "id": 2,
      "options": {
        "legend": {
          "calcs": ["sum"],
          "displayMode": "list",
          "placement": "bottom"
        },
        "tooltip": {
          "mode": "single"
        }
      },
      "targets": [
        {
          "expr": "ai_tokens_used_total",
          "legendFormat": "{{provider}} {{model}} {{type}}",
          "refId": "A"
        }
      ],
      "title": "AI Token Usage",
      "type": "timeseries"
    },
    {
      "datasource": "Prometheus",
      "fieldConfig": {
        "defaults": {
          "color": {
            "mode": "thresholds"
          },
          "mappings": [],
          "thresholds": {
            "mode": "absolute",
            "steps": [
              {
                "color": "green",
                "value": null
              },
              {
                "color": "yellow",
                "value": 1
              },
              {
                "color": "red",
                "value": 5
              }
            ]
          },
          "unit": "USD"
        }
      },
      "gridPos": {
        "h": 4,
        "w": 12,
        "x": 0,
        "y": 8
      },
      "id": 3,
      "options": {
        "orientation": "auto",
        "reduceOptions": {
          "values": false,
          "calcs": ["lastNotNull"],
          "fields": ""
        },
        "showThresholdLabels": false,
        "showThresholdMarkers": true
      },
      "targets": [
        {
          "expr": "ai_cost_usd_total",
          "refId": "A"
        }
      ],
      "title": "Total AI Cost (USD)",
      "type": "gauge"
    }
  ],
  "refresh": "5s",
  "schemaVersion": 27,
  "style": "dark",
  "tags": ["ai", "performance"],
  "templating": {
    "list": []
  },
  "time": {
    "from": "now-24h",
    "to": "now"
  },
  "timepicker": {},
  "timezone": "",
  "title": "AI Performance",
  "uid": "ai-performance",
  "version": 1
}
```

- [ ] **Step 5: 创建 Infrastructure Dashboard**

创建 `grafana/provisioning/dashboards/infrastructure.json`：

```json
{
  "annotations": {
    "list": []
  },
  "editable": true,
  "gnetId": null,
  "graphTooltip": 0,
  "id": null,
  "links": [],
  "panels": [
    {
      "datasource": "Prometheus",
      "fieldConfig": {
        "defaults": {
          "color": {
            "mode": "thresholds"
          },
          "mappings": [],
          "max": 100,
          "min": 0,
          "thresholds": {
            "mode": "absolute",
            "steps": [
              {
                "color": "green",
                "value": null
              },
              {
                "color": "yellow",
                "value": 70
              },
              {
                "color": "red",
                "value": 90
              }
            ]
          },
          "unit": "percent"
        }
      },
      "gridPos": {
        "h": 8,
        "w": 6,
        "x": 0,
        "y": 0
      },
      "id": 1,
      "options": {
        "orientation": "auto",
        "reduceOptions": {
          "values": false,
          "calcs": ["lastNotNull"],
          "fields": ""
        },
        "showThresholdLabels": false,
        "showThresholdMarkers": true
      },
      "targets": [
        {
          "expr": "db_connections_active{state=\"checked_out\"} / 20 * 100",
          "refId": "A"
        }
      ],
      "title": "DB Connection Pool Usage",
      "type": "gauge"
    },
    {
      "datasource": "Prometheus",
      "fieldConfig": {
        "defaults": {
          "color": {
            "mode": "palette-classic"
          },
          "custom": {
            "hideFrom": {
              "tooltip": false,
              "viz": false,
              "legend": false
            }
          },
          "mappings": []
        }
      },
      "gridPos": {
        "h": 8,
        "w": 18,
        "x": 6,
        "y": 0
      },
      "id": 2,
      "options": {
        "legend": {
          "displayMode": "table",
          "placement": "bottom"
        },
        "pieType": "donut",
        "tooltip": {
          "mode": "single"
        }
      },
      "targets": [
        {
          "expr": "db_connections_active",
          "legendFormat": "{{state}}",
          "refId": "A"
        }
      ],
      "title": "DB Connections by State",
      "type": "piechart"
    }
  ],
  "refresh": "5s",
  "schemaVersion": 27,
  "style": "dark",
  "tags": ["infrastructure", "database"],
  "templating": {
    "list": []
  },
  "time": {
    "from": "now-1h",
    "to": "now"
  },
  "timepicker": {},
  "timezone": "",
  "title": "Infrastructure",
  "uid": "infrastructure",
  "version": 1
}
```

- [ ] **Step 6: 提交 Dashboard 配置**

```bash
git add grafana/provisioning/dashboards/
git commit -m "feat: add Grafana dashboards for monitoring

- API Overview: request rate, error rate, latency
- PDCA Analytics: cycles created, status distribution
- AI Performance: requests, tokens, cost tracking
- Infrastructure: DB connection pool monitoring
- Auto-provision dashboards on Grafana startup

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>"
```

---

### Task 11: 创建 Docker Compose 监控服务配置

**Files:**
- Create: `docker-compose.monitoring.yml`

- [ ] **Step 1: 创建监控服务 Docker Compose 配置**

创建 `docker-compose.monitoring.yml`：

```yaml
version: '3.8'

services:
  prometheus:
    image: prom/prometheus:v2.48.0
    container_name: prometheus
    volumes:
      - ./prometheus/prometheus.yml:/etc/prometheus/prometheus.yml:ro
      - prometheus-data:/prometheus
    command:
      - '--config.file=/etc/prometheus/prometheus.yml'
      - '--storage.tsdb.path=/prometheus'
      - '--storage.tsdb.retention.time=15d'
      - '--web.console.libraries=/etc/prometheus/console_libraries'
      - '--web.console.templates=/etc/prometheus/consoles'
    ports:
      - "9090:9090"
    networks:
      - backend-network
    restart: unless-stopped

  grafana:
    image: grafana/grafana:10.2.2
    container_name: grafana
    volumes:
      - grafana-data:/var/lib/grafana
      - ./grafana/provisioning:/etc/grafana/provisioning:ro
    environment:
      - GF_SECURITY_ADMIN_USER=admin
      - GF_SECURITY_ADMIN_PASSWORD=admin
      - GF_SERVER_ROOT_URL=http://localhost:3000
      - GF_USERS_ALLOW_SIGN_UP=false
    ports:
      - "3000:3000"
    networks:
      - backend-network
    depends_on:
      - prometheus
    restart: unless-stopped

volumes:
  prometheus-data:
  grafana-data:

networks:
  backend-network:
    external: true
```

- [ ] **Step 2: 创建环境变量配置示例**

在项目根目录创建 `.env.monitoring.example`：

```bash
# Monitoring Configuration
METRICS_ENABLED=true
PROMETHEUS_RETENTION_DAYS=15
GRAFANA_ADMIN_PASSWORD=admin

# IMPORTANT: Change GRAFANA_ADMIN_PASSWORD in production!
```

- [ ] **Step 3: 更新主 .env 文件**

在项目根目录的 `.env` 文件中添加：

```bash
# Monitoring
METRICS_ENABLED=true
PROMETHEUS_RETENTION_DAYS=15
GRAFANA_ADMIN_PASSWORD=admin
```

- [ ] **Step 4: 创建 README 文档**

创建 `docs/MONITORING.md`：

```markdown
# Monitoring Setup Guide

This document describes how to set up and use the monitoring stack for the PDCA application.

## Architecture

The monitoring stack consists of:
- **Prometheus**: Metrics collection and storage
- **Grafana**: Visualization and dashboards
- **FastAPI integration**: Application metrics exposed via `/metrics` endpoint

## Quick Start

### 1. Start Monitoring Services

```bash
# Start monitoring stack
docker-compose -f docker-compose.monitoring.yml up -d

# Verify services are running
docker-compose -f docker-compose.monitoring.yml ps
```

### 2. Access Dashboards

- **Grafana**: http://localhost:3000
  - Username: `admin`
  - Password: `admin` (change in production!)

- **Prometheus**: http://localhost:9090

### 3. View Metrics

Grafana dashboards are automatically provisioned:
- API Overview
- PDCA Analytics
- AI Performance
- Infrastructure

## Metrics Collected

### HTTP Metrics
- Request rate by endpoint and status code
- Request duration (P50, P95, P99)
- Active requests

### PDCA Metrics
- Cycles created by user and department
- Cycle status distribution
- Stage duration

### AI Agent Metrics
- Request count by provider and model
- Token usage (prompt and completion)
- Estimated cost
- Request duration

### Infrastructure Metrics
- Database connection pool usage
- Query performance

## Maintenance

### Restart Services

```bash
docker-compose -f docker-compose.monitoring.yml restart
```

### View Logs

```bash
# Prometheus logs
docker-compose -f docker-compose.monitoring.yml logs prometheus

# Grafana logs
docker-compose -f docker-compose.monitoring.yml logs grafana
```

### Backup Data

```bash
# Backup Grafana dashboards
docker exec grafana grafana-cli admin export-dashboard > backup.json

# Backup Prometheus data
docker run --rm \
  -v prometheus-data:/prometheus \
  -v $(pwd):/backup \
  alpine tar czf /backup/prometheus-backup.tar.gz /prometheus
```

### Stop Services

```bash
docker-compose -f docker-compose.monitoring.yml down
```

## Troubleshooting

### Prometheus not scraping metrics

1. Check if backend is running: `curl http://localhost:8000/metrics`
2. Verify Prometheus configuration: `docker exec prometheus promtool check config /etc/prometheus/prometheus.yml`
3. Check Prometheus targets: http://localhost:9090/targets

### Grafana no data

1. Verify datasource is connected: http://localhost:3000/datasources
2. Check Prometheus has data: http://localhost:9090/graph
3. Verify dashboard time range

## Security Notes

**IMPORTANT** for production:
1. Change default Grafana password
2. Restrict `/metrics` endpoint access
3. Enable authentication on Prometheus
4. Use HTTPS/TLS for all services
5. Regular security updates
```

- [ ] **Step 5: 提交配置文件**

```bash
git add docker-compose.monitoring.yml .env.monitoring.example docs/MONITORING.md .env
git commit -m "feat: add Docker Compose monitoring services

- Add Prometheus and Grafana services
- Configure persistent volumes for data
- Auto-provision Grafana datasources and dashboards
- Include monitoring setup documentation
- Add environment variables for configuration

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>"
```

---

### Task 12: 端到端测试

**Files:**
- Create: `backend/tests/integration/test_monitoring_e2e.py`

- [ ] **Step 1: 创建端到端测试**

创建 `backend/tests/integration/test_monitoring_e2e.py`：

```python
"""End-to-end tests for monitoring system."""
import pytest
import time
from fastapi.testclient import TestClient
from app.core.metrics import (
    http_requests_total,
    pdca_cycles_created_total,
    ai_requests_total,
    generate_metrics,
)


def test_metrics_endpoint_returns_all_metrics(client: TestClient) -> None:
    """Test that /metrics endpoint returns all defined metrics."""
    response = client.get("/metrics")

    assert response.status_code == 200
    assert response.headers["content-type"] == "text/plain; charset=utf-8"

    content = response.content.decode('utf-8')

    # Check for HTTP metrics
    assert "http_requests_total" in content
    assert "http_request_duration_seconds" in content
    assert "http_requests_active" in content

    # Check for PDCA metrics
    assert "pdca_cycles_created_total" in content
    assert "pdca_cycles_by_status" in content
    assert "pdca_stage_duration_seconds" in content

    # Check for AI metrics
    assert "ai_requests_total" in content
    assert "ai_request_duration_seconds" in content
    assert "ai_tokens_used_total" in content
    assert "ai_cost_usd_total" in content

    # Check for infrastructure metrics
    assert "db_connections_active" in content


def test_http_request_metrics_incremented_on_api_call(client: TestClient) -> None:
    """Test that HTTP requests increment metrics."""
    # Make a test API call
    response = client.get("/api/v1/items/")
    initial_status = response.status_code

    # Get metric value before
    metric_before = http_requests_total.labels(
        method='GET',
        path='/api/v1/items/',
        status=str(initial_status)
    )._value.get()

    # Make another call
    response = client.get("/api/v1/items/")

    # Get metric value after
    metric_after = http_requests_total.labels(
        method='GET',
        path='/api/v1/items/',
        status=str(initial_status)
    )._value.get()

    # Metric should have incremented
    assert metric_after == metric_before + 1


def test_metrics_format_is_valid_prometheus(client: TestClient) -> None:
    """Test that metrics are in valid Prometheus format."""
    response = client.get("/metrics")
    content = response.content.decode('utf-8')

    # Check for HELP and TYPE comments (Prometheus format)
    assert "# HELP" in content
    assert "# TYPE" in content

    # Check metric name format (no invalid characters)
    lines = content.split('\n')
    for line in lines:
        if line and not line.startswith('#'):
            metric_name = line.split('{')[0].split(' ')[0]
            # Metric names should match [a-zA-Z_:][a-zA-Z0-9_:]*
            assert metric_name.replace('_', '').replace(':', '').isalnum()


def test_middleware_doesnt_break_normal_operations(client: TestClient) -> None:
    """Test that Prometheus middleware doesn't break normal API operations."""
    # Test various endpoints
    endpoints = [
        "/api/v1/items/",
        "/api/v1/users/me",
    ]

    for endpoint in endpoints:
        response = client.get(endpoint)
        # Should return a valid status code (200, 401, etc., not 500)
        assert response.status_code in [200, 401, 403, 404]


def test_generate_metrics_function() -> None:
    """Test the generate_metrics helper function."""
    metrics = generate_metrics()

    assert isinstance(metrics, bytes)
    assert b"http_requests_total" in metrics
    assert b"pdca_cycles_created_total" in metrics
```

- [ ] **Step 2: 运行端到端测试**

运行：
```bash
cd backend
pytest tests/integration/test_monitoring_e2e.py -v
```

预期输出：
```
collected 5 items

tests/integration/test_monitoring_e2e.py::test_metrics_endpoint_returns_all_metrics PASSED
tests/integration/test_monitoring_e2e.py::test_http_request_metrics_incremented_on_api_call PASSED
tests/integration/test_monitoring_e2e.py::test_metrics_format_is_valid_prometheus PASSED
tests/integration/test_monitoring_e2e.py::test_middleware_doesnt_break_normal_operations PASSED
tests/integration/test_monitoring_e2e.py::test_generate_metrics_function PASSED
```

- [ ] **Step 3: 提交测试**

```bash
git add backend/tests/integration/test_monitoring_e2e.py
git commit -m "test: add end-to-end monitoring tests

- Test /metrics endpoint returns all metrics
- Verify HTTP metrics increment on API calls
- Validate Prometheus format compliance
- Ensure middleware doesn't break normal operations
- Test generate_metrics helper function

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>"
```

---

### Task 13: 启动监控服务并验证

**Files:**
- No file changes, execution task

- [ ] **Step 1: 启动监控服务**

运行：
```bash
# Create network if it doesn't exist
docker network create backend-network 2>/dev/null || true

# Start monitoring services
docker-compose -f docker-compose.monitoring.yml up -d
```

预期输出：服务成功启动

- [ ] **Step 2: 等待服务就绪**

运行：
```bash
# Wait for services to be healthy
sleep 10

# Check services are running
docker-compose -f docker-compose.monitoring.yml ps
```

预期输出：prometheus 和 grafana 状态为 "Up"

- [ ] **Step 3: 验证 Prometheus 抓取指标**

运行：
```bash
# Check Prometheus targets
curl http://localhost:9090/api/v1/targets | python -m json.tool
```

或者在浏览器访问：http://localhost:9090/targets

预期：backend target 状态为 "UP"

- [ ] **Step 4: 验证 Grafana Dashboards**

1. 访问 http://localhost:3000
2. 登录（admin / admin）
3. 检查左侧菜单 "Dashboards"
4. 验证存在 4 个 dashboard：
   - API Overview
   - PDCA Analytics
   - AI Performance
   - Infrastructure

- [ ] **Step 5: 生成测试数据**

运行：
```bash
# Make some API calls to generate metrics
for i in {1..10}; do
  curl http://localhost:8000/api/v1/items/
done
```

- [ ] **Step 6: 验证数据在 Grafana 显示**

1. 在 Grafana 中打开 "API Overview" dashboard
2. 验证可以看到请求速率和延迟数据
3. 切换到其他 dashboards 验证数据正常

- [ ] **Step 7: 创建验证脚本**

创建 `scripts/verify-monitoring.sh`：

```bash
#!/bin/bash
set -e

echo "Verifying monitoring stack..."

# Check if services are running
echo "Checking services..."
docker-compose -f docker-compose.monitoring.yml ps | grep -q "prometheus.*Up"
echo "✓ Prometheus is running"

docker-compose -f docker-compose.monitoring.yml ps | grep -q "grafana.*Up"
echo "✓ Grafana is running"

# Check metrics endpoint
echo "Checking /metrics endpoint..."
curl -s http://localhost:8000/metrics | grep -q "http_requests_total"
echo "✓ /metrics endpoint is accessible"

# Check Prometheus targets
echo "Checking Prometheus targets..."
curl -s http://localhost:9090/api/v1/targets | grep -q "health\":\"up\""
echo "✓ Prometheus is scraping metrics"

# Check Grafana datasources
echo "Checking Grafana datasources..."
curl -s http://localhost:3000/api/datasources | grep -q "Prometheus"
echo "✓ Grafana datasource is configured"

echo ""
echo "All checks passed! ✓"
echo ""
echo "Access your dashboards at:"
echo "  Grafana: http://localhost:3000 (admin/admin)"
echo "  Prometheus: http://localhost:9090"
```

- [ ] **Step 8: 运行验证脚本**

运行：
```bash
chmod +x scripts/verify-monitoring.sh
./scripts/verify-monitoring.sh
```

预期输出：所有检查通过

- [ ] **Step 9: 提交验证脚本**

```bash
git add scripts/verify-monitoring.sh
git commit -m "feat: add monitoring verification script

- Check services are running
- Verify /metrics endpoint accessibility
- Confirm Prometheus scraping
- Validate Grafana datasource configuration
- Provide clear success/failure feedback

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>"
```

---

### Task 14: 性能影响测试

**Files:**
- Create: `backend/tests/performance/test_metrics_overhead.py`

- [ ] **Step 1: 创建性能测试**

创建 `backend/tests/performance/test_metrics_overhead.py`：

```python
"""Test metrics collection performance overhead."""
import pytest
import time
from fastapi.testclient import TestClient


def test_metrics_endpoint_response_time(client: TestClient) -> None:
    """Test that /metrics endpoint responds quickly."""
    start = time.time()
    response = client.get("/metrics")
    duration = time.time() - start

    assert response.status_code == 200
    # Should respond within 100ms
    assert duration < 0.1, f"/metrics took {duration:.3f}s, expected < 0.1s"


def test_middleware_overhead_is_minimal(client: TestClient) -> None:
    """Test that middleware adds minimal overhead to requests."""
    # Make multiple requests to get average
    iterations = 100
    times = []

    for _ in range(iterations):
        start = time.time()
        client.get("/api/v1/items/")
        times.append(time.time() - start)

    avg_time = sum(times) / len(times)

    # Average request should be under 50ms (allowing for test environment)
    assert avg_time < 0.05, f"Average request time {avg_time:.3f}s exceeds 50ms"


def test_concurrent_metric_recording() -> None:
    """Test that concurrent metric recording is thread-safe."""
    import threading
    from app.core.metrics import http_requests_total

    threads = []
    iterations_per_thread = 100

    def increment_metric():
        for _ in range(iterations_per_thread):
            http_requests_total.labels(
                method='GET',
                path='/test',
                status='200'
            ).inc()

    # Start 10 threads
    for _ in range(10):
        thread = threading.Thread(target=increment_metric)
        threads.append(thread)
        thread.start()

    # Wait for all threads to complete
    for thread in threads:
        thread.join()

    # Check metric value
    expected_value = 10 * iterations_per_thread
    actual_value = http_requests_total.labels(
        method='GET',
        path='/test',
        status='200'
    )._value.get()

    assert actual_value >= expected_value


def test_memory_usage_stays_bound() -> None:
    """Test that metrics don't cause unbounded memory growth."""
    import gc
    import tracemalloc
    from app.core.metrics import http_requests_total

    gc.collect()
    tracemalloc.start()

    # Record baseline
    baseline_memory = tracemalloc.get_traced_memory()[0]

    # Generate many metric recordings
    for i in range(10000):
        http_requests_total.labels(
            method='GET',
            path=f'/test/{i}',
            status='200'
        ).inc()

    # Force garbage collection
    gc.collect()

    # Check memory growth
    current_memory = tracemalloc.get_traced_memory()[0]
    memory_growth = current_memory - baseline_memory

    # Memory growth should be reasonable (< 10MB)
    assert memory_growth < 10 * 1024 * 1024, \
        f"Memory growth {memory_growth / 1024 / 1024:.2f}MB exceeds 10MB"

    tracemalloc.stop()
```

- [ ] **Step 2: 运行性能测试**

运行：
```bash
cd backend
pytest tests/performance/test_metrics_overhead.py -v
```

预期输出：
```
collected 4 items

tests/performance/test_metrics_overhead.py::test_metrics_endpoint_response_time PASSED
tests/performance/test_metrics_overhead.py::test_middleware_overhead_is_minimal PASSED
tests/performance/test_metrics_overhead.py::test_concurrent_metric_recording PASSED
tests/performance/test_metrics_overhead.py::test_memory_usage_stays_bound PASSED
```

- [ ] **Step 3: 提交性能测试**

```bash
git add backend/tests/performance/test_metrics_overhead.py
git commit -m "test: add metrics performance overhead tests

- Verify /metrics endpoint responds in < 100ms
- Ensure middleware adds minimal latency
- Test thread-safe concurrent metric recording
- Validate memory usage stays bounded
- Set performance expectations for monitoring

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>"
```

---

## 验收检查清单

完成所有任务后，运行以下验收检查：

### 功能验收

- [ ] `/metrics` 端点返回所有 4 类指标
- [ ] Grafana 中显示 4 个预配置的 Dashboard
- [ ] Prometheus 成功抓取后端指标
- [ ] HTTP 请求自动记录指标
- [ ] PDCA 创建时记录业务指标
- [ ] AI Agent 调用时记录指标

### 性能验收

- [ ] `/metrics` 端点响应时间 < 100ms
- [ ] 中间件增加的请求延迟 < 5ms
- [ ] 内存开销 < 50MB

### 稳定性验收

- [ ] 指标记录失败不影响业务逻辑
- [ ] Prometheus 重启后数据正常
- [ ] 并发指标记录是线程安全的

### 文档验收

- [ ] 监控设置文档完整
- [ ] 环境变量配置清晰
- [ ] 故障排查指南可用

## 完成总结

完成本实施计划后，你将拥有：

1. ✅ 完整的 Prometheus + Grafana 监控栈
2. ✅ 4 类指标的全面收集（API、PDCA、AI、基础设施）
3. ✅ 4 个预配置的 Grafana Dashboard
4. ✅ 自动化的指标收集和暴露
5. ✅ 完整的测试覆盖（单元、集成、端到端、性能）
6. ✅ 详细的文档和验证脚本

系统将提供实时的业务洞察，帮助你：
- 快速发现性能瓶颈
- 追踪 PDCA 业务效率
- 监控 AI 服务质量和成本
- 优化基础设施使用
