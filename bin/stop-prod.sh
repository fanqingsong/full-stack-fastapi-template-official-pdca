#!/bin/bash

# 生产环境停止脚本
# 用法: ./bin/stop-prod.sh [--clean] [--with-airflow]

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"

cd "$PROJECT_DIR"

ENV_FILE=".env.prod"
COMPOSE_FILE="compose.prod.yml"
ENV_NAME="生产环境"
CLEAN_VOLUMES=false
WITH_AIRFLOW=false

# 检查参数
for arg in "$@"; do
    if [[ "$arg" == "--clean" ]] || [[ "$arg" == "-c" ]]; then
        CLEAN_VOLUMES=true
    fi
    if [[ "$arg" == "--with-airflow" ]] || [[ "$arg" == "-a" ]]; then
        WITH_AIRFLOW=true
    fi
done

echo "🛑 停止${ENV_NAME}服务..."

# 加载环境变量以获取 STACK_NAME
if [ -f "$ENV_FILE" ]; then
    export $(grep -v '^#' "$ENV_FILE" | grep -v '^$' | xargs)
fi

# 构建 compose 文件列表（包含 Kong）
COMPOSE_FILES="-f compose.yml -f compose.kong.yml -f $COMPOSE_FILE"

# 添加 Airflow 支持
if [ "$WITH_AIRFLOW" = "true" ]; then
    COMPOSE_FILES="$COMPOSE_FILES -f compose.airflow.yml"
    echo "✅ 包含 Airflow 服务"
fi

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
    echo "💡 提示: 要清理所有数据（包括 Kong），请使用: ./bin/stop-prod.sh --clean"
fi
