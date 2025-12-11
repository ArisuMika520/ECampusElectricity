"""用户与订阅的关联表（多对一共享订阅）"""
from sqlmodel import SQLModel, Field
import uuid
from datetime import datetime
from typing import Optional


class UserSubscription(SQLModel, table=True):
    """用户订阅关联：一个房间订阅可被多用户共享访问"""
    __tablename__ = "user_subscriptions"

    id: Optional[uuid.UUID] = Field(default_factory=uuid.uuid4, primary_key=True)
    user_id: uuid.UUID = Field(foreign_key="users.id", index=True)
    subscription_id: uuid.UUID = Field(foreign_key="subscriptions.id", index=True)
    is_owner: bool = Field(default=False, description="是否为首个创建该订阅的用户")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = None

    class Config:
        arbitrary_types_allowed = True




