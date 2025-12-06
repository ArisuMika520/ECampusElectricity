"""电费查询服务"""
from app.core.electricity import ECampusElectricity
from app.models.config import Config
from sqlmodel import Session, select
from typing import Dict, Any, Optional


class ElectricityService:
    """电费查询服务"""
    
    def __init__(self, session: Session, user_id: Optional[str] = None):
        """
        初始化电费查询服务
        
        Args:
            session: 数据库会话
            user_id: 用户 ID，用于加载用户特定配置
        """
        self.session = session
        self.user_id = user_id
        self._ece = None
    
    def _get_ece_instance(self) -> ECampusElectricity:
        """获取或创建带配置的 ECampusElectricity 实例"""
        if self._ece is None:
            config = self._load_config()
            self._ece = ECampusElectricity(config)
        return self._ece
    
    def _load_config(self) -> Dict[str, Any]:
        """从数据库加载配置"""
        config_dict = {}
        statement = select(Config).where(Config.key == "shiroJID")
        if self.user_id:
            statement = statement.where(Config.user_id == self.user_id)
        shiro_config = self.session.exec(statement).first()
        if shiro_config:
            config_dict['shiroJID'] = shiro_config.value.get('value', '')
        smtp_keys = ['smtp_server', 'smtp_port', 'smtp_user', 'smtp_pass', 'from_email', 'use_tls']
        for key in smtp_keys:
            statement = select(Config).where(Config.key == key)
            if self.user_id:
                statement = statement.where(Config.user_id == self.user_id)
            config_item = self.session.exec(statement).first()
            if config_item:
                config_dict[key] = config_item.value.get('value')
        
        return config_dict
    
    def query_area(self) -> Dict[str, Any]:
        """查询校区信息"""
        ece = self._get_ece_instance()
        return ece.query_area()
    
    def query_building(self, area_id: str) -> Dict[str, Any]:
        """查询楼栋信息"""
        ece = self._get_ece_instance()
        return ece.query_building(area_id)
    
    def query_floor(self, area_id: str, building_code: str) -> Dict[str, Any]:
        """查询楼层信息"""
        ece = self._get_ece_instance()
        return ece.query_floor(area_id, building_code)
    
    def query_room(self, area_id: str, building_code: str, floor_code: str) -> Dict[str, Any]:
        """查询房间信息"""
        ece = self._get_ece_instance()
        return ece.query_room(area_id, building_code, floor_code)
    
    def query_room_surplus(self, area_id: str, building_code: str, 
                          floor_code: str, room_code: str) -> Dict[str, Any]:
        """查询房间电费余额"""
        ece = self._get_ece_instance()
        return ece.query_room_surplus(area_id, building_code, floor_code, room_code)



