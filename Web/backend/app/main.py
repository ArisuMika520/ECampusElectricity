from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.database import init_db
from app.models import user, subscription, history, config, log, user_subscription
from app.api import auth, subscriptions, history as history_api, config as config_api, logs, websocket, admin
from app.utils.logging import setup_logging
from app.utils.pm2_log_monitor import pm2_log_monitor

app = FastAPI(
    title="ECampus Electricity Monitor API",
    description="API for monitoring campus electricity usage",
    version="1.0.0"
)

setup_logging(settings.LOG_LEVEL, settings.LOG_FILE)

# 获取 CORS 允许的源
cors_origins = settings.get_cors_origins()
print(f"[CORS] Allowed origins: {cors_origins}")

# 配置 CORS 中间件 - 必须在所有路由之前添加
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH", "HEAD"],
    allow_headers=["*"],
    expose_headers=["*"],
    max_age=600,
)
app.include_router(auth.router, prefix="/api/auth", tags=["auth"])
app.include_router(subscriptions.router, prefix="/api/subscriptions", tags=["subscriptions"])
app.include_router(history_api.router, prefix="/api/history", tags=["history"])
app.include_router(config_api.router, prefix="/api/config", tags=["config"])
app.include_router(logs.router, prefix="/api/logs", tags=["logs"])
app.include_router(websocket.router, prefix="/ws", tags=["websocket"])
app.include_router(admin.router, prefix="/api/admin", tags=["admin"])


@app.on_event("startup")
async def startup_event():
    init_db()
    # 启动PM2日志监控器
    pm2_log_monitor.start()


@app.on_event("shutdown")
async def shutdown_event():
    # 停止PM2日志监控器
    pm2_log_monitor.stop()


@app.get("/")
async def root():
    return {"message": "ECampus Electricity Monitor API", "version": "1.0.0"}


@app.get("/health")
async def health():
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

