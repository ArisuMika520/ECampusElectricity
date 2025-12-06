# Web 版本 - 电费监控系统

基于 FastAPI + Next.js 的校园电费监控和管理系统，支持多用户、实时日志监控、历史数据可视化和邮件告警。

## 技术栈

### 后端
- FastAPI - Python Web 框架
- SQLModel - ORM（基于 SQLAlchemy）
- PostgreSQL - 关系型数据库
- APScheduler - 任务调度
- JWT - 用户认证
- bcrypt - 密码加密

### 前端
- Next.js 14+ (App Router)
- Tailwind CSS - 样式框架
- Shadcn/ui - UI 组件库
- Recharts - 图表库
- WebSocket - 实时通信

## 项目结构

```
Web/
├── package.json          # 统一 npm 脚本管理
├── scripts/              # 启动脚本
│   ├── dev.sh           # 开发模式启动
│   ├── start.sh         # 生产模式启动
│   └── setup.sh         # 环境设置
├── backend/              # FastAPI 后端
│   ├── app/
│   │   ├── api/         # API 路由
│   │   ├── core/        # 核心功能（电费查询）
│   │   ├── models/      # 数据库模型
│   │   ├── schemas/     # Pydantic 模式
│   │   ├── services/    # 业务逻辑
│   │   └── utils/       # 工具函数
│   ├── scripts/         # 数据库脚本
│   └── requirements.txt
├── frontend/             # Next.js 前端
│   ├── app/             # Next.js App Router
│   ├── components/      # React 组件
│   └── lib/             # 工具库
└── README.md
```

## 快速开始

### 前置要求

- Python 3.10+
- Node.js 18+
- PostgreSQL 12+
- npm

### 重要提示

**所有命令都需要在 `Web` 目录下执行！**

```bash
cd Web  # 先进入 Web 目录
```

### 一键设置（推荐）

```bash
# 1. 进入 Web 目录
cd Web

# 2. 一键设置环境（安装所有依赖）
npm run setup

# 3. 配置环境变量
cp backend/.env.example backend/.env
# 编辑 backend/.env 文件，设置数据库连接等配置

# 4. 初始化数据库
npm run db:init

# 5. 启动开发模式（同时启动前后端）
npm run dev
```

### 分步设置

#### 1. 安装依赖

```bash
# 安装所有依赖
npm run install:all

# 或分别安装
npm run install:backend   # 后端 Python 依赖
npm run install:frontend  # 前端 Node.js 依赖
```

#### 2. 配置环境变量

复制并编辑 `backend/.env`：

```env
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/electricity_db
SECRET_KEY=your-secret-key-here
CORS_ORIGINS=["http://localhost:3000","http://localhost:3001"]
SHIRO_JID=your-shiro-jid-here
```

#### 3. 初始化数据库

```bash
# 方法1: 使用 npm 脚本（推荐）
npm run db:init

# 方法2: 使用 SQL 脚本
sudo -u postgres psql -d electricity_db -f backend/scripts/init.sql

# 检查数据库状态
npm run db:check
```

## 命令行操作

### 统一脚本管理工具（推荐）

我们提供了一个统一的脚本管理工具 `scripts/manage.sh`，整合了所有常用操作：

```bash
# 显示帮助信息
./scripts/manage.sh help

# 完整环境设置
./scripts/manage.sh setup

# 启动开发模式（前后端同时启动）
./scripts/manage.sh dev

# 启动生产模式
./scripts/manage.sh start

# 数据库操作
./scripts/manage.sh db init          # 初始化数据库
./scripts/manage.sh db check         # 检查数据库状态
./scripts/manage.sh db migrate       # 数据库迁移
./scripts/manage.sh db migrate-mode2 # 从 Bot 版本迁移数据

# 清理环境
./scripts/manage.sh clean backend   # 清理后端环境
./scripts/manage.sh clean frontend  # 清理前端环境
./scripts/manage.sh clean all       # 清理所有环境
```

### 使用 npm 脚本（便捷方式）

所有 npm 脚本都已整合到统一管理工具：

```bash
# 开发模式
npm run dev              # 同时启动前后端（开发模式，支持热重载）
npm run dev:backend      # 只启动后端
npm run dev:frontend     # 只启动前端

# 生产模式
npm run build            # 构建前端
npm run start            # 同时启动前后端（生产模式）
npm run start:backend    # 只启动后端
npm run start:frontend   # 只启动前端

# 环境设置
npm run setup            # 一键设置所有环境
npm run install:all      # 安装所有依赖（等同于 setup）
npm run install:backend  # 安装后端依赖
npm run install:frontend # 安装前端依赖

# 数据库操作
npm run db:init          # 初始化数据库（创建表结构）
npm run db:migrate       # 数据库迁移（添加字段等）
npm run db:check         # 检查数据库状态
npm run db:migrate-mode2 # 从 Bot 版本迁移数据

# 清理操作
npm run clean            # 清理所有环境
npm run clean:backend    # 清理后端环境
npm run clean:frontend   # 清理前端环境
```

## 访问地址

启动后访问：
- **前端**: http://localhost:3000
- **后端 API**: http://localhost:8000
- **API 文档**: http://localhost:8000/docs

## 使用说明

### 1. 首次登录

- 访问 http://localhost:3000/login
- 输入任意用户名和密码
- 系统会自动创建管理员账号并登录
- 首次登录的用户自动获得管理员权限

### 2. 管理员功能

登录后，管理员可以：
- 进入"管理员"面板（导航栏可见）
- 创建新用户账号
- 开启/关闭用户注册功能
- 管理所有用户（启用/停用）

### 3. 配置系统

进入"设置"页面配置：
- **ShiroJID**: 从易校园小程序抓取的认证 token
- **SMTP 配置**: 用于发送告警邮件

