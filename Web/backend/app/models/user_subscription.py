"""用户与订阅的关联模型"""
from sqlmodel import SQLModel, Field
from datetime import datetime
import uuid


class UserSubscription(SQLModel, table=True):
    """多对多映射：用户拥有的订阅"""
    __tablename__ = "user_subscriptions"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    user_id: uuid.UUID = Field(foreign_key="users.id", index=True)
    subscription_id: uuid.UUID = Field(foreign_key="subscriptions.id", index=True)
    is_owner: bool = Field(default=False, description="是否为订阅创建者/拥有者")
    created_at: datetime = Field(default_factory=datetime.utcnow)



