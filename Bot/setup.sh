#!/bin/bash
# Bot 项目环境设置脚本

set -e

echo "=========================================="
echo "设置 Bot 开发环境"
echo "=========================================="

# 检查 Python
if ! command -v python3 &> /dev/null; then
    echo "错误: 未找到 python3"
    exit 1
fi

echo "✓ 找到 Python: $(python3 --version)"

# 检查 python3-venv
if ! python3 -m venv --help &> /dev/null; then
    echo ""
    echo "错误: 缺少 python3-venv 包"
    echo "请先安装: sudo apt install python3-venv python3-pip"
    echo ""
    exit 1
fi

# 创建虚拟环境
if [ ! -d "venv" ] || [ ! -f "venv/bin/activate" ]; then
    if [ -d "venv" ]; then
        echo "检测到不完整的虚拟环境，正在删除..."
        rm -rf venv
    fi
    echo "创建虚拟环境..."
    python3 -m venv venv
    if [ ! -f "venv/bin/activate" ]; then
        echo "错误: 虚拟环境创建失败"
        echo "请确保已安装: sudo apt install python3-venv"
        exit 1
    fi
    echo "✓ 虚拟环境创建成功"
else
    echo "✓ 虚拟环境已存在"
fi

# 激活虚拟环境
echo "激活虚拟环境..."
if [ -f "venv/bin/activate" ]; then
    source venv/bin/activate
else
    echo "错误: 无法找到虚拟环境激活脚本"
    exit 1
fi

# 升级 pip
echo "升级 pip..."
python -m pip install --upgrade pip

# 安装依赖
echo "安装依赖包..."
if [ -f "requirements.txt" ]; then
    pip install -r requirements.txt
    echo "✓ 依赖安装完成"
else
    echo "警告: 未找到 requirements.txt"
fi

echo ""
echo "=========================================="
echo "环境设置完成！"
echo "=========================================="
echo ""
echo "使用以下命令激活虚拟环境："
echo "  source venv/bin/activate"
echo ""
echo "然后运行机器人："
echo "  python src/bot/Elect_bot.py"
echo ""
echo "或者使用 PM2 启动："
echo "  pm2 start ../scripts/pm2-start-bot.sh --name bot"
echo ""

