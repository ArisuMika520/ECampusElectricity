#!/bin/bash
# 完整环境设置脚本 - 一键安装所有依赖

set -e

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}ECampus Electricity - Web 版本环境设置${NC}"
echo -e "${BLUE}========================================${NC}"

# 获取脚本所在目录
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$PROJECT_ROOT"

# 1. 检查系统依赖
echo -e "\n${YELLOW}[1/6] 检查系统依赖...${NC}"
MISSING_DEPS=0

if ! command -v python3 &> /dev/null; then
    echo -e "${RED}✗ 未找到 python3${NC}"
    echo -e "  请安装 Python 3.10+: https://www.python.org/downloads/"
    MISSING_DEPS=1
else
    PYTHON_VERSION=$(python3 --version | cut -d' ' -f2)
    echo -e "${GREEN}✓ Python: ${PYTHON_VERSION}${NC}"
fi

if ! command -v node &> /dev/null; then
    echo -e "${RED}✗ 未找到 node${NC}"
    echo -e "  请安装 Node.js 18+: https://nodejs.org/"
    MISSING_DEPS=1
else
    NODE_VERSION=$(node --version)
    echo -e "${GREEN}✓ Node.js: ${NODE_VERSION}${NC}"
fi

if ! command -v npm &> /dev/null; then
    echo -e "${RED}✗ 未找到 npm${NC}"
    MISSING_DEPS=1
else
    NPM_VERSION=$(npm --version)
    echo -e "${GREEN}✓ npm: ${NPM_VERSION}${NC}"
fi

if [ $MISSING_DEPS -eq 1 ]; then
    echo -e "\n${RED}请先安装缺失的系统依赖！${NC}"
    exit 1
fi

# 2. 检查 Python venv 模块
echo -e "\n${YELLOW}[2/6] 检查 Python 虚拟环境支持...${NC}"
if ! python3 -m venv --help &> /dev/null; then
    echo -e "${RED}✗ 缺少 python3-venv 模块${NC}"
    echo -e "${YELLOW}请运行以下命令安装:${NC}"
    echo -e "  ${BLUE}sudo apt install python3-venv python3-pip${NC}  # Ubuntu/Debian"
    echo -e "  ${BLUE}sudo yum install python3-venv python3-pip${NC}  # CentOS/RHEL"
    exit 1
else
    echo -e "${GREEN}✓ Python venv 支持已就绪${NC}"
fi

# 3. 设置后端环境
echo -e "\n${YELLOW}[3/6] 设置后端环境（Python 依赖）...${NC}"
if [ ! -d "backend/venv" ] || [ ! -f "backend/venv/bin/activate" ]; then
    if [ -d "backend/venv" ]; then
        echo -e "${YELLOW}检测到不完整的虚拟环境，正在删除...${NC}"
        rm -rf backend/venv
    fi
    
    cd backend
    bash setup.sh
    cd ..
    echo -e "${GREEN}✓ 后端环境设置完成${NC}"
    
    # 显示已安装的 Python 包
    echo -e "${BLUE}已安装的 Python 依赖:${NC}"
    source backend/venv/bin/activate
    pip list | grep -E "(fastapi|uvicorn|sqlmodel|psycopg2|pydantic|requests|websockets)" || true
    deactivate
else
    echo -e "${GREEN}✓ 后端虚拟环境已存在${NC}"
fi

# 4. 安装前端依赖
echo -e "\n${YELLOW}[4/6] 安装前端依赖（Node.js 包）...${NC}"
if [ ! -d "frontend/node_modules" ]; then
    cd frontend
    echo -e "${BLUE}正在安装前端依赖（这可能需要几分钟）...${NC}"
    npm install
    cd ..
    echo -e "${GREEN}✓ 前端依赖安装完成${NC}"
    
    # 显示已安装的主要包
    echo -e "${BLUE}已安装的主要前端依赖:${NC}"
    cd frontend
    npm list --depth=0 2>/dev/null | grep -E "(next|react|tailwind|recharts|axios)" || true
    cd ..
else
    echo -e "${GREEN}✓ 前端依赖已安装${NC}"
fi

# 5. 安装根目录依赖（开发工具）
echo -e "\n${YELLOW}[5/6] 安装开发工具（concurrently）...${NC}"
if [ ! -f "node_modules/.bin/concurrently" ]; then
    echo -e "${BLUE}正在安装开发工具...${NC}"
    npm install
    echo -e "${GREEN}✓ 开发工具安装完成${NC}"
else
    echo -e "${GREEN}✓ 开发工具已安装${NC}"
fi

# 6. 检查数据库连接（可选）
echo -e "\n${YELLOW}[6/6] 检查数据库配置...${NC}"
if [ -f "backend/.env" ]; then
    cd backend
    source venv/bin/activate
    if python scripts/check_db.py 2>/dev/null; then
        echo -e "${GREEN}✓ 数据库连接正常${NC}"
    else
        echo -e "${YELLOW}⚠ 数据库连接失败，请检查 backend/.env 配置${NC}"
        echo -e "  确保 PostgreSQL 已安装并运行"
        echo -e "  确保 DATABASE_URL 配置正确"
    fi
    deactivate
    cd ..
else
    echo -e "${YELLOW}⚠ 未找到 backend/.env 文件${NC}"
    echo -e "  请复制 backend/.env.example 到 backend/.env 并配置"
fi

echo -e "\n${GREEN}========================================${NC}"
echo -e "${GREEN}环境设置完成！${NC}"
echo -e "${GREEN}========================================${NC}"
echo -e "\n${BLUE}下一步操作:${NC}"
echo -e "  1. 配置环境变量: ${YELLOW}cp backend/.env.example backend/.env${NC}"
echo -e "  2. 编辑配置文件: ${YELLOW}nano backend/.env${NC}"
echo -e "  3. 初始化数据库: ${YELLOW}npm run db:init${NC}"
echo -e "\n${BLUE}启动命令:${NC}"
echo -e "  ${GREEN}npm run dev${NC}        # 开发模式（前后端同时启动，支持热重载）"
echo -e "  ${GREEN}npm run start${NC}      # 生产模式（需要先构建前端）"
echo -e "  ${GREEN}./scripts/manage.sh dev${NC}    # 使用脚本管理工具启动开发模式"
echo -e "  ${GREEN}./scripts/manage.sh start${NC}  # 使用脚本管理工具启动生产模式"
echo -e "\n${BLUE}访问地址:${NC}"
echo -e "  前端: ${GREEN}http://localhost:3000${NC}"
echo -e "  后端 API: ${GREEN}http://localhost:8000${NC}"
echo -e "  API 文档: ${GREEN}http://localhost:8000/docs${NC}"
echo ""

