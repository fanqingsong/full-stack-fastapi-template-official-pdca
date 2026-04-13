#!/bin/bash
set -e

echo "=========================================="
echo "🔍 检查可观测性功能"
echo "=========================================="
echo ""

# 检查后端是否运行
echo "1️⃣ 检查后端服务..."
if curl -s http://localhost:8000/metrics > /dev/null 2>&1; then
    echo "✅ 后端服务正在运行"
else
    echo "❌ 后端服务未运行"
    echo ""
    echo "请先启动后端服务："
    echo "  cd backend"
    echo "  uvicorn app.main:app --reload --port 8000"
    exit 1
fi

echo ""

# 检查 /metrics 端点
echo "2️⃣ 检查 /metrics 端点..."
METRICS_CONTENT=$(curl -s http://localhost:8000/metrics)

echo "✅ /metrics 端点可访问"
echo ""
echo "📊 可用的指标类型："
echo "$METRICS_CONTENT" | grep "^# HELP" | cut -d' ' -f2-3 | head -10
echo ""

# 检查具体的指标
echo "3️⃣ 检查具体指标示例："
echo ""
echo "HTTP 指标："
echo "$METRICS_CONTENT" | grep "^http_requests_total" | head -3
echo ""
echo "PDCA 指标："
echo "$METRICS_CONTENT" | grep "^pdca_cycles_created_total" | head -3
echo ""
echo "AI 指标："
echo "$METRICS_CONTENT" | grep "^ai_requests_total" | head -3
echo ""

echo "=========================================="
echo "✅ 基础检查完成！"
echo "=========================================="
echo ""
echo "📝 详细查看所有指标："
echo "  curl http://localhost:8000/metrics | less"
echo ""
echo "🚀 启动完整监控栈（需要 Docker）："
echo "  docker-compose -f docker-compose.monitoring.yml up -d"
echo ""
echo "📊 访问 Grafana Dashboard："
echo "  http://localhost:3000 (admin/admin)"
echo ""
echo "📈 访问 Prometheus："
echo "  http://localhost:9090"
