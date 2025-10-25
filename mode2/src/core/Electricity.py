"""
电费抓取脚本
- 获取房间名称与电费余额get_myRoom

Build by ArisuMika
"""
from email.header import Header
from email.mime.text import MIMEText
from email.utils import formataddr
import smtplib
from time import sleep
import json
import os
import re
from threading import RLock
import requests
from botpy import logging

_log = logging.get_logger()

# 偏移缓存相关对象（锁 / 文件路径 / 内存缓存 / 状态标记）
_OFFSET_LOCK = RLock()
_OFFSET_FILE = None
_OFFSET_CACHE = {}
_OFFSET_LOADED = False


def configure_offset_file(file_path):
    """
    配置楼层偏移缓存的持久化文件路径。
    """
    if not file_path:
        return
    abs_path = os.path.abspath(file_path)
    global _OFFSET_FILE
    if _OFFSET_FILE == abs_path:
        return
    with _OFFSET_LOCK:
        _OFFSET_FILE = abs_path
        _load_offset_cache(force=True)


def _ensure_offset_file():
    """
    确保始终使用约定的偏移缓存文件。
    """
    global _OFFSET_FILE
    if _OFFSET_FILE is not None:
        return
    default_path = os.path.abspath(
        os.path.join(os.path.dirname(__file__), '..', '..', 'data_files', 'floor_offset.json')
    )
    _OFFSET_FILE = default_path


