# 后端环境设置指南

## 前置要求

在开始之前，需要安装以下系统包：

```bash
sudo apt update
sudo apt install python3-venv python3-pip
```

## 快速设置

### 1. 安装系统依赖（如果尚未安装）

```bash
sudo apt install python3-venv python3-pip
```

### 2. 运行设置脚本

```bash
cd backend
bash setup.sh
```

### 3. 激活虚拟环境

```bash
source venv/bin/activate
```

### 4. 运行后端

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

## 手动设置步骤

如果自动脚本失败，可以手动执行：

### 1. 创建虚拟环境

```bash
cd backend
python3 -m venv venv
```

### 2. 激活虚拟环境

```bash
source venv/bin/activate
```

### 3. 升级 pip

```bash
python -m pip install --upgrade pip
```

### 4. 安装依赖

```bash
pip install -r requirements.txt
```

### 5. 配置环境变量

```bash
cp .env.example .env
# 编辑 .env 文件，设置数据库连接等信息
```

### 6. 初始化数据库

```bash
# 确保数据库已创建
sudo -u postgres psql -c "CREATE DATABASE electricity_db;"

# 初始化表结构
sudo -u postgres psql -d electricity_db -f scripts/init.sql
```

### 7. 运行应用

```bash
uvicorn app.main:app --reload
```

## 常见问题

### 问题1: `python3-venv` 未安装

**错误信息:**
```
The virtual environment was not created successfully because ensurepip is not available.
```

**解决方法:**
```bash
sudo apt install python3-venv python3-pip
```

### 问题2: `uvicorn` 命令未找到

**原因:** 未激活虚拟环境或未安装依赖

**解决方法:**
```bash
source venv/bin/activate
pip install -r requirements.txt
```

### 问题3: 数据库连接失败

**检查:**
1. PostgreSQL 服务是否运行: `sudo systemctl status postgresql`
2. 数据库是否已创建: `sudo -u postgres psql -l | grep electricity_db`
3. `.env` 文件中的 `DATABASE_URL` 是否正确

## 验证安装

运行以下命令验证环境是否正确设置：

```bash
# 检查 Python 版本
python --version

# 检查虚拟环境是否激活（应该显示 venv 路径）
which python

# 检查依赖是否安装
pip list | grep -E "fastapi|uvicorn|sqlmodel"
```

## 开发模式运行

开发时使用：

```bash
source venv/bin/activate
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

这将：
- 启用自动重载（代码修改后自动重启）
- 监听所有网络接口（0.0.0.0）
- 使用端口 8000

访问 API 文档: http://localhost:8000/docs



