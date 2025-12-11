"""邮件告警服务"""
from app.core.electricity import ECampusElectricity
from app.models.config import Config
from app.models.subscription import Subscription
from sqlmodel import Session, select
from typing import Dict, Any


class AlertService:
    """告警服务"""
    
    def __init__(self, session: Session, user_id: str):
        """
        初始化告警服务
        
        Args:
            session: 数据库会话
            user_id: 用户 ID，用于加载用户特定配置
        """
        self.session = session
        self.user_id = user_id
    
    def _load_smtp_config(self) -> Dict[str, Any]:
        """从数据库加载 SMTP 配置"""
        config_dict = {}
        smtp_keys = ['smtp_server', 'smtp_port', 'smtp_user', 'smtp_pass', 'from_email', 'use_tls']
        
        for key in smtp_keys:
            statement = select(Config).where(Config.key == key)
            if self.user_id:
                statement = statement.where(Config.user_id == self.user_id)
            config_item = self.session.exec(statement).first()
            if config_item:
                value = config_item.value.get('value')
                if key == 'smtp_port':
                    config_dict[key] = int(value) if value else 465
                elif key == 'use_tls':
                    config_dict[key] = bool(value) if value is not None else False
                else:
                    config_dict[key] = value
        
        return config_dict
    
    def send_alert(self, subscription: Subscription, room_info: Dict[str, Any], email_recipients: list = None, threshold: float = None) -> bool:
        """
        发送订阅的告警邮件
        
        Args:
            subscription: 订阅对象
            room_info: 来自 query_room_surplus 的房间信息
            email_recipients: 邮件收件人列表（可选，覆盖订阅的默认值）
            threshold: 告警阈值（可选，覆盖订阅的默认值）
            
        Returns:
            成功发送返回 True，否则返回 False
        """
        recipients = email_recipients or subscription.email_recipients
        if not recipients:
            return False
        
        alert_threshold = threshold or subscription.threshold
        
        smtp_config = self._load_smtp_config()
        if not smtp_config.get('smtp_user') or not smtp_config.get('smtp_pass'):
            return False
        statement = select(Config).where(Config.key == "shiroJID")
        if self.user_id:
            statement = statement.where(Config.user_id == self.user_id)
        shiro_config = self.session.exec(statement).first()
        shiro_jid = shiro_config.value.get('value', '') if shiro_config else ''
        config = {
            'shiroJID': shiro_jid,
            **smtp_config
        }
        ece = ECampusElectricity(config)
        return ece.check_and_alert(room_info, recipients, alert_threshold)




        return ece.check_and_alert(room_info, recipients, alert_threshold)


