"""订阅管理服务"""
from sqlmodel import Session, select
from app.models.subscription import Subscription
from app.schemas.subscription import SubscriptionCreate, SubscriptionUpdate
from typing import List, Optional
import uuid
from datetime import datetime


class SubscriptionService:
    """订阅管理服务"""
    
    def __init__(self, session: Session):
        self.session = session
    
    def get_user_subscriptions(self, user_id: uuid.UUID) -> List[Subscription]:
        """获取用户的所有订阅"""
        statement = select(Subscription).where(Subscription.user_id == user_id)
        return list(self.session.exec(statement).all())
    
    def get_subscription(self, subscription_id: uuid.UUID, user_id: uuid.UUID) -> Optional[Subscription]:
        """根据 ID 获取指定订阅（确保属于该用户）"""
        statement = select(Subscription).where(
            Subscription.id == subscription_id,
            Subscription.user_id == user_id
        )
        return self.session.exec(statement).first()
    
    def create_subscription(self, user_id: uuid.UUID, data: SubscriptionCreate) -> Subscription:
        """创建新订阅"""
        subscription = Subscription(
            user_id=user_id,
            **data.model_dump()
        )
        self.session.add(subscription)
        self.session.commit()
        self.session.refresh(subscription)
        return subscription
    
    def update_subscription(
        self, 
        subscription_id: uuid.UUID, 
        user_id: uuid.UUID,
        data: SubscriptionUpdate
    ) -> Optional[Subscription]:
        """更新现有订阅"""
        subscription = self.get_subscription(subscription_id, user_id)
        if not subscription:
            return None
        
        update_data = data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(subscription, key, value)
        
        subscription.updated_at = datetime.utcnow()
        self.session.add(subscription)
        self.session.commit()
        self.session.refresh(subscription)
        return subscription
    
    def delete_subscription(self, subscription_id: uuid.UUID, user_id: uuid.UUID) -> bool:
        """删除订阅"""
        subscription = self.get_subscription(subscription_id, user_id)
        if not subscription:
            return False
        
        self.session.delete(subscription)
        self.session.commit()
        return True
    
    def get_active_subscriptions(self) -> List[Subscription]:
        """获取所有活跃订阅（用于调度器）"""
        statement = select(Subscription).where(Subscription.is_active == True)
        return list(self.session.exec(statement).all())



