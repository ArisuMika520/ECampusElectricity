"""日志相关的 Pydantic 模式"""
from pydantic import BaseModel
from typing import Optional
from datetime import datetime
import uuid


class LogResponse(BaseModel):
    """日志响应模式"""
    id: uuid.UUID
    level: str
    message: str
    module: Optional[str] = None
    timestamp: datetime
    
    class Config:
        from_attributes = True



