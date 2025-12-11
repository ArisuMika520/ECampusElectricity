#!/bin/bash
# PM2 快速启动脚本 - 一键启动所有服务

set -e

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m'

SCRIPT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
cd "$SCRIPT_DIR"

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}ECampusElectricity - PM2 快速启动${NC}"
echo -e "${BLUE}========================================${NC}"

# 检查 PM2 是否安装
if ! command -v pm2 &> /dev/null; then
    echo -e "${RED}✗ PM2 未安装${NC}"
    echo -e "${YELLOW}请先安装 PM2:${NC}"
    echo -e "  ${BLUE}npm install -g pm2${NC}"
    exit 1
fi

echo -e "${GREEN}✓ PM2 已安装${NC}"

# 检查环境
echo -e "\n${YELLOW}检查环境...${NC}"

# 检查 Web 后端虚拟环境
if [ ! -d "Web/backend/venv" ]; then
    echo -e "${RED}✗ Web 后端虚拟环境不存在${NC}"
    echo -e "${YELLOW}请先运行:${NC}"
    echo -e "  ${BLUE}cd Web && npm run setup${NC}"
    exit 1
fi
echo -e "${GREEN}✓ Web 后端虚拟环境存在${NC}"

# 检查前端构建
if [ ! -d "Web/frontend/.next" ]; then
    echo -e "${YELLOW}⚠ 前端未构建，正在构建...${NC}"
    cd Web/frontend
    npm run build
    cd "$SCRIPT_DIR"
    echo -e "${GREEN}✓ 前端构建完成${NC}"
else
    echo -e "${GREEN}✓ 前端已构建${NC}"
fi

# 检查配置文件
if [ ! -f "Web/backend/.env" ]; then
    echo -e "${YELLOW}⚠ Web 后端配置文件不存在${NC}"
    echo -e "${YELLOW}请复制并配置:${NC}"
    echo -e "  ${BLUE}cp Web/backend/.env.example Web/backend/.env${NC}"
    echo -e "  ${BLUE}nano Web/backend/.env${NC}"
fi

# 创建日志目录
mkdir -p logs/pm2

# 启动服务
echo -e "\n${GREEN}启动 PM2 服务...${NC}"
pm2 start ecosystem.config.js

echo -e "\n${GREEN}========================================${NC}"
echo -e "${GREEN}启动完成！${NC}"
echo -e "${GREEN}========================================${NC}"
echo -e "\n${BLUE}常用命令:${NC}"
echo -e "  ${BLUE}pm2 status${NC}        # 查看服务状态"
echo -e "  ${BLUE}pm2 logs${NC}          # 查看日志"
echo -e "  ${BLUE}pm2 monit${NC}         # 监控面板"
echo -e "  ${BLUE}pm2 stop all${NC}      # 停止所有服务"
echo -e "  ${BLUE}pm2 restart all${NC}   # 重启所有服务"
echo -e "\n${BLUE}访问地址:${NC}"
echo -e "  前端: ${GREEN}http://localhost:3000${NC}"
echo -e "  后端 API: ${GREEN}http://localhost:8000${NC}"
echo -e "  API 文档: ${GREEN}http://localhost:8000/docs${NC}"
echo ""

