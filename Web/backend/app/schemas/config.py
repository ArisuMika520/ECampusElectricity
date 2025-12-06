"""配置相关的 Pydantic 模式"""
from pydantic import BaseModel
from typing import Optional, Any, Dict
from datetime import datetime
import uuid


class ConfigResponse(BaseModel):
    """配置响应模式"""
    id: uuid.UUID
    user_id: Optional[uuid.UUID]
    key: str
    value: Dict[str, Any]
    updated_at: datetime
    
    class Config:
        from_attributes = True


class ConfigUpdate(BaseModel):
    """配置更新模式"""
    value: Dict[str, Any]



