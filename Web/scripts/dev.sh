#!/bin/bash
# 开发模式启动脚本 - 同时启动前后端

set -e

# 颜色输出
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}启动开发模式（前后端）${NC}"
echo -e "${GREEN}========================================${NC}"

# 检查后端虚拟环境
if [ ! -d "backend/venv" ]; then
    echo -e "${YELLOW}后端虚拟环境不存在，正在创建...${NC}"
    cd backend
    bash setup.sh
    cd ..
fi

# 检查前端依赖
if [ ! -d "frontend/node_modules" ]; then
    echo -e "${YELLOW}前端依赖未安装，正在安装...${NC}"
    cd frontend
    npm install
    cd ..
fi

# 检查数据库
echo -e "${GREEN}检查数据库连接...${NC}"
cd backend
source venv/bin/activate
python scripts/check_db.py
cd ..

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}启动服务...${NC}"
echo -e "${GREEN}后端: http://localhost:8000${NC}"
echo -e "${GREEN}前端: http://localhost:4000${NC}"
echo -e "${GREEN}API 文档: http://localhost:8000/docs${NC}"
echo -e "${GREEN}按 Ctrl+C 停止所有服务${NC}"
echo -e "${GREEN}========================================${NC}"

# 使用 concurrently 启动前后端
npx concurrently \
  --names "后端,前端" \
  --prefix-colors "blue,green" \
  "cd backend && source venv/bin/activate && uvicorn app.main:app --reload --host 0.0.0.0 --port 8000" \
  "cd frontend && npm run dev"

