#!/bin/bash
# PM2 启动 Web 后端的包装脚本

cd "$(dirname "$0")/../Web/backend"

# 激活虚拟环境并启动
source venv/bin/activate
exec uvicorn app.main:app --host 0.0.0.0 --port 8000



