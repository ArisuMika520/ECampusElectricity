# 脚本说明

## 统一脚本管理工具

`manage.sh` 是整合了所有快速操作的统一脚本管理工具。

## 使用方法

```bash
./scripts/manage.sh [命令] [选项]
```

## 可用命令

### 环境设置

```bash
./scripts/manage.sh setup
```

完整环境设置，包括：
- 检查系统依赖（Python、Node.js、npm）
- 设置后端环境（创建虚拟环境、安装依赖）
- 设置前端环境（安装依赖）
- 安装开发工具（concurrently）

### 启动服务

```bash
# 开发模式（前后端同时启动，支持热重载）
./scripts/manage.sh dev

# 生产模式（前后端同时启动）
./scripts/manage.sh start
```

### 数据库操作

```bash
# 初始化数据库（创建表结构）
./scripts/manage.sh db init

# 检查数据库状态
./scripts/manage.sh db check

# 数据库迁移（添加管理员字段等）
./scripts/manage.sh db migrate

# 从 Mode2 迁移数据
./scripts/manage.sh db migrate-mode2
```

### 清理环境

```bash
# 清理后端环境（删除虚拟环境）
./scripts/manage.sh clean backend

# 清理前端环境（删除 node_modules 和构建文件）
./scripts/manage.sh clean frontend

# 清理所有环境
./scripts/manage.sh clean all
```

### 帮助信息

```bash
./scripts/manage.sh help
```

## 其他脚本

### dev.sh
开发模式启动脚本（已整合到 manage.sh，保留用于兼容）

### start.sh
生产模式启动脚本（已整合到 manage.sh，保留用于兼容）

### setup.sh
完整环境设置脚本（已整合到 manage.sh，保留用于兼容）

## 推荐使用方式

**推荐使用统一脚本管理工具 `manage.sh`**，它提供了：
- 统一的命令接口
- 更好的错误处理
- 彩色输出和进度提示
- 自动环境检查
- 完整的帮助信息

## 示例

```bash
# 首次使用：完整设置
./scripts/manage.sh setup

# 配置环境变量
cp backend/.env.example backend/.env
# 编辑 backend/.env

# 初始化数据库
./scripts/manage.sh db init

# 启动开发模式
./scripts/manage.sh dev

# 检查数据库状态
./scripts/manage.sh db check

# 清理并重新设置
./scripts/manage.sh clean all
./scripts/manage.sh setup
```

