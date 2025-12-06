"""FastAPI 应用入口"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.database import init_db, engine
from sqlmodel import SQLModel

from app.models import user, subscription, history, config, log
from app.api import auth, subscriptions, history as history_api, config as config_api, logs, websocket, admin
from app.utils.scheduler import start_scheduler
from app.utils.logging import setup_logging

app = FastAPI(
    title="ECampus Electricity Monitor API",
    description="API for monitoring campus electricity usage",
    version="1.0.0"
)

setup_logging(settings.LOG_LEVEL, settings.LOG_FILE)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.get_cors_origins(),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
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
    """应用启动时初始化数据库和定时任务"""
    init_db()
    start_scheduler()


@app.on_event("shutdown")
async def shutdown_event():
    """应用关闭时清理资源"""
    from app.utils.scheduler import stop_scheduler
    stop_scheduler()


@app.get("/")
async def root():
    """根端点"""
    return {"message": "ECampus Electricity Monitor API", "version": "1.0.0"}


@app.get("/health")
async def health():
    """健康检查端点"""
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

