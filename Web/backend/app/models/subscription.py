"""房间电费监控订阅模型"""
from sqlmodel import SQLModel, Field, Relationship, Column
from sqlalchemy import JSON
from datetime import datetime
from typing import Optional, List
import uuid


class Subscription(SQLModel, table=True):
    """房间电费监控订阅模型"""
    __tablename__ = "subscriptions"
    
    id: Optional[uuid.UUID] = Field(default_factory=uuid.uuid4, primary_key=True)
    # 保留首个创建者，告警等场景可使用
    user_id: uuid.UUID = Field(foreign_key="users.id", index=True)
    room_name: str = Field(max_length=100, index=True, unique=True)
    area_id: str = Field(max_length=50)
    building_code: str = Field(max_length=50)
    floor_code: str = Field(max_length=50)
    room_code: str = Field(max_length=50)
    threshold: float = Field(default=20.0, description="告警阈值（元）")
    email_recipients: List[str] = Field(
        default_factory=list,
        sa_column=Column(JSON)
    )
    is_active: bool = Field(default=True, index=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = None

