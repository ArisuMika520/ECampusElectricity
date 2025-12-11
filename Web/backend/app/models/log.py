"""应用日志存储模型"""
from sqlmodel import SQLModel, Field, Column
from sqlalchemy import Text
from datetime import datetime
from typing import Optional
import uuid
from app.utils.timezone import now_naive


class Log(SQLModel, table=True):
    """应用日志存储模型"""
    __tablename__ = "logs"
    
    id: Optional[uuid.UUID] = Field(default_factory=uuid.uuid4, primary_key=True)
    level: str = Field(max_length=20, index=True, description="日志级别：INFO, WARNING, ERROR, DEBUG")
    message: str = Field(sa_column=Column(Text))
    module: Optional[str] = Field(default=None, max_length=100, index=True)
    timestamp: datetime = Field(default_factory=now_naive, index=True)

