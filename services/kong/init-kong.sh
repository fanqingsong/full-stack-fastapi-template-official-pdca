#!/bin/bash
# Kong 初始化脚本
# 用于创建服务、路由和插件配置
# 支持开发和生产环境自动配置

# 允许命令失败（某些非关键命令可能失败）
set +e

# 默认使用 localhost（从宿主机执行）
KONG_ADMIN_URL="${KONG_ADMIN_URL:-http://localhost:8001}"
DOMAIN="${DOMAIN:-localhost}"
STACK_NAME="${STACK_NAME:-full-stack-fastapi-project}"
ENVIRONMENT="${ENVIRONMENT:-local}"

# 函数：检查服务是否存在
service_exists() {
  local service_name=$1
  local response=$(curl -s "${KONG_ADMIN_URL}/services/${service_name}")
  # 检查是否包含 "id" 字段（存在）或 "message"（错误）
  echo "${response}" | grep -q '"id"' 2>/dev/null
}

# 函数：创建服务（如果不存在）
create_service_if_not_exists() {
  local service_name=$1
  local service_url=$2

  if service_exists "${service_name}"; then
    echo "  ✓ 服务 ${service_name} 已存在，跳过创建"
    return 0
  fi

  echo "  → 创建服务 ${service_name}..."
  local response=$(curl -s -X POST "${KONG_ADMIN_URL}/services" \
    --data "name=${service_name}" \
    --data "url=${service_url}")

  # 检查响应中是否包含 id 字段
  if echo "${response}" | grep -q '"id"'; then
    echo "  ✓ 服务 ${service_name} 创建成功"
    return 0
  else
    # 可能是 UNIQUE violation（服务已存在），这不算失败
    if echo "${response}" | grep -q "UNIQUE violation"; then
      echo "  ✓ 服务 ${service_name} 已存在"
      return 0
    fi
    echo "  ✗ 服务 ${service_name} 创建失败: ${response}"
    return 1
  fi
}

# 函数：创建路由（如果不存在）
create_route_if_not_exists() {
  local service_name=$1
  local route_name=$2
  shift 2
  local route_data=("$@")

  # 检查路由是否存在
  local route_response=$(curl -s "${KONG_ADMIN_URL}/services/${service_name}/routes/${route_name}")
  if echo "${route_response}" | grep -q '"id"' 2>/dev/null; then
    echo "  ✓ 路由 ${route_name} 已存在，跳过创建"
    return 0
  fi

  echo "  → 创建路由 ${route_name}..."
  local curl_args=()
  for arg in "${route_data[@]}"; do
    curl_args+=("--data" "${arg}")
  done

  local response=$(curl -s -X POST "${KONG_ADMIN_URL}/services/${service_name}/routes" "${curl_args[@]}")

  # 检查响应中是否包含 id 字段
  if echo "${response}" | grep -q '"id"'; then
    echo "  ✓ 路由 ${route_name} 创建成功"
    return 0
  else
    # 可能是 UNIQUE violation（路由已存在），这不算失败
    if echo "${response}" | grep -q "UNIQUE violation"; then
      echo "  ✓ 路由 ${route_name} 已存在"
      return 0
    fi
    echo "  ✗ 路由 ${route_name} 创建失败: ${response}"
    return 1
  fi
}

# 函数：创建插件（如果不存在）
create_plugin_if_not_exists() {
  local service_name=$1
  local plugin_name=$2
  shift 2
  local plugin_data=("$@")

  # 检查插件是否存在 - 检查所有插件中是否有匹配的 name
  local plugins_response=$(curl -s "${KONG_ADMIN_URL}/services/${service_name}/plugins")
  if echo "${plugins_response}" | grep -q "\"name\":\"${plugin_name}\""; then
    echo "  ✓ 插件 ${plugin_name} 已存在，跳过创建"
    return 0
  fi

  echo "  → 创建插件 ${plugin_name}..."
  local curl_args=("--data" "name=${plugin_name}")
  for arg in "${plugin_data[@]}"; do
    curl_args+=("--data" "${arg}")
  done

  local response=$(curl -s -X POST "${KONG_ADMIN_URL}/services/${service_name}/plugins" "${curl_args[@]}")

  # 检查响应中是否包含 id 字段
  if echo "${response}" | grep -q '"id"'; then
    echo "  ✓ 插件 ${plugin_name} 创建成功"
    return 0
  else
    echo "  ⚠️  插件 ${plugin_name} 创建失败，跳过"
    return 0
  fi
}

echo "=========================================="
echo "Kong 初始化脚本"
echo "环境: ${ENVIRONMENT}"
echo "域名: ${DOMAIN}"
echo "=========================================="
echo ""

