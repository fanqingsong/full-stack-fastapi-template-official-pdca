#!/bin/bash

# 多环境重启服务脚本
# 用法: ./bin/restart.sh [dev|staging|prod] <service-name> [--no-build]
# 默认环境: dev

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"

cd "$PROJECT_DIR"

# 解析参数
ENVIRONMENT=${1:-dev}
SERVICE_NAME=""
NO_BUILD=false

# 检查第一个参数是否是环境名称
if [[ ! "$1" =~ ^(dev|staging|prod)$ ]]; then
    # 第一个参数不是环境，可能是服务名，默认使用 dev
    ENVIRONMENT="dev"
    SERVICE_NAME=$1
    NO_BUILD_FLAG=$2
else
    ENVIRONMENT=$1
    SERVICE_NAME=$2
    NO_BUILD_FLAG=$3
fi

# 检查是否有 --no-build 参数
if [[ "$SERVICE_NAME" == "--no-build" ]] || [[ "$NO_BUILD_FLAG" == "--no-build" ]]; then
    NO_BUILD=true
    if [[ "$SERVICE_NAME" == "--no-build" ]]; then
        SERVICE_NAME=""
    fi
fi

# 检查是否指定了服务名
if [ -z "$SERVICE_NAME" ]; then
    echo "❌ 错误: 请指定服务名称"
    echo ""
    echo "用法:"
    echo "  ./bin/restart.sh [dev|staging|prod] <service-name> [--no-build]"
    echo ""
    echo "示例:"
    echo "  ./bin/restart.sh dev backend            # 重启开发环境的 backend"
    echo "  ./bin/restart.sh staging frontend       # 重启预发布环境的 frontend"
    echo "  ./bin/restart.sh dev backend --no-build # 重启但不构建"
    echo ""
    echo "可用服务:"
    echo "  - backend"
    echo "  - frontend"
    echo "  - db"
    echo "  - adminer"
    echo "  - kong"
    echo "  - kong-db"
    echo "  - konga"
    echo "  - mailcatcher (仅 dev)"
    echo "  - cypress (仅 dev)"
    echo "  - prestart"
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

# 加载环境变量
if [ -f "$ENV_FILE" ]; then
    export $(grep -v '^#' "$ENV_FILE" | grep -v '^$' | xargs)
fi

# 构建 compose 文件列表（包含 Kong）
COMPOSE_FILES="-f compose.yml -f compose.kong.yml -f $COMPOSE_FILE"

# 验证服务是否存在
if ! docker compose $COMPOSE_FILES config --services 2>/dev/null | grep -q "^${SERVICE_NAME}$"; then
    echo "❌ 错误: 服务 '${SERVICE_NAME}' 在 ${ENV_NAME} 中不存在"
    echo ""
    echo "可用服务:"
    docker compose $COMPOSE_FILES config --services 2>/dev/null | sed 's/^/  - /'
    exit 1
fi

echo "🔄 准备重启${ENV_NAME}服务: ${SERVICE_NAME}"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# 构建服务（如果需要）
if [ "$NO_BUILD" = false ]; then
    echo ""
    echo "📦 构建服务镜像..."
    docker compose $COMPOSE_FILES build --no-cache "${SERVICE_NAME}"

    if [ $? -eq 0 ]; then
        echo "✅ 构建完成"
    else
        echo "❌ 构建失败"
        exit 1
    fi
else
    echo ""
    echo "⏭️  跳过构建（使用 --no-build 参数）"
fi

# 停止服务
echo ""
echo "🛑 停止服务..."
docker compose $COMPOSE_FILES stop "${SERVICE_NAME}"

# 删除旧容器（如果存在）
echo ""
echo "🗑️  删除旧容器..."
docker compose $COMPOSE_FILES rm -f "${SERVICE_NAME}" 2>/dev/null || true

# 启动服务
echo ""
echo "🚀 启动服务..."
docker compose $COMPOSE_FILES up -d "${SERVICE_NAME}"

# 等待服务启动
echo ""
echo "⏳ 等待服务启动..."
sleep 2

# 检查服务状态
echo ""
echo "📊 服务状态:"
docker compose $COMPOSE_FILES ps "${SERVICE_NAME}"

# 显示服务日志（最后10行）
echo ""
echo "📋 服务日志（最后10行）:"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
docker compose $COMPOSE_FILES logs --tail 10 "${SERVICE_NAME}"

echo ""
echo "✅ 服务重启完成！"
echo ""
echo "💡 提示:"
echo "  - 查看完整日志: docker compose $COMPOSE_FILES logs -f ${SERVICE_NAME}"
echo "  - 查看服务状态: docker compose $COMPOSE_FILES ps ${SERVICE_NAME}"
