## ECampusElectricity
<div align="center"> 
  <p><strong>对于采用易校园的大学寝室电费获取</strong></p> 
  <p>可查询电费，电费余额告警</p>
</div>

> **愿景**: 让大学生们及时得知电费情况，避免断电导致的不良影响

## 出现的缘由
闲来无事，周末寝室玩游戏，但是电费不足停电了，气死我了！
遂写了一个电费自动告警程序

## 已实现功能
* [x] 通过易校园抓取寝室电费
* [x] 设置电费阈值与邮箱告警
* [x] 接入QQ机器人，在QQ就可以随时查询电费
* [x] 实现电费消耗预测
* [x] 历史电费数据分析
* [x] 电费消耗/余额图形化
* [x] 实现数据库偏移缓存命中自动更新、异常处理
* [x] WebUI 图形化界面（FastAPI + Next.js）
* [x] PostgreSQL 数据库存储
* [x] 实时日志监控（WebSocket）

## 项目模式

本项目提供两种实现方式，**请根据您的需求选择**：

### Web 版本（推荐）
- **位置**: `Web/` 目录
- **技术栈**: FastAPI + Next.js + PostgreSQL
- **特点**: 
  - 现代化的 WebUI 界面
  - 多用户认证系统
  - 实时日志监控
  - 历史数据可视化
  - 管理员面板
  - 数据库存储（PostgreSQL）
- **适用场景**: 需要 Web 界面管理、多用户使用、需要数据持久化

### Bot 版本
- **位置**: `Bot/` 目录
- **技术栈**: Python + QQ 机器人 API
- **特点**:
  - QQ 机器人交互
  - 通过 QQ 查询电费
  - 电费消耗预测
  - 图形化展示
  - JSON 文件存储
- **适用场景**: 喜欢 QQ 机器人交互、简单部署、个人使用

## 快速开始

### 前置要求

#### Web 版本
- **Python**: 3.10 或更高版本
- **Node.js**: 18 或更高版本
- **PostgreSQL**: 12 或更高版本
- **npm**: 随 Node.js 一起安装

#### Bot 版本
- **Python**: 3.10 或更高版本
- **pip**: Python 包管理器

### 抓取 shiroJID

**重要**: 在使用本项目之前，您需要获取易校园的认证信息。

1. **Android 设备**:
   - 安装 ***易校园*** 和 ***HttpCanary***
   - 登录易校园后开启抓包
   - 在易校园中点击电费查询等功能
   - 在抓到的包中找到参数：**shiroJID**（在 cookie 里）

2. **iOS 设备**:
   - 安装 ***易校园*** 和 ***Stream***
   - 按照上述步骤进行抓包

3. **将 shiroJID 填入配置**:
   - Web 版本：在 WebUI 的"设置"页面配置，或填入 `backend/.env` 文件
   - Bot 版本：填入 `Bot/config.yaml` 文件

### Web 版本快速开始

#### 方式一：一键设置（推荐）

```bash
# 1. 进入 Web 目录
cd Web

# 2. 一键设置环境（自动安装所有依赖）
npm run setup

# 3. 配置环境变量
cp backend/.env.example backend/.env
# 编辑 backend/.env，设置以下关键配置：
#   - DATABASE_URL: PostgreSQL 数据库连接字符串
#   - SECRET_KEY: JWT 密钥（随机字符串）
#   - SHIRO_JID: 从易校园抓取的 shiroJID

# 4. 初始化数据库
npm run db:init

# 5. 启动开发模式
npm run dev
```

#### 方式二：使用脚本管理工具

```bash
cd Web

# 完整环境设置
./scripts/manage.sh setup

# 启动开发模式
./scripts/manage.sh dev

# 启动生产模式
./scripts/manage.sh start
```

启动后访问：
- **前端**: http://localhost:3000
- **后端 API**: http://localhost:8000
- **API 文档**: http://localhost:8000/docs

详细文档请查看 [Web/README.md](Web/README.md)

### Bot 版本快速开始

```bash
# 1. 进入 Bot 目录
cd Bot

# 2. 安装依赖
pip install -r requirements.txt

# 3. 配置 config.yaml
cp config.yaml.example config.yaml
# 编辑 config.yaml，填入以下配置：
#   - electricity.shiroJID: 从易校园抓取的 shiroJID
#   - qq.appid: QQ 机器人 AppID
#   - qq.secret: QQ 机器人 Secret
#   - uploader.token: 图床 API Token（可选）
#   - uploader.album_id: 图床相册 ID（可选）

# 4. 运行机器人
python src/bot/Elect_bot.py
```

**注意**: Bot 版本需要根据个人具体情况进行部分重构（例如图床API、appid等）

## 项目结构

