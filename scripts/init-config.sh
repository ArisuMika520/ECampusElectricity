#!/bin/bash

# 统一配置初始化脚本
# 用于快速设置项目配置

set -e

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_ROOT"

echo "=========================================="
echo "ECampusElectricity 配置初始化"
echo "=========================================="
echo

# 检查 .env 是否存在
if [ -f ".env" ]; then
    echo "⚠️  .env 文件已存在"
    read -p "是否覆盖? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "配置初始化已取消"
        exit 0
    fi
fi

# 从模板创建配置文件
if [ ! -f ".env.example" ]; then
    echo "❌ 错误: .env.example 模板文件不存在"
    exit 1
fi

cp .env.example .env
echo "✓ 已从模板创建 .env 文件"
echo

# 交互式配置
echo "请输入以下配置信息（直接回车跳过）："
echo

# 数据库配置
read -p "PostgreSQL 密码 [postgres]: " db_password
db_password=${db_password:-postgres}
sed -i "s|DATABASE_URL=postgresql://postgres:your_password@|DATABASE_URL=postgresql://postgres:${db_password}@|" .env

# JWT 密钥
echo
echo "生成 JWT 密钥..."
secret_key=$(openssl rand -hex 32 2>/dev/null || python3 -c "import secrets; print(secrets.token_hex(32))")
sed -i "s|SECRET_KEY=your-secret-key-change-in-production-use-openssl-rand-hex-32|SECRET_KEY=${secret_key}|" .env
echo "✓ JWT 密钥已生成"

# ShiroJID
echo
read -p "易校园 shiroJID: " shiro_jid
if [ -n "$shiro_jid" ]; then
    sed -i "s|SHIRO_JID=your-shiro-jid-here|SHIRO_JID=${shiro_jid}|" .env
    echo "✓ ShiroJID 已配置"
fi

# QQ Bot 配置（可选）
echo
read -p "是否配置 QQ Bot? (y/N): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    read -p "QQ AppID: " qq_appid
    read -p "QQ Secret: " qq_secret
    
    if [ -n "$qq_appid" ]; then
        sed -i "s|QQ_APPID=your_qq_appid|QQ_APPID=${qq_appid}|" .env
    fi
    if [ -n "$qq_secret" ]; then
        sed -i "s|QQ_SECRET=your_qq_secret|QQ_SECRET=${qq_secret}|" .env
    fi
    echo "✓ QQ Bot 配置已保存"
fi

echo
echo "=========================================="
echo "✅ 配置初始化完成！"
echo "=========================================="
echo
echo "配置文件位置: $PROJECT_ROOT/.env"
echo
echo "下一步："
echo "  1. 检查配置: nano .env"
echo "  2. 同步 Bot 配置: python3 scripts/sync_config.py"
echo "  3. 启动服务: bash scripts/pm2-start-backend.sh"
echo
echo "详细文档: CONFIG_MANAGEMENT.md"
