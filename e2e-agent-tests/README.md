# E2E Agent Tests for FastAPI Project

AI Agent-driven End-to-End testing framework using natural language test definitions.

## 🚀 Quick Start

### 1. 安装依赖
```bash
npm install
```

### 2. 安装系统依赖
```bash
sudo apt-get install -y libnspr4 libnss3 libatk1.0-0t64 libatk-bridge2.0-0t64 libcups2t64 libdrm2 libxkbcommon0 libxcomposite1 libxdamage1 libxfixes3 libxrandr2 libgbm1 libpango-1.0-0 libcairo2 libasound2t64 libatspi2.0-0t64
```

### 3. 配置环境
```bash
cp .env.example .env
# Edit .env with your application URLs
```

### 4. 运行测试
```bash
# 运行基础流程测试
npm run test:chromium

# 运行所有测试
npm run test:chromium:all

# 解析测试（不执行）
npm run test:parse
```

## 📝 创建测试

Tests are written in plain Markdown format! See `tests/` directory for examples.

## 🎯 Features

- ✅ Natural language test definitions
- ✅ Smart element location
- ✅ Automatic form filling
- ✅ Screenshot capture
- ✅ Detailed error reporting
- ✅ FastAPI optimized

## 📊 Reports

Test results and screenshots are saved in the `reports/` directory.

## 🔧 Configuration

Edit `.env` file to configure:
- Application URLs
- Test user credentials
- Timeout values
- Headless mode
