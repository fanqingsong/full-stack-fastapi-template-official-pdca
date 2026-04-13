# 如何检查可观测性功能

本文档提供详细的步骤来检查和使用刚刚实现的业务指标监控系统。

## 🚀 快速检查（3 步）

### 1. 启动后端服务

```bash
# 方法 1: 使用 uvicorn 直接启动
cd backend
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# 方法 2: 使用项目脚本（如果存在）
./scripts/backend-pre-start.sh
```

### 2. 检查 /metrics 端点

```bash
# 在另一个终端运行
./scripts/check-observability.sh
```

### 3. 查看原始指标

```bash
# 查看所有指标
curl http://localhost:8000/metrics

# 查看特定类型的指标
curl http://localhost:8000/metrics | grep "http_requests"
curl http://localhost:8000/metrics | grep "pdca_"
curl http://localhost:8000/metrics | grep "ai_"
curl http://localhost:8000/metrics | grep "db_"
```

## 📊 完整监控栈检查（需要 Docker）

### 启动 Prometheus + Grafana

```bash
# 1. 创建 Docker 网络（如果不存在）
docker network create backend-network 2>/dev/null || true

# 2. 启动监控服务
docker-compose -f docker-compose.monitoring.yml up -d

# 3. 验证服务运行
docker-compose -f docker-compose.monitoring.yml ps
```

### 访问监控界面

**Grafana Dashboard**:
- URL: http://localhost:3000
- 用户名: `admin`
- 密码: `admin`
- 包含 4 个预配置的 Dashboard

**Prometheus**:
- URL: http://localhost:9090
- 查看 Targets: http://localhost:9090/targets
- 查询指标: http://localhost:9090/graph

### 验证监控栈

```bash
# 运行验证脚本
./scripts/verify-monitoring.sh
```

## 🔬 详细检查清单

### ✅ 基础功能检查

#### 1. 检查指标定义模块

```bash
cd backend
python3 -c "
from app.core.metrics import (
    http_requests_total, 
    pdca_cycles_created_total,
    ai_requests_total,
    db_connections_active
)
print('✅ 所有指标模块加载成功')
print(f'HTTP 指标: {http_requests_total._name}')
print(f'PDCA 指标: {pdca_cycles_created_total._name}')
print(f'AI 指标: {ai_requests_total._name}')
print(f'DB 指标: {db_connections_active._name}')
"
```

#### 2. 检查中间件注册

```bash
# 查看 main.py 中的中间件注册
grep -A 5 "PrometheusMiddleware" backend/app/main.py

# 应该看到：
# if settings.METRICS_ENABLED:
#     app.add_middleware(PrometheusMiddleware)
```

#### 3. 测试 /metrics 端点响应

```bash
# 测试端点可访问性
curl -I http://localhost:8000/metrics

# 应该返回：
# HTTP/1.1 200 OK
# content-type: text/plain; charset=utf-8

# 测试指标格式正确性
curl -s http://localhost:8000/metrics | head -20

# 应该看到：
# HELP http_requests_total Total HTTP requests
# TYPE http_requests_total counter
# http_requests_total{method="GET",path="/api/v1/...",status="200"} 1.0
```

### 📈 业务指标检查

#### 测试 HTTP 请求指标

```bash
# 发送几个请求生成指标
for i in {1..5}; do
  curl -s http://localhost:8000/api/v1/items/ > /dev/null
done

# 查看指标是否增加
curl -s http://localhost:8000/metrics | grep "http_requests_total"
```

#### 测试 PDCA 业务指标

```bash
# 使用 API 创建 PDCA 循环（需要认证）
# 这会触发 pdca_cycles_created_total 指标

curl -X POST http://localhost:8000/api/v1/pdca/cycles \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "测试 PDCA",
    "description": "测试指标记录",
    "goal": "验证监控功能"
  }'

# 查看 PDCA 指标
curl -s http://localhost:8000/metrics | grep "pdca_"
```

#### 测试 AI Agent 指标

```bash
# 调用 AI Agent 生成指标
# 这会触发 ai_requests_total, ai_tokens_used_total 等指标

curl -X POST http://localhost:8000/api/v1/pdca/execute \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "task": "测试 AI 监控指标"
  }'

# 查看 AI 指标
curl -s http://localhost:8000/metrics | grep "ai_"
```

### 🔧 监控服务检查

#### 检查 Prometheus 配置

```bash
# 验证配置文件语法
docker run --rm -v $(pwd)/prometheus:/etc/prometheus \
  prom/prometheus:v2.48.0 \
  promtool check config /etc/prometheus/prometheus.yml

# 检查抓取目标
curl -s http://localhost:9090/api/v1/targets | python3 -m json.tool

# 应该看到 backend target 的 health 为 "up"
```

#### 检查 Grafana 数据源

```bash
# 查看 Grafana 数据源配置
curl -s http://localhost:3000/api/datasources \
  -u admin:admin | python3 -m json.tool

# 应该看到 Prometheus 数据源已配置
```

