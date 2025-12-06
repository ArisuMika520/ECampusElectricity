"""系统配置存储模型"""
from sqlmodel import SQLModel, Field, Column
from sqlalchemy import JSON
from datetime import datetime
from typing import Optional, Any, Dict
import uuid
import json


class Config(SQLModel, table=True):
    """系统配置存储模型"""
    __tablename__ = "config"
    
    id: Optional[uuid.UUID] = Field(default_factory=uuid.uuid4, primary_key=True)
    user_id: Optional[uuid.UUID] = Field(default=None, foreign_key="users.id", index=True)
    key: str = Field(unique=True, index=True, max_length=100)
    value: Dict[str, Any] = Field(default_factory=dict, sa_column=Column(JSON))
    updated_at: datetime = Field(default_factory=datetime.utcnow)

