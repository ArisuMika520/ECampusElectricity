# 部署指南

## 生产环境部署

### 1. 服务器要求

- Ubuntu 20.04+ 或类似 Linux 发行版
- Python 3.10+
- Node.js 18+
- PostgreSQL 12+
- Nginx

### 2. 安装依赖

#### 系统依赖

```bash
sudo apt update
sudo apt install -y python3-pip python3-venv postgresql postgresql-contrib nginx
```

#### Python 依赖

```bash
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
pip install gunicorn
```

#### Node.js 依赖

```bash
cd frontend
npm install
npm run build
```

### 3. 配置 PostgreSQL

```bash
sudo -u postgres psql
```

```sql
CREATE DATABASE electricity_db;
CREATE USER electricity_user WITH PASSWORD 'your_password';
GRANT ALL PRIVILEGES ON DATABASE electricity_db TO electricity_user;
\q
```

### 4. 配置环境变量

创建 `backend/.env`:

```env
DATABASE_URL=postgresql://electricity_user:your_password@localhost:5432/electricity_db
SECRET_KEY=your-very-secure-secret-key-here
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
CORS_ORIGINS=["https://yourdomain.com"]
LOG_LEVEL=INFO
LOG_FILE=/var/log/electricity/app.log
```

### 5. 初始化数据库

```bash
cd backend
source venv/bin/activate
python -m app.main
```

### 6. 配置 Gunicorn

创建 `backend/gunicorn_config.py`:

```python
bind = "127.0.0.1:8000"
workers = 4
worker_class = "uvicorn.workers.UvicornWorker"
timeout = 120
keepalive = 5
```

### 7. 创建 Systemd 服务

创建 `/etc/systemd/system/electricity-backend.service`:

```ini
[Unit]
Description=Electricity Monitor Backend
After=network.target postgresql.service

[Service]
User=www-data
Group=www-data
WorkingDirectory=/path/to/mode1/backend
Environment="PATH=/path/to/mode1/backend/venv/bin"
ExecStart=/path/to/mode1/backend/venv/bin/gunicorn -c gunicorn_config.py app.main:app
Restart=always

[Install]
WantedBy=multi-user.target
```

启动服务:

```bash
sudo systemctl daemon-reload
sudo systemctl enable electricity-backend
sudo systemctl start electricity-backend
```

### 8. 配置 Nginx

创建 `/etc/nginx/sites-available/electricity`:

```nginx
server {
    listen 80;
    server_name yourdomain.com;

    # Frontend
    location / {
        root /path/to/mode1/frontend/out;
        try_files $uri $uri/ /index.html;
    }

    # Backend API
    location /api {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # WebSocket
    location /ws {
        proxy_pass http://127.0.0.1:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

启用配置:

```bash
sudo ln -s /etc/nginx/sites-available/electricity /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

### 9. 配置 HTTPS (可选但推荐)

使用 Let's Encrypt:

```bash
sudo apt install certbot python3-certbot-nginx
sudo certbot --nginx -d yourdomain.com
```

### 10. 日志管理

创建日志目录:

```bash
sudo mkdir -p /var/log/electricity
sudo chown www-data:www-data /var/log/electricity
```

配置日志轮转，创建 `/etc/logrotate.d/electricity`:

```
/var/log/electricity/*.log {
    daily
    missingok
    rotate 14
    compress
    delaycompress
    notifempty
    create 0640 www-data www-data
    sharedscripts
}
```

## Docker 部署

### 使用 Docker Compose

创建 `docker-compose.yml`:

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
    restart: always

  backend:
    build:
      context: ./backend
      dockerfile: Dockerfile
    environment:
      DATABASE_URL: postgresql://postgres:postgres@postgres:5432/electricity_db
      SECRET_KEY: ${SECRET_KEY}
    depends_on:
      - postgres
    restart: always

  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile
    environment:
      NEXT_PUBLIC_API_URL: http://backend:8000
    depends_on:
      - backend
    restart: always

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
    depends_on:
      - frontend
      - backend
    restart: always

volumes:
  postgres_data:
```

启动:

```bash
docker-compose up -d
```

## 监控和维护

### 查看日志

```bash
# 后端日志
sudo journalctl -u electricity-backend -f

# Nginx 日志
sudo tail -f /var/log/nginx/access.log
sudo tail -f /var/log/nginx/error.log
```

### 备份数据库

```bash
pg_dump -U electricity_user electricity_db > backup_$(date +%Y%m%d).sql
```

### 恢复数据库

```bash
psql -U electricity_user electricity_db < backup_20240101.sql
```

## 安全建议

1. 使用强密码
2. 定期更新依赖
3. 配置防火墙
4. 使用 HTTPS
5. 定期备份数据库
6. 监控系统日志
7. 限制 API 访问频率



