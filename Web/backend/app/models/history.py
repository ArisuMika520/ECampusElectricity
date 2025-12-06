"""电费历史数据存储模型"""
from sqlmodel import SQLModel, Field, Relationship
from datetime import datetime
from typing import Optional
import uuid


class ElectricityHistory(SQLModel, table=True):
    """电费历史数据存储模型"""
    __tablename__ = "electricity_history"
    
    id: Optional[uuid.UUID] = Field(default_factory=uuid.uuid4, primary_key=True)
    subscription_id: uuid.UUID = Field(foreign_key="subscriptions.id", index=True)
    surplus: float = Field(description="电费余额（元）")
    timestamp: datetime = Field(default_factory=datetime.utcnow, index=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)