```
ECampusElectricity/
├── Web/                    # WebUI 版本（FastAPI + Next.js）
│   ├── backend/            # FastAPI 后端
│   │   ├── app/            # 应用主目录
│   │   │   ├── api/       # API 路由
│   │   │   ├── core/      # 核心功能（电费查询）
│   │   │   ├── models/    # 数据库模型
│   │   │   ├── schemas/   # Pydantic 模式
│   │   │   ├── services/  # 业务逻辑
│   │   │   └── utils/     # 工具函数
│   │   ├── scripts/       # 数据库脚本
│   │   ├── requirements.txt  # Python 依赖
│   │   └── setup.sh       # 后端环境设置脚本
│   ├── frontend/           # Next.js 前端
│   │   ├── app/           # Next.js App Router
│   │   ├── components/    # React 组件
│   │   └── package.json   # 前端依赖
│   ├── scripts/            # 启动脚本
│   │   ├── manage.sh      # 统一脚本管理工具
│   │   ├── dev.sh         # 开发模式启动
│   │   └── start.sh       # 生产模式启动
│   └── package.json       # 统一 npm 脚本管理
├── Bot/                    # QQ 机器人版本
│   ├── src/
│   │   ├── bot/           # Bot 相关模块
│   │   ├── core/          # 核心逻辑模块
│   │   ├── data/          # 数据模块
│   │   └── utils/         # 工具函数模块
│   ├── scripts/           # 独立脚本目录
│   ├── data_files/        # 存放数据（JSON）
│   ├── assets/            # 存放静态资源
│   ├── requirements.txt   # Python 依赖
│   └── config.yaml.example  # 配置文件示例
├── Script/                 # 工具脚本
│   └── elect_tracker_db.py  # 数据库版本追踪器
├── scripts/                # PM2 启动脚本
│   ├── pm2-start-backend.sh   # 后端启动脚本
│   ├── pm2-start-frontend.sh  # 前端启动脚本
│   ├── pm2-start-tracker.sh   # Tracker 启动脚本
│   └── pm2-start-bot.sh       # Bot 启动脚本
├── ecosystem.config.js     # PM2 配置文件
├── PM2_DEPLOYMENT.md       # PM2 部署文档
├── example/                # 示例文件
├── README.md               # 本文件
└── LICENSE                 # 许可证
```

## 详细文档

- **Web 版本**: 查看 [Web/README.md](Web/README.md) - 包含完整的部署和使用说明
- **Bot 版本**: 查看 `Bot/` 目录下的配置文件示例和代码注释

## 开发与部署

### Web 版本开发

```bash
cd Web

# 开发模式（支持热重载）
npm run dev
# 或
./scripts/manage.sh dev

# 生产模式（需要先构建前端）
npm run build          # 构建前端
npm run start          # 启动生产模式
# 或
./scripts/manage.sh start
```

### PM2 部署（推荐）

使用 PM2 可以统一管理所有服务（Web 后端、Web 前端、Tracker、Bot），支持自动重启、日志管理、监控等功能。

#### 安装 PM2

```bash
npm install -g pm2
```

#### 前置准备

```bash
# 1. 完成环境设置
cd Web
npm run setup
npm run db:init

# 2. 构建前端
cd frontend
npm run build
cd ../..

# 3. 配置环境变量
cp Web/backend/.env.example Web/backend/.env
# 编辑 Web/backend/.env

# 4. 配置 Bot（如需要）
cp Bot/config.yaml.example Bot/config.yaml
# 编辑 Bot/config.yaml
```

#### 启动服务

```bash
# 启动所有服务
pm2 start ecosystem.config.js

# 启动单个服务
pm2 start ecosystem.config.js --only web-backend
pm2 start ecosystem.config.js --only web-frontend
pm2 start ecosystem.config.js --only tracker
pm2 start ecosystem.config.js --only bot
```

#### 常用命令

```bash
# 查看状态
pm2 status

# 查看日志
pm2 logs

# 停止服务
pm2 stop all

# 重启服务
pm2 restart all

# 监控面板
pm2 monit

# 保存配置（用于开机自启）
pm2 save
pm2 startup
```

**详细文档**: 查看 [PM2_DEPLOYMENT.md](PM2_DEPLOYMENT.md)

### Web 版本生产部署（传统方式）

1. **构建前端**:
   ```bash
   cd Web/frontend
   npm run build
   ```

2. **配置环境变量**: 确保 `backend/.env` 中的生产环境配置正确

3. **启动服务**: 使用生产模式启动脚本或配置进程管理器（如 systemd、supervisor）

4. **反向代理**: 建议使用 Nginx 作为反向代理，配置 HTTPS

### Bot 版本部署

```bash
cd Bot

# 安装依赖
pip install -r requirements.txt

# 配置 config.yaml
cp config.yaml.example config.yaml
# 编辑配置文件

# 运行机器人（建议使用进程管理器）
python src/bot/Elect_bot.py
```

### 数据库追踪器（Script/elect_tracker_db.py）

该脚本用于从数据库读取订阅并定期查询电费，适用于 Web 版本：

```bash
# 确保已安装 Web 版本的依赖
cd Script
python elect_tracker_db.py
```

## 重要提示