def _load_offset_cache(force=False):
    """
    读取偏移缓存文件，必要时强制刷新。
    """
    _ensure_offset_file()
    global _OFFSET_LOADED, _OFFSET_CACHE
    if _OFFSET_LOADED and not force:
        return
    with _OFFSET_LOCK:
        _OFFSET_LOADED = True
        _OFFSET_CACHE = {}
        try:
            os.makedirs(os.path.dirname(_OFFSET_FILE), exist_ok=True)
            if not os.path.exists(_OFFSET_FILE):
                return
            with open(_OFFSET_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
            if isinstance(data, dict):
                for key, value in data.items():
                    try:
                        _OFFSET_CACHE[key] = int(value)
                    except (TypeError, ValueError):
                        _log.warning(f"忽略无效的偏移配置：{key} -> {value}")
        except Exception as e:
            _log.error(f"读取楼层偏移缓存失败：{e}")


def _save_offset_cache():
    """
    将当前偏移缓存写回磁盘。
    """
    if not _OFFSET_LOADED:
        return
    _ensure_offset_file()
    with _OFFSET_LOCK:
        try:
            os.makedirs(os.path.dirname(_OFFSET_FILE), exist_ok=True)
            with open(_OFFSET_FILE, 'w', encoding='utf-8') as f:
                json.dump(_OFFSET_CACHE, f, ensure_ascii=False, indent=4)
        except Exception as e:
            _log.error(f"保存楼层偏移缓存失败：{e}")


def _offset_key(area_id, building_code, floor_code):
    return f"{area_id}|{building_code}|{floor_code}"


def _get_cached_offset(area_id, building_code, floor_code):
    _load_offset_cache()
    key = _offset_key(area_id, building_code, floor_code)
    return _OFFSET_CACHE.get(key, 0)


def _update_cached_offset(area_id, building_code, floor_code, offset):
    _load_offset_cache()
    key = _offset_key(area_id, building_code, floor_code)
    if _OFFSET_CACHE.get(key) == offset:
        return
    _OFFSET_CACHE[key] = offset
    _log.info(f"更新楼层偏移：{key} -> {offset}")
    _save_offset_cache()


def _extract_room_number(room_entry):
    """
    尝试从房间信息中解析出末尾的房间号。
    """
    if not isinstance(room_entry, dict):
        return None
    name_candidates = [
        room_entry.get('displayRoomName'),
        room_entry.get('roomName'),
        room_entry.get('roomAlias')
    ]
    for raw_name in name_candidates:
        if not raw_name:
            continue
        numbers = re.findall(r'(\d{3,4})', str(raw_name))
        if numbers:
            try:
                return int(numbers[-1])
            except ValueError:
                continue
    return None


def _fetch_room_by_index(room_list, index):
    if not isinstance(room_list, list):
        return None
    if index < 0 or index >= len(room_list):
        return None
    return room_list[index]


def _detect_offset(room_list, original_index, expected_number):
    """
    基于当前楼层数据动态计算偏移量。
    """
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


def _resolve_room_entry(area_id, building_code, floor_code, room_list, original_index, expected_number):
    """结合缓存与实时校验，输出目标房间条目。

    Args:
        area_id (str): 校区ID。
        building_code (str): 楼栋编码。
        floor_code (str): 楼层编码。
        room_list (list): 当前楼层房间列表。
        original_index (int): 旧逻辑使用的索引。
        expected_number (int): 期望的人类可读房间号。
    """
    #  尝试使用缓存偏移
    cached_offset = _get_cached_offset(area_id, building_code, floor_code)
    candidate_index = original_index + cached_offset
    candidate_entry = _fetch_room_by_index(room_list, candidate_index)
    if candidate_entry and _extract_room_number(candidate_entry) == expected_number:
        return candidate_entry

    #  缓存失效时再动态检测一次
    detected_offset = _detect_offset(room_list, original_index, expected_number)
    if detected_offset is not None:
        adjusted_index = original_index + detected_offset
        adjusted_entry = _fetch_room_by_index(room_list, adjusted_index)
        if adjusted_entry and _extract_room_number(adjusted_entry) == expected_number:
            _update_cached_offset(area_id, building_code, floor_code, detected_offset)
            return adjusted_entry

    #  兜底返回原始索引结果，避免调用方直接崩溃
    fallback_entry = _fetch_room_by_index(room_list, original_index)
    if fallback_entry:
        fallback_number = _extract_room_number(fallback_entry)
        _log.warning(
            f"楼层偏移自动修正失败，使用原始索引。期望房间号 {expected_number}，实际 {fallback_number}"
        )
    else:
        _log.error(f"楼层偏移自动修正失败，原始索引 {original_index} 超出范围")
    return fallback_entry
# 电费查询脚本
class ECampusElectricity:
    def __init__(self, config=None):
        self.config = {
            'shiroJID': '',
            'alert_threshold': 20.0 
        }
        if config:
            self.config.update(config)

    def set_config(self, config):
        self.config.update(config)

    def school_info(self):
        data = self._request('getCoutomConfig', {'customType': 1})
        if data.get('success'):
            return {
                'error': 0,
                'data': {
                    'schoolCode': data['data']['schoolCode'],
                    'schoolName': data['data']['schoolName']
                }
            }
        return self._error_response(data)

    def query_area(self):
        data = self._request('queryArea', {'type': 1})
        if data.get('success'):
            for item in data['rows']:
                item.pop('paymentChannel', None)
                item.pop('isBindAfterRecharge', None)
                item.pop('bindRoomNum', None)
            return {'error': 0, 'data': data['rows']}
        return self._error_response(data)

    def query_building(self, area_id):
        data = self._request('queryBuilding', {'areaId': area_id})
        if data.get('success'):
            return {'error': 0, 'data': data['rows']}
        return self._error_response(data)

    def query_floor(self, area_id, building_code):
        data = self._request('queryFloor', {
            'areaId': area_id,
            'buildingCode': building_code
        })
        if data.get('success'):
            return {'error': 0, 'data': data['rows']}
        return self._error_response(data)

    def query_room(self, area_id, building_code, floor_code):
        data = self._request('queryRoom', {
            'areaId': area_id,
            'buildingCode': building_code,
            'floorCode': floor_code
        })
        if data.get('success'):
            return {'error': 0, 'data': data['rows']}
        return self._error_response(data)

    def query_room_surplus(self, area_id, building_code, floor_code, room_code):
        data = self._request('queryRoomSurplus', {
            'areaId': area_id,
            'buildingCode': building_code,
            'floorCode': floor_code,
            'roomCode': room_code
        })
        if data.get('success'):
            return {
                'error': 0,
                'data': {
                    'surplus': data['data']['amount'],
                    'roomName': data['data']['displayRoomName']
                }
            }
        return self._error_response(data)

    def _error_response(self, data):
        return {
            'error': 1,
            'error_description': self._errcode(data.get('statusCode', 0))
        }

    def _errcode(self, code):
        return {
            233: 'shiroJID无效',
        }.get(code, '未知错误')

    def _request(self, uri, params):
        url = f'https://application.xiaofubao.com/app/electric/{uri}'
        params.update({
            'platform': 'YUNMA_APP'
        })
        headers = {
            'Cookie': f'shiroJID={self.config["shiroJID"]}'
        }
        
        try:
            response = requests.post(
                url,
                params=params,
                headers=headers,
                #verify=False
            )
            return response.json()
        except Exception as e:
            print(f"Request Error: {e}")
            return {'success': False}
    
    def get_myRoom(area,building,floor,room,ece):
        # 获取校区
        area_info = ece.query_area()
        area_id = area_info['data'][area]['id']
        # 获取宿舍楼
        building_list = ece.query_building(area_id)
        building_code = building_list['data'][building]['buildingCode']
        # 获取楼层
        floor_list = ece.query_floor(area_id, building_code)
        floor_code = floor_list['data'][floor]['floorCode']
        # 获取房间并做偏移纠正
        room_list = ece.query_room(area_id, building_code, floor_code)
        rooms = room_list['data']
        # 将楼层/房号转可读编号
        expected_number = (floor + 1) * 100 + (room + 1)
        target_entry = _resolve_room_entry(
            area_id,
            building_code,
            floor_code,
            rooms,
            room,
            expected_number
        )
        if not target_entry:
            raise ValueError(f"未能定位房间数据，楼层：{floor_code}，索引：{room}")

        room_code = target_entry['roomCode']
        # 获取电费信息
        room_info = ece.query_room_surplus(area_id, building_code, floor_code, room_code)
        surplus = room_info['data']['surplus']
        name = room_info['data']['roomName']
        return (surplus,name)
    

