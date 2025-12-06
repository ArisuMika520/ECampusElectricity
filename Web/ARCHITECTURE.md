# WebUI 架构设计

## 技术栈

### 前端
- **框架**: Next.js 14+ (App Router)
- **样式**: Tailwind CSS
- **组件库**: Shadcn/ui
- **图表**: Recharts 或 Chart.js
- **实时通信**: WebSocket (通过 Next.js API Routes)
- **状态管理**: Zustand (可选，如果状态复杂)

### 后端
- **框架**: FastAPI
- **ORM**: SQLModel (基于 SQLAlchemy)
- **数据库**: PostgreSQL
- **任务调度**: APScheduler (轻量级) 或 Celery (如果需要分布式)
- **日志**: Python logging + 文件轮转
- **WebSocket**: FastAPI WebSocket 支持
- **认证**: JWT (FastAPI 的 `python-jose`)

## 数据库设计

### 表结构

1. **subscriptions** (订阅表)
   - id: UUID (主键)
   - room_name: VARCHAR (房间名称，如 "D9东 425")
   - area_id: VARCHAR
   - building_code: VARCHAR
   - floor_code: VARCHAR
   - room_code: VARCHAR
   - threshold: FLOAT (告警阈值)
   - email_recipients: JSON (收件人列表)
   - is_active: BOOLEAN (是否启用)
   - created_at: TIMESTAMP
   - updated_at: TIMESTAMP

2. **electricity_history** (历史数据表)
   - id: UUID (主键)
   - subscription_id: UUID (外键 -> subscriptions.id)
   - surplus: FLOAT (电费余额)
   - timestamp: TIMESTAMP
   - created_at: TIMESTAMP
   - 索引: (subscription_id, timestamp)

3. **config** (配置表)
   - id: UUID (主键)
   - key: VARCHAR (唯一)
   - value: JSON
   - updated_at: TIMESTAMP

4. **logs** (日志表，可选)
   - id: UUID (主键)
   - level: VARCHAR (INFO, WARNING, ERROR)
   - message: TEXT
   - module: VARCHAR
   - timestamp: TIMESTAMP
   - 索引: (timestamp, level)

## API 设计

### RESTful API

- `GET /api/subscriptions` - 获取所有订阅
- `POST /api/subscriptions` - 创建订阅
- `GET /api/subscriptions/{id}` - 获取单个订阅
- `PUT /api/subscriptions/{id}` - 更新订阅
- `DELETE /api/subscriptions/{id}` - 删除订阅
- `GET /api/subscriptions/{id}/history` - 获取历史数据
- `GET /api/logs` - 获取日志（分页）
- `GET /api/config` - 获取配置
- `PUT /api/config` - 更新配置

### WebSocket

- `ws://localhost:8000/ws/logs` - 实时日志流
