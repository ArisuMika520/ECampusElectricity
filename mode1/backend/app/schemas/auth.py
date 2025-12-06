"""认证相关的 Pydantic 模式"""
from pydantic import BaseModel, EmailStr
from typing import Optional
import uuid


class UserRegister(BaseModel):
    """用户注册模式"""
    username: str
    email: EmailStr
    password: str


class UserLogin(BaseModel):
    """用户登录模式"""
    username: str
    password: str


class Token(BaseModel):
    """令牌响应模式"""
    access_token: str
    token_type: str = "bearer"


class UserResponse(BaseModel):
    """用户响应模式"""
    id: uuid.UUID
    username: str
    email: str
    is_active: bool
    is_admin: bool
    
    class Config:
        from_attributes = True

