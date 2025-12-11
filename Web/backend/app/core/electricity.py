"""电费核心查询"""
import json
import logging
import os
import re
import smtplib
import time
from email.header import Header
from email.mime.text import MIMEText
from email.utils import formataddr
from threading import RLock
from typing import Any, Dict, List, Optional

import requests

from app.core.buildings import get_building_index

logger = logging.getLogger(__name__)

# 偏移缓存相关对象（锁 / 文件路径 / 内存缓存 / 状态标记）
_OFFSET_LOCK = RLock()
_OFFSET_FILE = None
_OFFSET_CACHE: Dict[str, int] = {}
_OFFSET_LOADED = False


def configure_offset_file(file_path: Optional[str]):
    """
    配置楼层偏移缓存的持久化文件路径。
    """
    global _OFFSET_FILE
    with _OFFSET_LOCK:
        if file_path:
            abs_path = os.path.abspath(file_path)
            if _OFFSET_FILE == abs_path:
                return
            _OFFSET_FILE = abs_path
        else:
            _ensure_offset_file()
        _load_offset_cache(force=True)


def _ensure_offset_file():
    """确保始终使用约定的偏移缓存文件。"""
    global _OFFSET_FILE
    if _OFFSET_FILE is not None:
        return
    default_path = os.path.abspath(
        os.path.join(os.path.dirname(__file__), "..", "..", "data", "floor_offset.json")
    )
    _OFFSET_FILE = default_path


def _load_offset_cache(force: bool = False):
    """读取偏移缓存文件，必要时强制刷新。"""
    _ensure_offset_file()
    global _OFFSET_LOADED, _OFFSET_CACHE
    if _OFFSET_LOADED and not force:
        return
    with _OFFSET_LOCK:
        _OFFSET_LOADED = True
        _OFFSET_CACHE = {}
        try:
            os.makedirs(os.path.dirname(_OFFSET_FILE), exist_ok=True)  # type: ignore
            if not os.path.exists(_OFFSET_FILE):  # type: ignore
                return
            with open(_OFFSET_FILE, "r", encoding="utf-8") as f:  # type: ignore
                data = json.load(f)
            if isinstance(data, dict):
                for key, value in data.items():
                    try:
                        _OFFSET_CACHE[key] = int(value)
                    except (TypeError, ValueError):
                        logger.warning("忽略无效的偏移配置：%s -> %s", key, value)
        except Exception as e:  # pragma: no cover - 记录异常即可
            logger.error("读取楼层偏移缓存失败：%s", e)


def _save_offset_cache():
    """将当前偏移缓存写回磁盘。"""
    if not _OFFSET_LOADED:
        return
    _ensure_offset_file()
    with _OFFSET_LOCK:
        try:
            os.makedirs(os.path.dirname(_OFFSET_FILE), exist_ok=True)  # type: ignore
            with open(_OFFSET_FILE, "w", encoding="utf-8") as f:  # type: ignore
                json.dump(_OFFSET_CACHE, f, ensure_ascii=False, indent=4)
        except Exception as e:  # pragma: no cover
            logger.error("保存楼层偏移缓存失败：%s", e)


def _offset_key(area_id: str, building_code: str, floor_code: str) -> str:
    return f"{area_id}|{building_code}|{floor_code}"


def _get_cached_offset(area_id: str, building_code: str, floor_code: str) -> int:
    _load_offset_cache()
    key = _offset_key(area_id, building_code, floor_code)
    return _OFFSET_CACHE.get(key, 0)


def _update_cached_offset(area_id: str, building_code: str, floor_code: str, offset: int):
    _load_offset_cache()
    key = _offset_key(area_id, building_code, floor_code)
    if _OFFSET_CACHE.get(key) == offset:
        return
    _OFFSET_CACHE[key] = offset
    logger.info("更新楼层偏移：%s -> %s", key, offset)
    _save_offset_cache()


def _extract_room_number(room_entry: Dict[str, Any]):
    """尝试从房间信息中解析出末尾的房间号。"""
    if not isinstance(room_entry, dict):
        return None
    name_candidates = [
        room_entry.get("displayRoomName"),
        room_entry.get("roomName"),
        room_entry.get("roomAlias"),
    ]
    for raw_name in name_candidates:
        if not raw_name:
            continue
        numbers = re.findall(r"(\d{3,4})", str(raw_name))
        if numbers:
            try:
                return int(numbers[-1])
            except ValueError:
                continue
    return None


