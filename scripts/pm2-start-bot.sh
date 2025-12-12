#!/bin/bash
# PM2 启动 Bot 的包装脚本

SCRIPT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
cd "$SCRIPT_DIR/Bot/src/bot"

# 设置 Python 路径
export PYTHONPATH="$SCRIPT_DIR/Bot/src:$SCRIPT_DIR/Bot:$PYTHONPATH"

# 使用系统 Python 或虚拟环境
if [ -f "$SCRIPT_DIR/Bot/venv/bin/python" ]; then
    exec "$SCRIPT_DIR/Bot/venv/bin/python" Elect_bot.py
else
    exec python3 Elect_bot.py
fi



