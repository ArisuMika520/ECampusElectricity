from sqlmodel import Session, select
from datetime import datetime, timedelta
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
    def __init__(self, session: Session):
        self.session = session
    
    def check_all_subscriptions(self):
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
        logger.info(f"Checking subscription: {subscription.room_name} (ID: {subscription.id})")
        
        owner_stmt = (
            select(UserSubscription)
            .where(UserSubscription.subscription_id == subscription.id)
            .order_by(UserSubscription.is_owner.desc(), UserSubscription.created_at.asc())
        )
        mapping = self.session.exec(owner_stmt).first()
        target_user_id = str(mapping.user_id) if mapping else str(subscription.user_id)

        electricity_service = ElectricityService(self.session, target_user_id)
        room_info = electricity_service.query_room_surplus_by_room_name(subscription.room_name)
        
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
        
        if surplus < subscription.threshold:
            logger.warning(f"Room {subscription.room_name} is below threshold ({subscription.threshold} yuan)")
            alert_service = AlertService(self.session, target_user_id)
            success = alert_service.send_alert(subscription, room_info)
            if success:
                logger.info(f"Alert sent for {subscription.room_name}")
            else:
                logger.warning(f"Failed to send alert for {subscription.room_name}")
        
        self._cleanup_old_history(subscription.id)
    
    def _should_add_history(self, subscription_id, surplus: float) -> bool:
        from sqlmodel import select
        statement = select(ElectricityHistory).where(
            ElectricityHistory.subscription_id == subscription_id
        ).order_by(ElectricityHistory.timestamp.desc()).limit(1)
        
        latest = self.session.exec(statement).first()
        
        if not latest:
            return True
        
        if latest.surplus == surplus:
            time_diff = datetime.utcnow() - latest.timestamp
            if time_diff < timedelta(hours=2):
                return False
        
        return True
    
    def _cleanup_old_history(self, subscription_id):
        from sqlmodel import select, func
        count_statement = select(func.count(ElectricityHistory.id)).where(
            ElectricityHistory.subscription_id == subscription_id
        )
        count = self.session.exec(count_statement).first()
        
        if count and count > settings.HISTORY_LIMIT:
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



