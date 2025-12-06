"""订阅相关的 Pydantic 模式"""
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
import uuid


class SubscriptionBase(BaseModel):
    """订阅基础模式"""
    room_name: str
    area_id: str
    building_code: str
    floor_code: str
    room_code: str
    threshold: float = 20.0
    email_recipients: List[str] = []
    is_active: bool = True


class SubscriptionCreate(SubscriptionBase):
    """订阅创建模式"""
    pass


class SubscriptionUpdate(BaseModel):
    """订阅更新模式"""
    room_name: Optional[str] = None
    area_id: Optional[str] = None
    building_code: Optional[str] = None
    floor_code: Optional[str] = None
    room_code: Optional[str] = None
    threshold: Optional[float] = None
    email_recipients: Optional[List[str]] = None
    is_active: Optional[bool] = None


class SubscriptionResponse(SubscriptionBase):
    """订阅响应模式"""
    id: uuid.UUID
    user_id: uuid.UUID
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True



