from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.database import init_db
from app.models import user, subscription, history, config, log, user_subscription
from app.api import auth, subscriptions, history as history_api, config as config_api, logs, websocket, admin
from app.utils.logging import setup_logging

app = FastAPI(
    title="ECampus Electricity Monitor API",
    description="API for monitoring campus electricity usage",
    version="1.0.0"
)

setup_logging(settings.LOG_LEVEL, settings.LOG_FILE)

# 获取 CORS 允许的源
cors_origins = settings.get_cors_origins()
print(f"[CORS] Allowed origins: {cors_origins}")

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
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
    init_db()


@app.get("/")
async def root():
    return {"message": "ECampus Electricity Monitor API", "version": "1.0.0"}


@app.get("/health")
async def health():
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

