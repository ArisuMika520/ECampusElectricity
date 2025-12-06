#!/bin/bash
# 生产模式启动脚本

set -e

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}启动生产模式（前后端）${NC}"
echo -e "${GREEN}========================================${NC}"

# 检查前端是否已构建
if [ ! -d "frontend/.next" ]; then
    echo -e "${YELLOW}前端未构建，正在构建...${NC}"
    cd frontend
    npm run build
    cd ..
fi

echo -e "${GREEN}启动服务...${NC}"

# 启动服务
npx concurrently \
  --names "后端,前端" \
  --prefix-colors "blue,green" \
  "cd backend && source venv/bin/activate && uvicorn app.main:app --host 0.0.0.0 --port 8000" \
  "cd frontend && npm start"

