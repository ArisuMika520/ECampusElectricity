#!/bin/bash
# 完整环境设置脚本

set -e

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}ECampus Electricity - Web 版本环境设置${NC}"
echo -e "${BLUE}========================================${NC}"

# 1. 检查系统依赖
echo -e "\n${YELLOW}[1/5] 检查系统依赖...${NC}"
if ! command -v python3 &> /dev/null; then
    echo "错误: 未找到 python3"
    exit 1
fi
if ! command -v node &> /dev/null; then
    echo "错误: 未找到 node"
    exit 1
fi
echo -e "${GREEN}✓ 系统依赖检查通过${NC}"

# 2. 安装系统包（如果需要）
if ! python3 -m venv --help &> /dev/null; then
    echo -e "${YELLOW}需要安装 python3-venv，请运行:${NC}"
    echo "  sudo apt install python3-venv python3-pip"
    exit 1
fi

# 3. 设置后端
echo -e "\n${YELLOW}[2/5] 设置后端环境...${NC}"
if [ ! -d "backend/venv" ]; then
    cd backend
    bash setup.sh
    cd ..
else
    echo -e "${GREEN}✓ 后端虚拟环境已存在${NC}"
fi

# 4. 安装前端依赖
echo -e "\n${YELLOW}[3/5] 安装前端依赖...${NC}"
if [ ! -d "frontend/node_modules" ]; then
    cd frontend
    npm install
    cd ..
else
    echo -e "${GREEN}✓ 前端依赖已安装${NC}"
fi

# 5. 安装根目录依赖（concurrently）
echo -e "\n${YELLOW}[4/5] 安装开发工具...${NC}"
if [ ! -f "node_modules/.bin/concurrently" ]; then
    npm install
else
    echo -e "${GREEN}✓ 开发工具已安装${NC}"
fi

# 6. 检查数据库
echo -e "\n${YELLOW}[5/5] 检查数据库...${NC}"
cd backend
source venv/bin/activate
python scripts/check_db.py
cd ..

echo -e "\n${GREEN}========================================${NC}"
echo -e "${GREEN}环境设置完成！${NC}"
echo -e "${GREEN}========================================${NC}"
echo -e "\n使用以下命令启动开发模式："
echo -e "  ${BLUE}npm run dev${NC}     # 同时启动前后端（开发模式）"
echo -e "  ${BLUE}npm run start${NC}   # 同时启动前后端（生产模式）"
echo -e "\n或者使用脚本："
echo -e "  ${BLUE}bash scripts/dev.sh${NC}   # 开发模式"
echo -e "  ${BLUE}bash scripts/start.sh${NC} # 生产模式"

