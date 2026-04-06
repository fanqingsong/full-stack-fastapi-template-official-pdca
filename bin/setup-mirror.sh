#!/bin/bash

# 配置 Docker 镜像加速器
# 支持多个国内镜像源

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"

echo "🔧 配置 Docker 镜像加速器..."
echo ""

# Docker 配置目录
DOCKER_CONFIG_DIR="$HOME/.docker"
DOCKER_CONFIG_FILE="$DOCKER_CONFIG_DIR/daemon.json"

# 创建配置目录（如果不存在）
mkdir -p "$DOCKER_CONFIG_DIR"

# 备份现有配置
if [ -f "$DOCKER_CONFIG_FILE" ]; then
    echo "备份现有配置到: $DOCKER_CONFIG_FILE.bak"
    cp "$DOCKER_CONFIG_FILE" "$DOCKER_CONFIG_FILE.bak"
fi

# 检测可用的镜像源
echo "检测可用的镜像源..."

# 镜像源列表（按优先级排序）
MIRRORS=(
    "https://docker.1panel.live"
    "https://docker.xuanyuan.me"
    "https://docker.chenby.cn"
    "https://docker.awsl9527.cn"
    "https://dockerpull.org"
    "https://dockerhub.icu"
)

# 测试镜像源是否可用
AVAILABLE_MIRRORS=()
for mirror in "${MIRRORS[@]}"; do
    if curl -s --connect-timeout 3 "https://registry-1.docker.io/v2/" -H "Accept: application/vnd.docker.distribution.manifest.v2+json" >/dev/null 2>&1; then
        echo "  ✓ Docker Hub 官方可访问"
    fi

    # 测试镜像源
    if curl -s --connect-timeout 3 "$mirror" >/dev/null 2>&1; then
        echo "  ✓ $mirror"
        AVAILABLE_MIRRORS+=("$mirror")
    fi
done

# 如果没有检测到可用镜像源，使用默认推荐列表
if [ ${#AVAILABLE_MIRRORS[@]} -eq 0 ]; then
    echo "  ⚠️  未能检测到可用镜像源，使用推荐配置"
    AVAILABLE_MIRRORS=(
        "https://docker.1panel.live"
        "https://docker.xuanyuan.me"
        "https://docker.chenby.cn"
    )
fi

echo ""
echo "将配置以下镜像源:"
for mirror in "${AVAILABLE_MIRRORS[@]}"; do
    echo "  - $mirror"
done
echo ""

# 生成配置 JSON
MIRROR_JSON=""
for mirror in "${AVAILABLE_MIRRORS[@]}"; do
    if [ -z "$MIRROR_JSON" ]; then
        MIRROR_JSON="    \"$mirror\""
    else
        MIRROR_JSON="$MIRROR_JSON,
    \"$mirror\""
    fi
done

# 创建新的配置文件
cat > "$DOCKER_CONFIG_FILE" <<EOF
{
  "registry-mirrors": [
$MIRROR_JSON
  ],
  "log-driver": "json-file",
  "log-opts": {
    "max-size": "10m",
    "max-file": "3"
  }
}
EOF

echo "✅ Docker 配置已更新: $DOCKER_CONFIG_FILE"
echo ""
echo "配置内容:"
cat "$DOCKER_CONFIG_FILE"
echo ""

# 检测操作系统并提供重启命令
echo "🔄 请重启 Docker 使配置生效:"
echo ""
if [ -f /etc/debian_version ] || [ -f /etc/lsb-release ]; then
    echo "  sudo systemctl restart docker"
elif [ -f /etc/redhat-release ]; then
    echo "  sudo systemctl restart docker"
elif command -v service >/dev/null 2>&1; then
    echo "  sudo service docker restart"
elif [ "$(uname)" == "Darwin" ]; then
    echo "  macOS: 请在 Docker Desktop 中点击 Restart"
else
    echo "  请根据你的系统手动重启 Docker"
fi
echo ""
echo "重启后，可以运行以下命令验证配置:"
echo "  docker info | grep -A 10 \"Registry Mirrors\""
echo ""
