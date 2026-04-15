#!/bin/bash

echo "🔍 E2E 测试环境检查"
echo "=========================================="
echo ""

# 检查 Node.js
echo "1. 检查 Node.js..."
if command -v node &> /dev/null; then
    echo "✅ Node.js 已安装: $(node --version)"
else
    echo "❌ Node.js 未安装"
    exit 1
fi

# 检查 npm
echo ""
echo "2. 检查 npm..."
if command -v npm &> /dev/null; then
    echo "✅ npm 已安装: $(npm --version)"
else
    echo "❌ npm 未安装"
    exit 1
fi

# 检查依赖安装
echo ""
echo "3. 检查依赖安装..."
if [ -d "node_modules" ]; then
    echo "✅ 依赖已安装"
else
    echo "⚠️  依赖未安装"
    echo "   运行: npm install"
fi

# 检查环境配置
echo ""
echo "4. 检查环境配置..."
if [ -f ".env" ]; then
    echo "✅ 环境配置文件存在"
else
    echo "⚠️  环境配置文件缺失"
    echo "   运行: cp .env.example .env"
fi

echo ""
echo "=========================================="
echo "🎯 环境检查完成！"
echo ""
echo "运行测试: npm run test:chromium"
