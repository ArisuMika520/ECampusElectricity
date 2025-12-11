from typing import Any, Dict, Optional
from sqlmodel import Session, select
from app.core.electricity import ECampusElectricity
from app.models.config import Config


class ElectricityService:
    def __init__(self, session: Session, user_id: Optional[str] = None):
        self.session = session
        self.user_id = user_id
        self._ece = None
    
    def _get_ece_instance(self) -> ECampusElectricity:
        if self._ece is None:
            config = self._load_config()
            self._ece = ECampusElectricity(config)
        return self._ece
    
    def _load_config(self) -> Dict[str, Any]:
        def fetch_key(key: str):
            user_stmt = select(Config).where(Config.key == key)
            global_stmt = select(Config).where(Config.key == key, Config.user_id == None)  # noqa: E711
            if self.user_id:
                user_stmt = user_stmt.where(Config.user_id == self.user_id)
                found = self.session.exec(user_stmt).first()
                if found:
                    return found
            return self.session.exec(global_stmt).first()

        config_dict: Dict[str, Any] = {}
        shiro_config = fetch_key("shiroJID")
        if shiro_config:
            config_dict["shiroJID"] = shiro_config.value.get("value", "")

        smtp_keys = ["smtp_server", "smtp_port", "smtp_user", "smtp_pass", "from_email", "use_tls"]
        for key in smtp_keys:
            item = fetch_key(key)
            if item:
                config_dict[key] = item.value.get("value")

        offset_file = fetch_key("floor_offset_file")
        if offset_file:
            config_dict["floor_offset_file"] = offset_file.value.get("value")

        return config_dict
    
    def query_area(self) -> Dict[str, Any]:
        ece = self._get_ece_instance()
        return ece.query_area()
    
    def query_building(self, area_id: str) -> Dict[str, Any]:
        ece = self._get_ece_instance()
        return ece.query_building(area_id)
    
    def query_floor(self, area_id: str, building_code: str) -> Dict[str, Any]:
        ece = self._get_ece_instance()
        return ece.query_floor(area_id, building_code)
    
    def query_room(self, area_id: str, building_code: str, floor_code: str) -> Dict[str, Any]:
        ece = self._get_ece_instance()
        return ece.query_room(area_id, building_code, floor_code)
    
    def query_room_surplus(self, area_id: str, building_code: str, 
                          floor_code: str, room_code: str) -> Dict[str, Any]:
        ece = self._get_ece_instance()
        return ece.query_room_surplus(area_id, building_code, floor_code, room_code)

    def query_room_surplus_by_human(self, area_index: int, building_name: str, floor: int, room: int) -> Dict[str, Any]:
        ece = self._get_ece_instance()
        return ece.query_room_surplus_by_human(area_index, building_name, floor, room)

    def query_room_surplus_by_room_name(self, room_name: str) -> Dict[str, Any]:
        ece = self._get_ece_instance()
        return ece.query_room_surplus_by_room_name(room_name)