def _fetch_room_by_index(room_list, index: int):
    if not isinstance(room_list, list):
        return None
    if index < 0 or index >= len(room_list):
        return None
    return room_list[index]


def _detect_offset(room_list, original_index: int, expected_number: int):
    """基于当前楼层数据动态计算偏移量。"""
    base_entry = _fetch_room_by_index(room_list, original_index)
    base_number = _extract_room_number(base_entry)
    if base_number is None:
        return None
    delta = expected_number - base_number
    if delta == 0:
        return 0
    adjusted_entry = _fetch_room_by_index(room_list, original_index + delta)
    if adjusted_entry and _extract_room_number(adjusted_entry) == expected_number:
        return delta
    return None


def _resolve_room_entry(area_id: str, building_code: str, floor_code: str, room_list, original_index: int, expected_number: int):
    """
    结合缓存与实时校验，输出目标房间条目。
    """
    cached_offset = _get_cached_offset(area_id, building_code, floor_code)
    candidate_index = original_index + cached_offset
    candidate_entry = _fetch_room_by_index(room_list, candidate_index)
    if candidate_entry and _extract_room_number(candidate_entry) == expected_number:
        return candidate_entry

    detected_offset = _detect_offset(room_list, original_index, expected_number)
    if detected_offset is not None:
        adjusted_index = original_index + detected_offset
        adjusted_entry = _fetch_room_by_index(room_list, adjusted_index)
        if adjusted_entry and _extract_room_number(adjusted_entry) == expected_number:
            _update_cached_offset(area_id, building_code, floor_code, detected_offset)
            return adjusted_entry

    fallback_entry = _fetch_room_by_index(room_list, original_index)
    if fallback_entry:
        fallback_number = _extract_room_number(fallback_entry)
        logger.warning(
            "楼层偏移自动修正失败，使用原始索引。期望房间号 %s，实际 %s",
            expected_number,
            fallback_number,
        )
    else:
        logger.error("楼层偏移自动修正失败，原始索引 %s 超出范围", original_index)
    return fallback_entry


