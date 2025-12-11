"""定时电费查询跟踪服务"""
from sqlmodel import Session
from datetime import datetime, timedelta
from typing import List
from app.models.subscription import Subscription
from app.models.history import ElectricityHistory
from app.services.subscription import SubscriptionService
from app.models.user_subscription import UserSubscription
from app.services.electricity import ElectricityService
from app.services.alert import AlertService
from app.config import settings
import logging

logger = logging.getLogger(__name__)


class TrackerService:
    """电费使用跟踪服务"""
    
    def __init__(self, session: Session):
        self.session = session
    
    def check_all_subscriptions(self):
        """检查所有活跃订阅并更新历史记录"""
        logger.info("Starting scheduled electricity check")
        
        service = SubscriptionService(self.session)
        subscriptions = service.get_active_subscriptions()
        
        logger.info(f"Found {len(subscriptions)} active subscriptions")
        
        for subscription in subscriptions:
            try:
                self._check_subscription(subscription)
            except Exception as e:
                logger.error(f"Error checking subscription {subscription.id}: {e}")
    
    def _check_subscription(self, subscription: Subscription):
        """检查单个订阅"""
        logger.info(f"Checking subscription: {subscription.room_name} (ID: {subscription.id})")
        
        # 选择一个关联用户作为查询/告警主体，优先 owner
        owner_stmt = (
            select(UserSubscription)
            .where(UserSubscription.subscription_id == subscription.id)
            .order_by(UserSubscription.is_owner.desc(), UserSubscription.created_at.asc())
        )
        mapping = self.session.exec(owner_stmt).first()
        target_user_id = str(mapping.user_id) if mapping else str(subscription.user_id)

        electricity_service = ElectricityService(self.session, target_user_id)
        room_info = electricity_service.query_room_surplus(
            subscription.area_id,
            subscription.building_code,
            subscription.floor_code,
            subscription.room_code
        )
        
        if room_info.get('error') != 0:
            logger.warning(f"Failed to query electricity for {subscription.room_name}: {room_info.get('error_description', 'Unknown error')}")
            return
        
        surplus = float(room_info['data']['surplus'])
        logger.info(f"Room {subscription.room_name} has surplus: {surplus} yuan")
        
        should_add = self._should_add_history(subscription.id, surplus)
        
        if should_add:
            history = ElectricityHistory(
                subscription_id=subscription.id,
                surplus=surplus,
                timestamp=datetime.utcnow()
            )
            self.session.add(history)
            self.session.commit()
            logger.info(f"Added history record for {subscription.room_name}")
        
        # 检查阈值并发送告警
        if surplus < subscription.threshold:
            logger.warning(f"Room {subscription.room_name} is below threshold ({subscription.threshold} yuan)")
            alert_service = AlertService(self.session, target_user_id)
            success = alert_service.send_alert(subscription, room_info)
            if success:
                logger.info(f"Alert sent for {subscription.room_name}")
            else:
                logger.warning(f"Failed to send alert for {subscription.room_name}")
        
        # 清理旧的历史记录
        self._cleanup_old_history(subscription.id)
    
    def _should_add_history(self, subscription_id, surplus: float) -> bool:
        """判断是否应该添加历史记录"""
        from sqlmodel import select
        statement = select(ElectricityHistory).where(
            ElectricityHistory.subscription_id == subscription_id
        ).order_by(ElectricityHistory.timestamp.desc()).limit(1)
        
        latest = self.session.exec(statement).first()
        
        if not latest:
            return True
        
        # 如果值相同且时间差小于 2 小时，则不添加
        if latest.surplus == surplus:
            time_diff = datetime.utcnow() - latest.timestamp
            if time_diff < timedelta(hours=2):
                return False
        
        return True
    
    def _cleanup_old_history(self, subscription_id):
        """清理超出限制的旧历史记录"""
        from sqlmodel import select, func
        count_statement = select(func.count(ElectricityHistory.id)).where(
            ElectricityHistory.subscription_id == subscription_id
        )
        count = self.session.exec(count_statement).first()
        
        if count and count > settings.HISTORY_LIMIT:
            # 获取需要保留的记录（最新的）
            keep_statement = select(ElectricityHistory).where(
                ElectricityHistory.subscription_id == subscription_id
            ).order_by(ElectricityHistory.timestamp.desc()).limit(settings.HISTORY_LIMIT)
            
            keep_records = list(self.session.exec(keep_statement).all())
            keep_ids = {r.id for r in keep_records}
            all_statement = select(ElectricityHistory).where(
                ElectricityHistory.subscription_id == subscription_id
            )
            all_records = list(self.session.exec(all_statement).all())
            
            deleted = 0
            for record in all_records:
                if record.id not in keep_ids:
                    self.session.delete(record)
                    deleted += 1
            
            if deleted > 0:
                self.session.commit()
                logger.info(f"Cleaned up {deleted} old history records for subscription {subscription_id}")



