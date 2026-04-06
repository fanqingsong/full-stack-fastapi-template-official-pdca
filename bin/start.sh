#!/bin/bash

# 多环境启动脚本
# 用法: ./bin/start.sh [dev|staging|prod] [--with-airflow]
# 默认: dev

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"

cd "$PROJECT_DIR"

# 解析参数
ENVIRONMENT=${1:-dev}
WITH_AIRFLOW=false

# 检查是否启用 Airflow
if [[ "$2" == "--with-airflow" ]] || [[ "$2" == "-a" ]]; then
    WITH_AIRFLOW=true
elif [[ "$1" == "--with-airflow" ]] || [[ "$1" == "-a" ]]; then
    WITH_AIRFLOW=true
    ENVIRONMENT="dev"
fi

# 验证环境参数
if [[ ! "$ENVIRONMENT" =~ ^(dev|staging|prod)$ ]]; then
    echo "❌ 错误: 无效的环境 '$ENVIRONMENT'"
    echo ""
    echo "用法:"
    echo "  ./bin/start.sh [dev|staging|prod] [--with-airflow]"
    echo ""
    echo "示例:"
    echo "  ./bin/start.sh dev                # 开发环境（默认，支持热加载）"
    echo "  ./bin/start.sh staging            # 预发布环境"
    echo "  ./bin/start.sh prod               # 生产环境"
    echo "  ./bin/start.sh dev --with-airflow # 开发环境 + Airflow"
    exit 1
fi

# 环境配置
case $ENVIRONMENT in
    dev)
        ENV_FILE=".env.dev"
        COMPOSE_FILE="compose.dev.yml"
        ENV_NAME="开发环境"
        ;;
    staging)
        ENV_FILE=".env.staging"
        COMPOSE_FILE="compose.staging.yml"
        ENV_NAME="预发布环境"
        ;;
    prod)
        ENV_FILE=".env.prod"
        COMPOSE_FILE="compose.prod.yml"
        ENV_NAME="生产环境"
        ;;
esac

echo "🚀 启动${ENV_NAME}..."
echo "📁 项目目录: $PROJECT_DIR"

# 检查环境文件是否存在
if [ ! -f "$ENV_FILE" ]; then
    echo "❌ 错误: 环境配置文件不存在: $ENV_FILE"
    exit 1
fi

# 加载环境变量
export $(grep -v '^#' "$ENV_FILE" | grep -v '^$' | xargs)

# 构建 compose 文件列表（包含 Kong）
COMPOSE_FILES="-f compose.yml -f compose.kong.yml -f $COMPOSE_FILE"

# 添加 Airflow 支持
if [ "$WITH_AIRFLOW" = "true" ]; then
    COMPOSE_FILES="$COMPOSE_FILES -f compose.airflow.yml"
    echo "✅ 已启用 Airflow 工作流调度服务"
fi

# 先停止现有服务（如果存在）
echo "检查并停止现有服务..."
if docker compose $COMPOSE_FILES ps -q 2>/dev/null | grep -q .; then
    echo "停止现有服务..."
    docker compose $COMPOSE_FILES down --remove-orphans 2>/dev/null || true
fi

# 清理残留容器
echo "清理残留容器..."
docker ps -a --filter "name=${STACK_NAME}" --format "{{.ID}} {{.Status}}" | grep -E "Created|Exited" | awk '{print $1}' | xargs -r docker rm -f 2>/dev/null || true

sleep 2

# 启动服务
echo ""
echo "启动${ENV_NAME}服务..."

if [ "$ENVIRONMENT" = "dev" ]; then
    echo "ℹ️  开发环境特性:"
    echo "   - Kong API Gateway 网关"
    echo "   - 前后端热加载已启用"
    echo "   - 端口已暴露: backend(8000), frontend(5173), adminer(8080), mailcatcher(1080)"
    echo "   - Kong (8000), Kong Admin API (8001), Konga UI (1337)"
    echo "   - Cypress E2E 测试服务可用 (使用 --profile test 启动)"
    if [ "$WITH_AIRFLOW" = "true" ]; then
        echo "   - Airflow 工作流调度已启用 (9090, 5555)"
    fi
