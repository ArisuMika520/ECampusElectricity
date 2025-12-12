#!/bin/bash
# PM2 启动 Tracker 的包装脚本

SCRIPT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
cd "$SCRIPT_DIR/Script"

# 设置 Python 路径
export PYTHONPATH="$SCRIPT_DIR/Script:$SCRIPT_DIR/Web/backend:$SCRIPT_DIR/Bot:$PYTHONPATH"

# 使用 Web 后端的虚拟环境
exec "$SCRIPT_DIR/Web/backend/venv/bin/python" elect_tracker_db.py



