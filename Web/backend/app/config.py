"""应用配置管理"""
from pydantic_settings import BaseSettings
from typing import Optional, List, Union
import json


class Settings(BaseSettings):
    """从环境变量加载的应用设置"""
    DATABASE_URL: str = "postgresql://postgres:postgres@localhost:5432/electricity_db"
    
    # JWT
    SECRET_KEY: str = "your-secret-key-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    CORS_ORIGINS: Union[str, List[str]] = ["http://localhost:3000", "http://localhost:3001"]
    
    def get_cors_origins(self) -> List[str]:
        """解析 CORS_ORIGINS（支持 JSON 字符串或列表）"""
        if isinstance(self.CORS_ORIGINS, str):
            try:
                return json.loads(self.CORS_ORIGINS)
            except json.JSONDecodeError:
                return [origin.strip() for origin in self.CORS_ORIGINS.split(",")]
        return self.CORS_ORIGINS
    LOG_LEVEL: str = "INFO"
    LOG_FILE: str = "logs/app.log"
    SMTP_SERVER: str = "smtp.qq.com"
    SMTP_PORT: int = 465
    SMTP_USER: Optional[str] = None
    SMTP_PASS: Optional[str] = None
    FROM_EMAIL: Optional[str] = None
    USE_TLS: bool = False
    SHIRO_JID: Optional[str] = None
    API_BASE_URL: str = "https://application.xiaofubao.com/app/electric"
    
    HISTORY_LIMIT: int = 2400
    
    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()