fi

docker compose $COMPOSE_FILES up -d --build

# 等待服务启动
echo ""
echo "等待服务启动..."
sleep 5

# 等待 Kong 启动并初始化
echo ""
echo "等待 Kong Gateway 启动..."
if docker compose $COMPOSE_FILES ps kong 2>/dev/null | grep -q "Up"; then
    echo "等待 Kong Admin API 就绪..."
    for i in {1..60}; do
        if curl -s http://localhost:8001/status 2>/dev/null | grep -q '"database":{"reachable":true}'; then
            echo "✅ Kong 已就绪"
            break
        fi
        if [ $i -eq 60 ]; then
            echo "⚠️  警告: Kong 启动超时"
        fi
        sleep 2
    done

    # 执行 Kong 初始化脚本
    echo ""
    echo "初始化 Kong 配置..."
    if [ -f "$PROJECT_DIR/services/kong/init-kong.sh" ]; then
        export KONG_ADMIN_URL="http://localhost:8001"
        bash "$PROJECT_DIR/services/kong/init-kong.sh" || echo "⚠️  Kong 初始化脚本执行失败"
    else
        echo "⚠️  警告: Kong 初始化脚本不存在"
    fi
else
    echo "⚠️  警告: Kong 服务未启动"
fi

# 检查服务状态
echo ""
echo "✅ ${ENV_NAME}启动完成！"
echo ""
echo "📋 服务状态:"
docker compose $COMPOSE_FILES ps
echo ""

# 显示访问地址
if [ "$ENVIRONMENT" = "dev" ]; then
    echo "🌐 访问地址:"
    echo "  📌 通过 Kong API Gateway:"
    echo "    - Backend API: http://localhost:8000/api"
    echo "    - Frontend: http://localhost:8000/dashboard"
    echo ""
    echo "  📌 直接访问（本地开发）:"
    echo "    - Backend API: http://localhost:8000"
    echo "    - Frontend: http://localhost:5173"
    echo "    - Adminer: http://localhost:8080"
    echo "    - Mailcatcher: http://localhost:1080"
    echo ""
    echo "  📌 管理界面:"
    echo "    - Kong Admin API: http://localhost:8001"
    echo "    - Konga UI: http://localhost:1337"
    if [ "$WITH_AIRFLOW" = "true" ]; then
        echo "    - Airflow Web UI: http://localhost:9090 (airflow/airflow)"
        echo "    - Flower UI: http://localhost:5555"
    fi
    echo ""
    echo "🧪 运行 E2E 测试:"
    echo "  docker compose $COMPOSE_FILES --profile test up cypress"
    echo ""
elif [ "$ENVIRONMENT" = "staging" ]; then
    echo "🌐 访问地址:"
    echo "  - Frontend: https://dashboard.${DOMAIN}"
    echo "  - Backend API: https://api.${DOMAIN}"
    echo "  - Adminer: http://localhost:8080 (内部访问)"
    echo ""
    echo "  📌 管理界面:"
    echo "    - Kong Admin API: http://localhost:8001 (内部访问)"
    echo "    - Konga UI: http://localhost:1337 (内部访问)"
    if [ "$WITH_AIRFLOW" = "true" ]; then
        echo "    - Airflow Web UI: http://localhost:9090 (内部访问)"
        echo "    - Flower UI: http://localhost:5555 (内部访问)"
    fi
    echo ""
else
    echo "🌐 访问地址:"
    echo "  - Frontend: https://dashboard.${DOMAIN}"
    echo "  - Backend API: https://api.${DOMAIN}"
    if [ "$WITH_AIRFLOW" = "true" ]; then
        echo "  - Airflow Web UI: http://localhost:9090 (内部访问)"
        echo "  - Flower UI: http://localhost:5555 (内部访问)"
    fi
    echo ""
fi

echo "📝 查看日志: docker compose $COMPOSE_FILES logs -f"
if [ "$WITH_AIRFLOW" = "true" ]; then
    echo "🛑 停止服务: ./bin/stop.sh $ENVIRONMENT --with-airflow"
else
    echo "🛑 停止服务: ./bin/stop.sh $ENVIRONMENT"
fi
echo ""