#### 检查 Dashboard

在 Grafana 中：
1. 登录 http://localhost:3000 (admin/admin)
2. 点击左侧菜单 "Dashboards"
3. 应该看到 4 个 Dashboard：
   - API Overview
   - PDCA Analytics
   - AI Performance
   - Infrastructure

## 🧪 运行测试

### 单元测试

```bash
cd backend

# 运行指标测试
python3 -m pytest tests/core/test_metrics.py -v

# 运行中间件测试
python3 -m pytest tests/api/test_middleware.py -v

# 运行 PDCA 指标测试
python3 -m pytest tests/pdca/test_crud_metrics.py -v

# 运行端到端测试
python3 -m pytest tests/integration/test_monitoring_e2e.py -v

# 运行性能测试
python3 -m pytest tests/performance/test_metrics_overhead.py -v
```

### 性能验证

```bash
# 测试 /metrics 端点响应时间
time curl -s http://localhost:8000/metrics > /dev/null

# 应该在 100ms 内完成
```

## 🐛 故障排查

### 问题 1: /metrics 端点返回 404

**原因**: METRICS_ENABLED 可能被设置为 false

**解决**:
```bash
# 检查 .env 文件
grep METRICS_ENABLED .env

# 应该是：
# METRICS_ENABLED=true

# 如果不是，修改并重启后端
```

### 问题 2: Prometheus 无法抓取指标

**检查**:
```bash
# 1. 确认后端 /metrics 端点可访问
curl http://localhost:8000/metrics

# 2. 确认 Prometheus 能访问 backend
# 在浏览器访问: http://localhost:9090/targets

# 3. 检查网络连接
docker network inspect backend-network
```

**解决**:
```bash
# 确保 backend 和 prometheus 在同一网络
# 重新启动监控服务
docker-compose -f docker-compose.monitoring.yml restart
```

### 问题 3: Grafana 无数据显示

**检查**:
```bash
# 1. 验证 Prometheus 有数据
curl -s http://localhost:9090/api/v1/query?query=up | python3 -m json.tool

# 2. 验证 Grafana 数据源
curl -s http://localhost:3000/api/datasources \
  -u admin:admin | python3 -m json.tool

# 3. 检查 Dashboard 时间范围
# Grafana 默认显示最近数据，如果没有数据会显示空白
```

**解决**:
```bash
# 1. 生成一些测试数据
for i in {1..20}; do
  curl -s http://localhost:8000/api/v1/items/ > /dev/null
done

# 2. 在 Grafana 中刷新 Dashboard
# 3. 调整时间范围到 "Last 5 minutes"
```

### 问题 4: 指标未记录

**检查指标是否定义**:
```bash
cd backend
python3 -c "
from app.core.metrics import http_requests_total
print('指标名称:', http_requests_total._name)
print('标签:', http_requests_total._labelnames)
"
```

**检查日志**:
```bash
# 查看后端日志是否有指标记录失败的警告
# 应该看到类似：
# WARNING: Failed to record metric: ...
```

## 📊 预期的监控输出示例

### /metrics 端点输出示例

```
# HELP http_requests_total Total HTTP requests
# TYPE http_requests_total counter
http_requests_total{method="GET",path="/api/v1/items/",status="200"} 15.0
http_requests_total{method="GET",path="/metrics",status="200"} 3.0

# HELP pdca_cycles_created_total Total PDCA cycles created
# TYPE pdca_cycles_created_total counter
pdca_cycles_created_total{department="engineering",user_id="123"} 5.0

# HELP ai_requests_total Total AI agent requests
# TYPE ai_requests_total counter
ai_requests_total{model="gpt-4",provider="openai",status="success"} 12.0
ai_tokens_used_total{model="gpt-4",provider="openai",type="prompt"} 1500.0
ai_cost_usd_total{model="gpt-4",provider="openai"} 0.18

# HELP db_connections_active Active database connections
# TYPE db_connections_active gauge
db_connections_active{state="checked_out"} 2.0
db_connections_active{state="idle"} 3.0
```

## ✅ 验收标准

完成以下检查即表示可观测性功能正常：

- [ ] /metrics 端点返回 200 状态码
- [ ] 指标包含 4 大类（HTTP、PDCA、AI、基础设施）
- [ ] 发送 API 请求后 http_requests_total 增加
- [ ] Prometheus 成功抓取 backend 指标
- [ ] Grafana 数据源连接正常
- [ ] Grafana Dashboard 可以显示数据

## 🎯 下一步

1. **启动服务并验证**
   ```bash
   ./scripts/check-observability.sh
   ```

2. **查看详细文档**
   ```bash
   cat docs/MONITORING.md
   ```

3. **生成测试数据并观察**
   - 发送 API 请求
   - 查看 Grafana Dashboard
   - 验证指标正确记录

4. **生产部署准备**
   - 修改默认密码
   - 配置认证
   - 启用 HTTPS

需要帮助执行任何步骤吗？
