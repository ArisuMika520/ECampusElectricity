# PM2 部署指南

本文档介绍如何使用 PM2 管理 ECampusElectricity 项目的所有服务。

## 目录

- [安装 PM2](#安装-pm2)
- [前置准备](#前置准备)
- [配置文件说明](#配置文件说明)
- [基本使用](#基本使用)
- [服务管理](#服务管理)
- [日志管理](#日志管理)
- [监控和性能](#监控和性能)
- [开机自启](#开机自启)
- [故障排除](#故障排除)

## 安装 PM2

```bash
# 使用 npm 全局安装
npm install -g pm2

# 验证安装
pm2 --version
```

## 前置准备

### 1. 环境设置

确保已完成以下步骤：

```bash
# 1. 配置统一环境变量（项目根目录）
bash scripts/init-config.sh  # 交互式配置
# 或手动配置:
cp .env.example .env
nano .env  # 编辑配置，设置数据库连接、JWT密钥、SHIRO_JID等

# 2. Web 版本环境设置
cd Web
npm run setup

# 3. 初始化数据库
npm run db:init

# 4. 构建前端（生产模式需要）
cd frontend
npm run build
cd ../..
```

### 2. Bot 版本配置

```bash
# 安装 Bot 依赖
cd Bot
pip install -r requirements.txt

# 配置 Bot
cp config.yaml.example config.yaml
# 编辑 config.yaml，填入 QQ 机器人配置等
cd ..
```

### 3. 创建日志目录

```bash
mkdir -p logs/pm2
```

## 配置文件说明

项目根目录下的 `ecosystem.config.js` 是 PM2 的配置文件，包含四个服务：

1. **web-backend**: Web 后端（FastAPI）
2. **web-frontend**: Web 前端（Next.js）
3. **tracker**: 电费追踪器（数据库版本）
4. **bot**: QQ 机器人

每个服务都有独立的启动脚本（位于 `scripts/pm2-*.sh`），用于处理环境设置和依赖。

## 基本使用

### 快速启动（推荐）

使用快速启动脚本，会自动检查环境并启动所有服务：

```bash
# 从项目根目录执行
bash scripts/pm2-quick-start.sh
```

### 手动启动所有服务

```bash
# 从项目根目录执行
pm2 start ecosystem.config.js
```

### 启动单个服务

```bash
# 只启动后端
pm2 start ecosystem.config.js --only web-backend

# 只启动前端
pm2 start ecosystem.config.js --only web-frontend

# 只启动 Tracker
pm2 start ecosystem.config.js --only tracker

# 只启动 Bot
pm2 start ecosystem.config.js --only bot
```

### 停止服务

```bash
# 停止所有服务
pm2 stop all

# 停止单个服务
pm2 stop web-backend
pm2 stop web-frontend
pm2 stop tracker
pm2 stop bot
```

### 重启服务

```bash
# 重启所有服务
pm2 restart all

# 重启单个服务
pm2 restart web-backend
```

### 删除服务

```bash
# 删除所有服务
pm2 delete all

# 删除单个服务
pm2 delete web-backend
```

## 服务管理

### 查看服务状态

```bash
# 查看所有服务状态
pm2 status

# 查看详细信息
pm2 show web-backend
```

### 服务列表说明

- **name**: 服务名称
- **status**: 运行状态（online/stopped/errored）
- **cpu**: CPU 使用率
- **memory**: 内存使用量
- **uptime**: 运行时间
- **restarts**: 重启次数

### 重新加载配置

```bash
# 重新加载配置文件（不会中断服务）
pm2 reload ecosystem.config.js

# 或者重启所有服务
pm2 restart all
```

## 日志管理

### 查看日志

```bash
# 查看所有服务日志
pm2 logs

# 查看单个服务日志
pm2 logs web-backend
pm2 logs web-frontend
pm2 logs tracker
pm2 logs bot

# 查看最近 100 行日志
pm2 logs --lines 100

# 实时跟踪日志（类似 tail -f）
pm2 logs --lines 0
```

### 日志文件位置

所有日志文件保存在 `logs/pm2/` 目录：

```
logs/pm2/
├── web-backend.log          # 后端标准输出
├── web-backend-error.log    # 后端错误日志
├── web-backend-out.log      # 后端输出日志
├── web-frontend.log         # 前端标准输出
├── web-frontend-error.log   # 前端错误日志
├── web-frontend-out.log     # 前端输出日志
├── tracker.log              # Tracker 标准输出
├── tracker-error.log        # Tracker 错误日志
├── tracker-out.log          # Tracker 输出日志
├── bot.log                  # Bot 标准输出
├── bot-error.log           # Bot 错误日志
└── bot-out.log             # Bot 输出日志
```

### 清空日志

```bash
# 清空所有日志
pm2 flush

# 清空单个服务日志
pm2 flush web-backend
```

## 监控和性能

### 实时监控

```bash
# 打开监控面板（显示 CPU、内存使用情况）
pm2 monit
```

### 性能指标

```bash
# 查看性能指标
pm2 list

# 查看详细信息（包括内存、CPU）
pm2 show web-backend
```

### 内存限制

配置文件已设置内存限制：
- Web 后端/前端: 500MB
- Tracker/Bot: 300MB

超过限制会自动重启服务。

## 开机自启

### 保存当前进程列表

```bash
# 保存当前 PM2 进程列表
pm2 save
```

### 设置开机自启

```bash
# 生成启动脚本（根据系统提示选择）
pm2 startup

# 示例输出会显示类似以下命令，需要以 root 权限执行：
# sudo env PATH=$PATH:/usr/bin pm2 startup systemd -u arisu --hp /home/arisu
```

执行完上述命令后，PM2 会在系统启动时自动恢复之前保存的进程列表。

### 取消开机自启

```bash
# 取消开机自启
pm2 unstartup
```

## 故障排除

### 服务无法启动

1. **检查日志**:
   ```bash
   pm2 logs web-backend --lines 50
   ```

2. **检查环境**:
   ```bash
   # 检查虚拟环境是否存在
   ls -la Web/backend/venv/bin/python
   
   # 检查配置文件
   cat Web/backend/.env
   ```

3. **手动测试启动脚本**:
   ```bash
   bash scripts/pm2-start-backend.sh
   ```

### 服务频繁重启

1. **查看重启原因**:
   ```bash
   pm2 show web-backend
   ```

2. **检查内存使用**:
   ```bash
   pm2 monit
   ```

3. **查看错误日志**:
   ```bash
   pm2 logs web-backend --err
   ```

### 端口被占用

```bash
# 检查端口占用
lsof -i :8000  # 后端端口
lsof -i :3000  # 前端端口

# 杀死占用进程
kill -9 <PID>
```

### 数据库连接失败

1. **检查数据库服务**:
   ```bash
   sudo systemctl status postgresql
   ```

2. **检查环境变量**:
   ```bash
   cat Web/backend/.env | grep DATABASE_URL
   ```

3. **测试数据库连接**:
   ```bash
   cd Web/backend
   source venv/bin/activate
   python scripts/check_db.py
   ```

### 前端构建失败

```bash
# 清理并重新构建
cd Web/frontend
rm -rf .next node_modules
npm install
npm run build
```

## 常用命令速查

```bash
# 启动
pm2 start ecosystem.config.js

# 停止
pm2 stop all

# 重启
pm2 restart all

# 查看状态
pm2 status

# 查看日志
pm2 logs

# 监控
pm2 monit

# 保存配置
pm2 save

# 删除所有
pm2 delete all
```

## 注意事项

1. **首次启动前**:
   - 确保已完成环境设置（`npm run setup`）
   - 确保已配置环境变量（`backend/.env`）
   - 确保数据库已初始化（`npm run db:init`）
   - 确保前端已构建（`npm run build`）

2. **服务启动顺序**:
   - Web 后端应该先启动
   - Tracker 依赖 Web 后端，应该在后端启动后再启动
   - Web 前端和 Bot 可以独立启动

3. **配置文件修改**:
   - 修改 `ecosystem.config.js` 后需要重启服务
   - 修改环境变量（`.env`）后需要重启对应服务

4. **日志管理**:
   - 定期清理日志文件，避免占用过多磁盘空间
   - 使用 `pm2 flush` 清空日志

5. **生产环境**:
   - 建议使用 Nginx 作为反向代理
   - 配置 HTTPS
   - 设置防火墙规则
   - 定期备份数据库

## 参考资源

- [PM2 官方文档](https://pm2.keymetrics.io/docs/usage/quick-start/)
- [PM2 生态系统文件](https://pm2.keymetrics.io/docs/usage/application-declaration/)
- [PM2 日志管理](https://pm2.keymetrics.io/docs/usage/log-management/)