### 4. 添加订阅

进入"订阅管理"页面：
- 点击"添加订阅"
- 填写房间信息（校区ID、楼栋代码、楼层代码、房间代码）
- 设置告警阈值
- 配置收件人邮箱

### 5. 查看历史数据

在"订阅管理"页面，点击"查看历史"可以查看电费余额趋势图。

### 6. 监控日志

进入"日志监控"页面，可以实时查看系统运行日志。

## API 文档

启动后端后，访问 `http://localhost:8000/docs` 查看自动生成的交互式 API 文档。

### 主要 API 端点

**认证 API**:
- `POST /api/auth/login` - 用户登录（首次登录自动创建管理员）
- `POST /api/auth/register` - 用户注册（需要管理员开启）
- `GET /api/auth/me` - 获取当前用户信息

**订阅管理**:
- `GET /api/subscriptions` - 获取订阅列表
- `POST /api/subscriptions` - 创建订阅
- `GET /api/subscriptions/{id}` - 获取单个订阅
- `PUT /api/subscriptions/{id}` - 更新订阅
- `DELETE /api/subscriptions/{id}` - 删除订阅
- `POST /api/subscriptions/{id}/test` - 测试查询电费

**历史数据**:
- `GET /api/history/subscriptions/{id}` - 获取订阅历史数据
- `GET /api/history/stats/{id}` - 获取统计数据

**管理员 API**（需要管理员权限）:
- `GET /api/admin/users` - 获取所有用户
- `POST /api/admin/users` - 创建用户
- `PUT /api/admin/users/{id}` - 更新用户
- `DELETE /api/admin/users/{id}` - 删除用户
- `GET /api/admin/system/config` - 获取系统配置
- `PUT /api/admin/system/config` - 更新系统配置（开关注册）

**其他**:
- `GET /api/logs` - 获取日志
- `WS /ws/logs` - WebSocket 实时日志流

## 数据迁移

### 从 Bot 版本迁移数据

```bash
cd backend
source venv/bin/activate
python scripts/migrate_from_mode2.py
```

**前提条件**: 确保 `Bot/data_files/` 目录存在且包含 `sub.json` 和 `his.json` 文件。

这将：
1. 创建默认用户（用户名: `migrated_user`, 密码: `changeme`）
2. 从 `Bot/data_files/sub.json` 导入订阅数据
3. 从 `Bot/data_files/his.json` 导入历史数据

**注意**: 迁移后请立即修改默认用户密码！

## 定时任务

系统会自动定时查询所有活跃订阅的电费：
- 默认间隔：3600 秒（1小时）
- 可在 `backend/.env` 中配置 `TRACKER_CHECK_INTERVAL`

当电费余额低于阈值时，系统会自动发送告警邮件。

## 环境变量配置

### 后端环境变量 (backend/.env)

```env
# 数据库
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/electricity_db

# JWT 认证
SECRET_KEY=your-secret-key-here
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# CORS
CORS_ORIGINS=["http://localhost:3000","http://localhost:3001"]

# 日志
LOG_LEVEL=INFO
LOG_FILE=logs/app.log

# SMTP（可选，也可通过 WebUI 配置）
SMTP_SERVER=smtp.qq.com
SMTP_PORT=465
SMTP_USER=your-email@qq.com
SMTP_PASS=your-email-password
FROM_EMAIL=your-email@qq.com
USE_TLS=false

# 易校园 API
SHIRO_JID=your-shiro-jid-here

# 定时任务
TRACKER_CHECK_INTERVAL=3600
HISTORY_LIMIT=2400
```

### 前端环境变量 (frontend/.env.local)

```env
NEXT_PUBLIC_API_URL=http://localhost:8000
```

## 故障排除

### 端口被占用

```bash
# 检查端口占用
lsof -i :8000  # 后端端口
lsof -i :3000  # 前端端口

# 杀死进程
kill -9 <PID>
```

### 数据库连接失败

```bash
# 检查数据库状态
npm run db:check

# 检查 PostgreSQL 服务
sudo systemctl status postgresql

# 验证数据库连接配置
cat backend/.env | grep DATABASE_URL
```

### 登录失败

1. 检查数据库是否已初始化：`npm run db:check`
2. 检查后端日志中的错误信息
3. 确认数据库表结构正确（特别是 `is_admin` 字段）

### 电费查询失败

- 检查 `shiroJID` 是否有效（可能已过期）
- 查看后端日志了解详细错误信息
- 在"设置"页面重新配置 `shiroJID`

### 邮件发送失败

- 检查 SMTP 配置是否正确
- 确认邮箱授权码有效
- 检查防火墙设置
- 在"设置"页面测试 SMTP 配置

### 依赖问题

```bash
# 重新安装后端依赖
cd backend
rm -rf venv
bash setup.sh

# 重新安装前端依赖
cd frontend
rm -rf node_modules
npm install
```

## 部署

详细部署指南请参考 `backend/DEPLOYMENT.md`。

### 快速部署（Docker Compose）

```yaml
version: '3.8'

services:
  postgres:
    image: postgres:15
    environment:
      POSTGRES_DB: electricity_db
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: postgres
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"

volumes:
  postgres_data:
```

### 生产环境建议

1. 使用 Nginx 反向代理
2. 前端构建为静态文件：`npm run build`
3. 后端使用 Gunicorn + Uvicorn workers
4. 配置 HTTPS
5. 使用环境变量管理敏感配置

## 开发

### 后端开发

```bash
npm run dev:backend
# 或
cd backend && source venv/bin/activate && uvicorn app.main:app --reload
```

### 前端开发

```bash
npm run dev:frontend
# 或
cd frontend && npm run dev
```

## 许可证

MIT License

## 贡献

欢迎提交 Issue 和 Pull Request！
