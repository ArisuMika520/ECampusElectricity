"""管理员操作相关的 Pydantic 模式"""
from pydantic import BaseModel, EmailStr
from typing import Optional
import uuid


class UserCreate(BaseModel):
    """管理员创建用户模式"""
    username: str
    email: EmailStr
    password: str
    is_admin: bool = False
    is_active: bool = True


class UserUpdate(BaseModel):
    """管理员更新用户模式"""
    email: Optional[EmailStr] = None
    password: Optional[str] = None
    is_admin: Optional[bool] = None
    is_active: Optional[bool] = None


class SystemConfigUpdate(BaseModel):
    """系统配置更新模式"""
    allow_registration: bool


class UserResponse(BaseModel):
    """用户响应模式"""
    id: uuid.UUID
    username: str
    email: str
    is_active: bool
    is_admin: bool
    
    class Config:
        from_attributes = True



