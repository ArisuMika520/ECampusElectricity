#!/bin/bash
# PM2 启动 Web 前端的包装脚本

cd "$(dirname "$0")/../Web/frontend"

# 检查是否已构建
if [ ! -d ".next" ]; then
    echo "前端未构建，正在构建..."
    npm run build
fi

# 启动生产服务器
exec npm start



