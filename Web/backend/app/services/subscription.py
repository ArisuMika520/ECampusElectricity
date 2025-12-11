"""订阅管理服务"""
from sqlmodel import Session, select
from app.models.subscription import Subscription
from app.models.user_subscription import UserSubscription
from app.schemas.subscription import SubscriptionCreate, SubscriptionUpdate
from typing import List, Optional
import uuid
from datetime import datetime
from app.utils.room_parser import parse_building_room, parse_room_name, RoomParseError


class SubscriptionService:
    """订阅管理服务"""
    
    def __init__(self, session: Session):
        self.session = session
    
    def get_user_subscriptions(self, user_id: uuid.UUID, include_all: bool = False) -> List[Subscription]:
        """获取用户的所有订阅。管理员可查看全部。"""
        if include_all:
            statement = select(Subscription)
        else:
            statement = (
                select(Subscription)
                .join(UserSubscription, UserSubscription.subscription_id == Subscription.id)
                .where(UserSubscription.user_id == user_id)
            )
        return list(self.session.exec(statement).all())
    
    def _user_can_access(self, subscription_id: uuid.UUID, user_id: uuid.UUID, allow_admin: bool) -> bool:
        """检查用户是否可访问该订阅"""
        mapping_stmt = select(UserSubscription).where(
            UserSubscription.subscription_id == subscription_id,
            UserSubscription.user_id == user_id
        )
        mapping = self.session.exec(mapping_stmt).first()
        if mapping:
            return True
        if allow_admin:
            # 管理员可查看全部
            return True
        return False

    def get_subscription(self, subscription_id: uuid.UUID, user_id: uuid.UUID, is_admin: bool = False) -> Optional[Subscription]:
        """根据 ID 获取指定订阅（确保用户有访问权限或管理员）"""
        statement = select(Subscription).where(Subscription.id == subscription_id)
        subscription = self.session.exec(statement).first()
        if not subscription:
            return None
        if not self._user_can_access(subscription_id, user_id, allow_admin=is_admin):
            return None
        return subscription
    
    def _normalize_payload(self, data: SubscriptionCreate) -> dict:
        """规范化订阅创建输入，支持楼栋+房间号或 room_name 简化填写。"""
        payload = data.model_dump()
        # 优先使用 building_name + room_number
        try:
            if payload.get("building_name") and payload.get("room_number"):
                parsed = parse_building_room(payload["building_name"], payload["room_number"])
                payload.update(parsed)
            elif payload.get("room_name") and (not payload.get("area_id") or not payload.get("building_code")):
                parsed = parse_room_name(payload["room_name"])
                payload.update(parsed)
        except RoomParseError as e:
            raise ValueError(str(e))

        required_fields = ["room_name", "area_id", "building_code", "floor_code", "room_code"]
        for f in required_fields:
            if not payload.get(f):
                raise ValueError(f"缺少必要字段: {f}")
        return payload

    def create_subscription(self, user_id: uuid.UUID, data: SubscriptionCreate) -> Subscription:
        """创建新订阅；若房间已存在则直接授权用户访问"""
        payload = self._normalize_payload(data)

        # 1. 查是否已有房间
        existing_stmt = select(Subscription).where(Subscription.room_name == payload["room_name"])
        existing = self.session.exec(existing_stmt).first()

        if existing:
            # 检查是否已有映射
            mapping_stmt = select(UserSubscription).where(
                UserSubscription.subscription_id == existing.id,
                UserSubscription.user_id == user_id
            )
            mapping = self.session.exec(mapping_stmt).first()
            if mapping:
                return existing
            mapping = UserSubscription(
                user_id=user_id,
                subscription_id=existing.id,
                is_owner=False
            )
            self.session.add(mapping)
            self.session.commit()
            return existing

        # 2. 新建订阅并创建关联
        subscription = Subscription(
            user_id=user_id,
            room_name=payload["room_name"],
            area_id=payload["area_id"],
            building_code=payload["building_code"],
            floor_code=payload["floor_code"],
            room_code=payload["room_code"],
            threshold=payload.get("threshold", 20.0),
            email_recipients=payload.get("email_recipients", []),
            is_active=payload.get("is_active", True),
        )
        self.session.add(subscription)
        self.session.commit()
        self.session.refresh(subscription)

        mapping = UserSubscription(
            user_id=user_id,
            subscription_id=subscription.id,
            is_owner=True
        )
        self.session.add(mapping)
        self.session.commit()
        return subscription
    
    def update_subscription(
        self, 
        subscription_id: uuid.UUID, 
        user_id: uuid.UUID,
        data: SubscriptionUpdate,
        is_admin: bool = False
    ) -> Optional[Subscription]:
        """更新现有订阅，仅所有者或管理员可以修改"""
        subscription = self.get_subscription(subscription_id, user_id, is_admin=is_admin)
        if not subscription:
            return None

        # 非管理员需要是 owner 才能更新
        if not is_admin:
            mapping_stmt = select(UserSubscription).where(
                UserSubscription.subscription_id == subscription_id,
                UserSubscription.user_id == user_id,
                UserSubscription.is_owner == True
            )
            if not self.session.exec(mapping_stmt).first():
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
        """删除订阅。如果用户不是所有者，仅移除自己的关联。"""
        subscription = self.get_subscription(subscription_id, user_id, is_admin=False)
        if not subscription:
            return False

        mapping_stmt = select(UserSubscription).where(
            UserSubscription.subscription_id == subscription_id,
            UserSubscription.user_id == user_id
        )
        mapping = self.session.exec(mapping_stmt).first()
        if mapping and not mapping.is_owner:
            self.session.delete(mapping)
            self.session.commit()
            return True

        # 所有者删除订阅及所有关联
        map_all_stmt = select(UserSubscription).where(UserSubscription.subscription_id == subscription_id)
        for m in self.session.exec(map_all_stmt).all():
            self.session.delete(m)
        self.session.delete(subscription)
        self.session.commit()
        return True
    
    def get_active_subscriptions(self) -> List[Subscription]:
        """获取所有活跃订阅（用于调度器）"""
        statement = select(Subscription).where(Subscription.is_active == True)
        return list(self.session.exec(statement).all())



