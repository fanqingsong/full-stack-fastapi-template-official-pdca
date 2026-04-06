#!/bin/bash

# 开发环境停止脚本
# 用法: ./bin/stop-dev.sh [--clean]

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"

cd "$PROJECT_DIR"

ENV_FILE=".env.dev"
COMPOSE_FILE="compose.dev.yml"
ENV_NAME="开发环境"
CLEAN_VOLUMES=false

# 检查参数
for arg in "$@"; do
    if [[ "$arg" == "--clean" ]] || [[ "$arg" == "-c" ]]; then
        CLEAN_VOLUMES=true
    fi
done

echo "🛑 停止${ENV_NAME}服务..."

# 加载环境变量以获取 STACK_NAME
if [ -f "$ENV_FILE" ]; then
    export $(grep -v '^#' "$ENV_FILE" | grep -v '^$' | xargs)
fi

# 构建 compose 文件列表（包含 Kong 和 Airflow）
COMPOSE_FILES="-f compose.yml -f compose.kong.yml -f compose.airflow.yml -f $COMPOSE_FILE"
echo "✅ 包含 Airflow 服务"

# 停止服务
echo "停止服务..."

if [ "$CLEAN_VOLUMES" = "true" ]; then
    docker compose $COMPOSE_FILES down -v
else
    docker compose $COMPOSE_FILES down
fi

echo "✅ ${ENV_NAME}服务已停止！"

if [ "$CLEAN_VOLUMES" = "true" ]; then
    echo ""
    echo "💡 提示: 已清理所有数据卷（包括 Kong 数据）"
else
    echo ""
    echo "💡 提示: 要清理所有数据（包括 Kong），请使用: ./bin/stop-dev.sh --clean"
fi