class ECampusElectricity:
    """校园电费信息查询核心类（含楼层偏移自校准）"""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        使用配置初始化 ECampusElectricity
        """
        self.config = {
            "shiroJID": "",
            "smtp_server": "smtp.qq.com",
            "smtp_port": 465,
            "smtp_user": "",
            "smtp_pass": "",
            "from_email": "",
            "use_tls": False,
            "alert_threshold": 20.0,
            "floor_offset_file": None,
        }
        if config:
            self.config.update(config)
        configure_offset_file(self.config.get("floor_offset_file"))
        # 复用长连接，减少 TLS 握手耗时
        self._session = requests.Session()
        # 简单内存缓存，避免频繁重复拉取区域/楼栋/楼层
        self._cache_ttl = 300  # 秒
        self._area_cache: Dict[str, Any] = {}
        self._building_cache: Dict[str, Any] = {}
        self._floor_cache: Dict[str, Any] = {}

    def set_config(self, config: Dict[str, Any]):
        """更新配置"""
        self.config.update(config)
        if "floor_offset_file" in config:
            configure_offset_file(config.get("floor_offset_file"))

    def school_info(self) -> Dict[str, Any]:
        """获取学校信息"""
        data = self._request("getCoutomConfig", {"customType": 1})
        if data.get("success"):
            return {
                "error": 0,
                "data": {
                    "schoolCode": data["data"]["schoolCode"],
                    "schoolName": data["data"]["schoolName"],
                },
            }
        return self._error_response(data)

    def query_area(self) -> Dict[str, Any]:
        """查询校区信息"""
        cached = self._get_cache(self._area_cache, "all")
        if cached:
            return cached

        data = self._request("queryArea", {"type": 1})
        if data.get("success"):
            for item in data["rows"]:
                item.pop("paymentChannel", None)
                item.pop("isBindAfterRecharge", None)
                item.pop("bindRoomNum", None)
            result = {"error": 0, "data": data["rows"]}
            self._set_cache(self._area_cache, "all", result)
            return result
        return self._error_response(data)

    def query_building(self, area_id: str) -> Dict[str, Any]:
        """查询指定校区的楼栋信息"""
        cached = self._get_cache(self._building_cache, area_id)
        if cached:
            return cached

        data = self._request("queryBuilding", {"areaId": area_id})
        if data.get("success"):
            result = {"error": 0, "data": data["rows"]}
            self._set_cache(self._building_cache, area_id, result)
            return result
        return self._error_response(data)

    def query_floor(self, area_id: str, building_code: str) -> Dict[str, Any]:
        """查询指定楼栋的楼层信息"""
        cache_key = f"{area_id}|{building_code}"
        cached = self._get_cache(self._floor_cache, cache_key)
        if cached:
            return cached

        data = self._request(
            "queryFloor",
            {
                "areaId": area_id,
                "buildingCode": building_code,
            },
        )
        if data.get("success"):
            result = {"error": 0, "data": data["rows"]}
            self._set_cache(self._floor_cache, cache_key, result)
            return result
        return self._error_response(data)

    def query_room(self, area_id: str, building_code: str, floor_code: str) -> Dict[str, Any]:
        """查询指定楼层的房间信息"""
        data = self._request(
            "queryRoom",
            {
                "areaId": area_id,
                "buildingCode": building_code,
                "floorCode": floor_code,
            },
        )
        if data.get("success"):
            return {"error": 0, "data": data["rows"]}
        return self._error_response(data)

    def query_room_surplus(self, area_id: str, building_code: str, floor_code: str, room_code: str) -> Dict[str, Any]:
        """查询指定房间的电费余额"""
        data = self._request(
            "queryRoomSurplus",
            {
                "areaId": area_id,
                "buildingCode": building_code,
                "floorCode": floor_code,
                "roomCode": room_code,
            },
        )
        if data.get("success"):
            return {
                "error": 0,
                "data": {
                    "surplus": data["data"]["amount"],
                    "roomName": data["data"]["displayRoomName"],
                },
            }
        return self._error_response(data)

    def query_room_surplus_by_human(self, area_index: int, building_name: str, floor_number: int, room_number: int) -> Dict[str, Any]:
        """
        使用人类（？可读的楼栋+房间号进行查询，并自动纠正楼层偏移。
        """
        try:
            area_idx = int(area_index)
        except (TypeError, ValueError):
            return {"error": 1, "error_description": "区域编号无效"}

        try:
            building_idx = get_building_index(area_idx, building_name)
        except Exception:
            return {"error": 1, "error_description": f"未知楼栋: {building_name}"}

        try:
            floor_idx = max(int(floor_number) - 1, 0)
        except (TypeError, ValueError):
            return {"error": 1, "error_description": "楼层编号无效"}

        room_number_str = str(room_number)
        if len(room_number_str) < 3 or len(room_number_str) > 4 or not room_number_str.isdigit():
            return {"error": 1, "error_description": "房间号格式错误，需为3-4位数字"}

        try:
            room_idx = int(room_number_str[1:]) - 1
        except ValueError:
            return {"error": 1, "error_description": "房间号格式错误"}

        expected_number = (floor_idx + 1) * 100 + (room_idx + 1)

        area_info = self.query_area()
        if area_info.get("error") != 0:
            return area_info
        try:
            area_id = area_info["data"][area_idx]["id"]
        except Exception:
            return {"error": 1, "error_description": "无法获取校区信息，请检查区域编号"}

        building_list = self.query_building(area_id)
        if building_list.get("error") != 0:
            return building_list
        try:
            building_code = building_list["data"][building_idx]["buildingCode"]
        except Exception:
            return {"error": 1, "error_description": "无法匹配楼栋，请检查楼栋名称"}

        floor_list = self.query_floor(area_id, building_code)
        if floor_list.get("error") != 0:
            return floor_list
        try:
            floor_code = floor_list["data"][floor_idx]["floorCode"]
        except Exception:
            return {"error": 1, "error_description": "无法匹配楼层，请检查房间号"}

        room_list = self.query_room(area_id, building_code, floor_code)
        if room_list.get("error") != 0:
            return room_list
        rooms = room_list.get("data", [])

        target_entry = _resolve_room_entry(
            area_id,
            building_code,
            floor_code,
            rooms,
            room_idx,
            expected_number,
        )
        if not target_entry:
            return {"error": 1, "error_description": "未能定位房间数据"}

        room_code = target_entry.get("roomCode")
        if not room_code:
            return {"error": 1, "error_description": "房间数据异常，缺少 roomCode"}

        return self.query_room_surplus(area_id, building_code, floor_code, room_code)

    def query_room_surplus_by_room_name(self, room_name: str) -> Dict[str, Any]:
        """
        兼容 Bot 写法
        - "D9东 425"
        - "10南 101"
        - "D9东425"（无空格也可）
        """
        if not room_name:
            return {"error": 1, "error_description": "房间名不能为空"}

        parts = room_name.strip().split()
        building = None
        room_token = None

        if len(parts) == 2:
            building, room_token = parts
        elif len(parts) == 1:
            match = re.match(r"^(.+?)(\d{3,4})$", parts[0])
            if match:
                building, room_token = match.group(1), match.group(2)
        if not building or not room_token:
            return {"error": 1, "error_description": "房间名格式应为 '楼栋 房间号'，如 D9东 425"}

        area_idx = 1 if building.startswith("D") else 0
        try:
            floor_num = int(room_token[0])
            room_num_full = int(room_token)
        except (ValueError, IndexError):
            return {"error": 1, "error_description": "房间号格式错误，应为3-4位数字"}

        return self.query_room_surplus_by_human(area_idx, building, floor_num, room_num_full)

    def check_and_alert(self, room_info: Dict[str, Any], recipients: List[str], threshold: Optional[float] = None) -> bool:
        """检查电费余额并在需要时发送告警邮件"""
        if room_info.get("error") != 0:
            return False

        surplus = float(room_info["data"]["surplus"])
        threshold = threshold or self.config.get("alert_threshold", 20.0)

        if surplus < threshold:
            subject = f"电费告警：{room_info['data']['roomName']} 余额不足"
            content = f"""