echo "等待 Kong Admin API 就绪..."
max_attempts=60
attempt=0
while [ $attempt -lt $max_attempts ]; do
  response=$(curl -s --max-time 2 --connect-timeout 1 "${KONG_ADMIN_URL}/status" 2>/dev/null)
  if [ $? -eq 0 ] && echo "$response" | grep -q '"database":{"reachable":true}'; then
    echo "✓ Kong 已就绪"
    break
  fi

  attempt=$((attempt + 1))
  if [ $attempt -eq $max_attempts ]; then
    echo "✗ 错误: Kong Admin API 未就绪"
    echo "使用 Konga UI 手动配置: http://localhost:1337"
    return 0
  fi
  if [ $((attempt % 10)) -eq 0 ]; then
    echo "  等待中... (${attempt}/${max_attempts})"
  fi
  sleep 2
done

echo ""
echo "开始配置 Kong 服务..."
echo ""

# 创建 Backend 服务
echo "1. 配置 Backend 服务..."
# 后端服务 URL 指向 /api 前缀，因为 FastAPI 路由都在 /api 下
create_service_if_not_exists "${STACK_NAME}-backend" "http://backend:8000/api"

# 创建 Backend 路由
if [ "${ENVIRONMENT}" = "local" ]; then
  # 开发环境：支持路径路由 /api
  # 注意：strip_path=true 因为后端已经包含 /api 前缀
  create_route_if_not_exists "${STACK_NAME}-backend" "${STACK_NAME}-backend-route-path" \
    "paths[]=/api" \
    "strip_path=true"
fi

# 域名路由
create_route_if_not_exists "${STACK_NAME}-backend" "${STACK_NAME}-backend-route-host" \
  "hosts[]=api.${DOMAIN}" \
  "paths[]=/api" \
  "strip_path=true"

# 为 Backend 添加 CORS 插件
create_plugin_if_not_exists "${STACK_NAME}-backend" "cors" \
  "config.origins=*" \
  "config.methods=GET" \
  "config.methods=POST" \
  "config.methods=PUT" \
  "config.methods=DELETE" \
  "config.methods=OPTIONS" \
  "config.methods=PATCH" \
  "config.credentials=true" \
  "config.max_age=3600"

# 创建 Frontend 服务
echo ""
echo "2. 配置 Frontend 服务..."
if [ "${ENVIRONMENT}" = "local" ]; then
  FRONTEND_URL="http://frontend:5173"
else
  FRONTEND_URL="http://frontend:80"
fi
create_service_if_not_exists "${STACK_NAME}-frontend" "${FRONTEND_URL}"

# 创建 Frontend 路由
if [ "${ENVIRONMENT}" = "local" ]; then
  create_route_if_not_exists "${STACK_NAME}-frontend" "${STACK_NAME}-frontend-route-path" \
    "paths[]=/dashboard" \
    "paths[]=/login" \
    "paths[]=/signup" \
    "paths[]=/" \
    "strip_path=false"
fi

# 域名路由
create_route_if_not_exists "${STACK_NAME}-frontend" "${STACK_NAME}-frontend-route-host" \
  "hosts[]=dashboard.${DOMAIN}" \
  "paths[]=/"

# 创建 Adminer 服务
echo ""
echo "3. 配置 Adminer 服务..."
create_service_if_not_exists "${STACK_NAME}-adminer" "http://adminer:8080"

create_route_if_not_exists "${STACK_NAME}-adminer" "${STACK_NAME}-adminer-route" \
  "hosts[]=adminer.${DOMAIN}"

echo ""
echo "=========================================="
echo "Kong 配置完成！"
echo "=========================================="
echo ""
echo "服务访问地址："
echo "  通过 Kong (http://localhost:8000)："
echo "    - Backend API: http://localhost:8000/api"
echo "    - Frontend: http://localhost:8000/dashboard"
echo ""
if [ "${ENVIRONMENT}" = "local" ]; then
  echo "  直接访问（开发调试）："
  echo "    - Backend API: http://localhost:8000"
  echo "    - Frontend: http://localhost:5173"
  echo "    - Adminer: http://localhost:8080"
fi
echo ""
echo "  域名路由（如果配置了 DOMAIN）："
echo "    - Backend API: http://api.${DOMAIN}/api"
echo "    - Frontend: http://dashboard.${DOMAIN}"
echo "    - Adminer: http://adminer.${DOMAIN}"
echo ""
echo "管理界面："
echo "  - Kong Admin API: http://localhost:8001"
echo "  - Konga UI: http://localhost:1337"
echo ""