1. **shiroJID 有效期**: shiroJID 可能会过期，如果查询失败，请重新抓取
2. **数据库配置**: Web 版本需要正确配置 PostgreSQL 数据库连接
3. **Bot 版本自定义**: Bot 版本需要根据个人情况配置图床 API、QQ 机器人等
4. **buildingData**: 本项目的 buildingData 数据只适用于特定学校，如需修改，请通过遍历抓取字典中的所有楼寝室与对应的索引
5. **iOS 抓包**: 如果你是 iOS + 小程序抓不到相关数据，目前已找到解决方法，正在编写教程中

## 依赖说明

### Web 版本依赖

**后端 Python 依赖** (`Web/backend/requirements.txt`):
- `fastapi` - Web 框架
- `uvicorn[standard]` - ASGI 服务器
- `sqlmodel` - ORM（基于 SQLAlchemy）
- `psycopg2-binary` - PostgreSQL 驱动
- `pydantic` - 数据验证
- `python-jose[cryptography]` - JWT 认证
- `passlib[bcrypt]` - 密码加密
- `requests` - HTTP 请求
- `websockets` - WebSocket 支持
- `alembic` - 数据库迁移工具

**前端 Node.js 依赖** (`Web/frontend/package.json`):
- `next` - Next.js 框架
- `react` / `react-dom` - React 库
- `tailwindcss` - CSS 框架
- `recharts` - 图表库
- `axios` - HTTP 客户端
- `@radix-ui/*` - UI 组件库
- `framer-motion` - 动画库

### Bot 版本依赖

**Python 依赖** (`Bot/requirements.txt`):
- `botpy` - QQ 机器人框架
- `requests` - HTTP 请求
- `numpy` - 数值计算
- `scipy` - 科学计算
- `matplotlib` - 数据可视化
- `seaborn` - 统计图表
- `pyyaml` - YAML 配置文件解析

## 一键启动命令

### Web 版本

#### 开发模式（Development）

```bash
cd Web

# 方式一：使用 npm 脚本（推荐）
npm run dev

# 方式二：使用脚本管理工具
./scripts/manage.sh dev

# 方式三：使用独立脚本
bash scripts/dev.sh
```

**特点**:
- 前后端同时启动
- 支持热重载（代码修改自动重启）
- 日志输出到控制台和日志文件
- 前端运行在 http://localhost:3000
- 后端运行在 http://localhost:8000

#### 生产模式（Production）

```bash
cd Web

# 1. 构建前端（首次运行或前端代码更新后）
npm run build

# 2. 启动生产模式
# 方式一：使用 npm 脚本
npm run start

# 方式二：使用脚本管理工具
./scripts/manage.sh start

# 方式三：使用独立脚本
bash scripts/start.sh
```

**特点**:
- 前端已构建为静态文件
- 后端以生产模式运行
- 性能优化，适合部署

### Bot 版本

```bash
cd Bot

# 安装依赖（首次运行）
pip install -r requirements.txt

# 运行机器人
python src/bot/Elect_bot.py
```

## 许可证

本项目采用 MIT 许可证 - 详情请参阅 [LICENSE](LICENSE) 文件

## 联系我们

- **GitHub Issues**: [提交问题或建议](https://github.com/ArisuMika520/ECampusElectricity/issues)

---

<div align="center">
  <p>⭐️ 如果你喜欢这个项目，别忘了给它一个星！ ⭐️</p>
</div>

---

## 注意事项

### 通用注意事项

1. **shiroJID 有效期**: shiroJID 可能会过期，如果查询失败，请重新抓取
2. **buildingData 数据**: 本项目的 buildingData 数据只适用于特定学校，如需修改，请通过遍历抓取字典中的所有楼寝室与对应的索引
3. **Bot 版本自定义**: Bot 版本需要根据个人情况配置图床 API、QQ 机器人等

### Web 版本注意事项

1. **数据库配置**: 确保 PostgreSQL 已正确安装并运行
2. **环境变量**: 首次运行前必须配置 `backend/.env` 文件
3. **数据库初始化**: 首次运行前必须执行 `npm run db:init` 初始化数据库
4. **端口占用**: 确保 3000（前端）和 8000（后端）端口未被占用

### Bot 版本注意事项

1. **配置文件**: 必须正确配置 `config.yaml` 文件
2. **QQ 机器人**: 需要有效的 QQ 机器人 AppID 和 Secret
3. **图床配置**: 图床 API 为可选配置，用于图片上传功能
4. **代码调整**: 根据具体寝室结构调整相关代码

## 参考资源

- **示例代码**: 参照 [Example](https://github.com/ArisuMika520/ECampusElectricity/tree/main/example)
- **Web 版本详细文档**: [Web/README.md](Web/README.md)
- **PM2 部署指南**: [PM2_DEPLOYMENT.md](PM2_DEPLOYMENT.md)
- **项目架构说明**: [Web/ARCHITECTURE.md](Web/ARCHITECTURE.md)（如果存在）

## 贡献指南

欢迎提交 Issue 和 Pull Request！

1. Fork 本项目
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 开启 Pull Request 