房间名称：{room_info['data']['roomName']}
当前余额：{surplus} 元
告警阈值：{threshold} 元

请及时充值！
"""
            return self.send_alert(subject, content, recipients)
        return False

    def send_alert(self, subject: str, content: str, recipients: List[str]) -> bool:
        """发送告警邮件"""
        try:
            if self.config.get("use_tls", False):
                server = smtplib.SMTP(
                    host=self.config["smtp_server"],
                    port=self.config["smtp_port"],
                    timeout=15,
                )
                server.starttls()
            else:
                server = smtplib.SMTP_SSL(
                    host=self.config["smtp_server"],
                    port=self.config["smtp_port"],
                    timeout=15,
                )

            server.login(self.config["smtp_user"], self.config["smtp_pass"])
            msg = MIMEText(content, "plain", "utf-8")
            msg["Subject"] = Header(subject, "utf-8").encode()
            msg["From"] = formataddr(
                (
                    Header("电费监控系统", "utf-8").encode(),
                    self.config["from_email"],
                )
            )
            msg["To"] = ", ".join(recipients)

            server.sendmail(self.config["from_email"], recipients, msg.as_string())
            return True
        except smtplib.SMTPServerDisconnected as e:
            logger.error("SMTP 服务器意外断开：%s", e)
            return False
        except Exception as e:  # pragma: no cover - 捕获并记录异常
            logger.error("发送邮件异常：%s", e)
            return False

    def _error_response(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """生成错误响应，包含原始状态码和服务端 message"""
        status_code = data.get("statusCode", 0)
        message = data.get("message") or self._errcode(status_code)
        return {
            "error": 1,
            "statusCode": status_code,
            "error_description": message or "未知错误",
            "raw": data,
        }

    def _errcode(self, code: int) -> str:
        """根据错误代码获取错误描述"""
        error_codes = {
            233: "shiroJID无效",
        }
        return error_codes.get(code, "未知错误")

    def _request(self, uri: str, params: Dict[str, Any]) -> Dict[str, Any]:
        url = f"https://application.xiaofubao.com/app/electric/{uri}"
        params.update(
            {
                "platform": "YUNMA_APP",
            }
        )
        headers = {
            "Cookie": f"shiroJID={self.config['shiroJID']}",
        }

        try:
            response = self._session.post(
                url,
                params=params,
                headers=headers,
                verify=False,
                timeout=10,
            )
            return response.json()
        except Exception as e: 
            logger.error("Request Error: %s", e)
            return {"success": False, "exception": str(e)}

    def _get_cache(self, cache_store: Dict[str, Any], key: str):
        item = cache_store.get(key)
        if not item:
            return None
        data, ts = item
        if time.time() - ts > self._cache_ttl:
            cache_store.pop(key, None)
            return None
        return data

    def _set_cache(self, cache_store: Dict[str, Any], key: str, value: Any):
        cache_store[key] = (value, time.time())
