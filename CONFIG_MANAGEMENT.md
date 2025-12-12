# 统一配置管理指南

## 概述

为了简化配置管理和部署，项目采用**统一配置方案**：

- **单一配置源**：`/root/pro/ECampusElectricity/.env`
- **所有组件**：Bot、Web Backend、Tracker 都从同一个配置文件读取
- **自动同步**：Bot 的 `config.yaml` 可以从 `.env` 自动生成

## 配置文件结构

```
ECampusElectricity/
├── .env                    # 【主配置】所有组件的统一配置
├── .env.example            # 配置模板
├── Bot/
│   └── config.yaml         # 【自动生成】Bot 配置（可选，建议使用 .env）
├── Web/
│   └── backend/
│       ├── .env            # 【已废弃】建议删除
│       └── .env.example    # 【已废弃】建议删除
└── scripts/
    └── sync_config.py      # 配置同步工具
```

## 快速开始

### 1. 初始化配置

```bash
cd /root/pro/ECampusElectricity

# 从模板创建配置文件
cp .env.example .env

# 编辑配置文件
nano .env  # 或使用其他编辑器
```

### 2. 配置必填项

编辑 `.env` 文件，填入以下关键配置：

```bash
# 数据库（必填）
DATABASE_URL=postgresql://postgres:your_password@localhost:5432/electricity_db

# JWT 密钥（必填，生产环境必须修改）
SECRET_KEY=$(openssl rand -hex 32)

# 易校园配置（必填）
SHIRO_JID=your-shiro-jid-from-xiaoyuan-app

# QQ Bot 配置（如果使用 Bot）
QQ_APPID=your_qq_appid
QQ_SECRET=your_qq_secret
```

### 3. 验证配置

```bash
# 测试配置加载
python3 -c "
import sys
sys.path.insert(0, 'Web/backend')
from app.config import settings
print('✓ 配置加载成功')
print(f'  数据库: {settings.DATABASE_URL}')
print(f'  SHIRO_JID: {\"已配置\" if settings.SHIRO_JID else \"未配置\"}')
"
```

### 4. 同步 Bot 配置（可选）

如果需要使用传统的 `config.yaml`：

```bash
python3 scripts/sync_config.py
```

## 配置项说明

### 数据库配置
- `DATABASE_URL`: PostgreSQL 连接字符串

### 认证配置
- `SECRET_KEY`: JWT 加密密钥
- `ALGORITHM`: 加密算法（默认 HS256）
- `ACCESS_TOKEN_EXPIRE_MINUTES`: Token 过期时间

### 易校园 API
- `SHIRO_JID`: 从小程序抓取的认证 ID
- `API_BASE_URL`: 易校园 API 地址

### QQ Bot
- `QQ_APPID`: QQ 开放平台应用 ID
- `QQ_SECRET`: QQ 开放平台密钥

### Tracker
- `TRACKER_CHECK_INTERVAL`: 检查间隔（秒）
- `HISTORY_LIMIT`: 历史记录上限

### 邮件通知
- `SMTP_SERVER`, `SMTP_PORT`, `SMTP_USER`, `SMTP_PASS`

## 部署建议

### 开发环境
直接编辑 `.env` 文件

### 生产环境
推荐使用环境变量注入：

```bash
# 方式1：PM2 使用 ecosystem.config.js
module.exports = {
  apps: [{
    name: "backend",
    env: {
      DATABASE_URL: "postgresql://...",
      SECRET_KEY: "...",
      // ...
    }
  }]
}

# 方式2：Docker 环境变量
docker run -e DATABASE_URL="postgresql://..." ...

# 方式3：系统环境变量
export DATABASE_URL="postgresql://..."
```

## 迁移指南

### 从旧配置迁移

如果你之前使用多个配置文件：

1. **备份旧配置**
   ```bash
   cp Web/backend/.env Web/backend/.env.backup
   cp Bot/config.yaml Bot/config.yaml.backup
   ```

2. **合并到根目录 .env**
   ```bash
   # 将 Web/backend/.env 的内容复制到根目录 .env
   # 将 Bot/config.yaml 的值对应填入 .env
   ```

3. **删除旧配置**（可选）
   ```bash
   rm Web/backend/.env
   # config.yaml 保留作为备份，但程序将优先使用 .env
   ```

4. **测试新配置**
   ```bash
   # 测试 Backend
   cd Web/backend && python3 -m app.main
   
   # 测试 Tracker
   python3 Script/elect_tracker_db.py
   ```

## 故障排查

### 配置未生效
检查 `.env` 文件位置是否在项目根目录：
```bash
ls -la /root/pro/ECampusElectricity/.env
```

### 数据库连接失败
验证数据库配置：
```bash
python3 -c "from app.config import settings; print(settings.DATABASE_URL)"
```

### Bot 无法启动
同步配置到 config.yaml：
```bash
python3 scripts/sync_config.py
```

## 安全建议

1. ✅ **永远不要提交 `.env` 到 Git**（已在 .gitignore 中）
2. ✅ **生产环境使用强密钥**：`openssl rand -hex 32`
3. ✅ **定期轮换 SECRET_KEY**
4. ✅ **使用环境变量而非文件**（生产环境）
5. ✅ **限制 `.env` 文件权限**：`chmod 600 .env`
