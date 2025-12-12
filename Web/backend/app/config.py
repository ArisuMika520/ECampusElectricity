"""应用配置管理"""
from pydantic_settings import BaseSettings
from typing import Optional, List, Union
import json
from pathlib import Path

# 统一配置：所有组件从项目根目录的 .env 文件读取配置
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent
ENV_FILE = PROJECT_ROOT / ".env"


class Settings(BaseSettings):
    """从环境变量加载的应用设置"""
    # 数据库配置
    DATABASE_URL: str = "postgresql://postgres:postgres@localhost:5432/electricity_db"
    
    # JWT 认证
    SECRET_KEY: str = "your-secret-key-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # CORS 配置
    CORS_ORIGINS: Union[str, List[str]] = [
        "http://localhost:4000", 
        "http://localhost:3001", 
        "http://127.0.0.1:4000"
    ]
    
    def get_cors_origins(self) -> List[str]:
        """解析 CORS_ORIGINS（支持 JSON 字符串或列表）"""
        if isinstance(self.CORS_ORIGINS, str):
            try:
                return json.loads(self.CORS_ORIGINS)
            except json.JSONDecodeError:
                return [origin.strip() for origin in self.CORS_ORIGINS.split(",")]
        return self.CORS_ORIGINS
    
    # 日志配置
    LOG_LEVEL: str = "INFO"
    LOG_FILE: str = "logs/app.log"
    
    # SMTP 邮件配置
    SMTP_SERVER: str = "smtp.qq.com"
    SMTP_PORT: int = 465
    SMTP_USER: Optional[str] = None
    SMTP_PASS: Optional[str] = None
    FROM_EMAIL: Optional[str] = None
    USE_TLS: bool = False
    
    # 易校园 API 配置
    SHIRO_JID: Optional[str] = None
    API_BASE_URL: str = "https://application.xiaofubao.com/app/electric"
    
    # QQ Bot 配置
    QQ_APPID: Optional[str] = None
    QQ_SECRET: Optional[str] = None
    
    # Tracker 配置
    TRACKER_CHECK_INTERVAL: int = 3600
    HISTORY_LIMIT: int = 2400
    
    # 图床配置
    UPLOADER_TOKEN: Optional[str] = None
    UPLOADER_ALBUM_ID: Optional[str] = None
    
    class Config:
        env_file = str(ENV_FILE)
        env_file_encoding = "utf-8"
        case_sensitive = True


settings = Settings()

