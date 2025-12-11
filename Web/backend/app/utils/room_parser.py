"""房间输入解析工具：将楼栋+房间号转换为订阅所需字段。"""

from typing import Optional, Dict

# 直接使用 Bot 版本的楼栋映射
BUILDING_INDEX = [
    {
        "1东": 0,
        "1西": 1,
        "2东": 5,
        "2西": 6,
        "3北": 8,
        "3南": 9,
        "4东": 12,
        "4西": 13,
        "5北": 15,
        "5南": 16,
        "6东": 19,
        "6西": 20,
        "7北": 22,
        "7南": 23,
        "8东": 26,
        "8西": 27,
        "9北": 29,
        "9南": 30,
        "10北": 33,
        "10南": 34,
        "11北": 36,
        "11南": 37,
        "13": 39,
    },
    {
        "D1": 1,
        "D2": 2,
        "D3": 3,
        "D4东": 6,
        "D4西": 7,
        "D5": 8,
        "D6": 9,
        "D7东": 11,
        "D7西": 12,
        "D8": 13,
        "D9东": 14,
        "D9西": 15,
    },
]


class RoomParseError(ValueError):
    pass


def parse_building_room(building: str, room_number: str) -> Dict[str, str]:
    """解析楼栋与房间号，输出订阅所需字段。

    Args:
        building: 楼栋名称（如 "D9东" 或 "10南"）
        room_number: 房间号（如 "101"）

    Returns:
        dict 包含 area_id, building_code, floor_code, room_code, room_name, building_index
    """
    if not building or not room_number:
        raise RoomParseError("楼栋与房间号均不能为空")

    building_code = building.strip()
    room_code = room_number.strip()

    # area: 以 D 开头认为是东区（1），否则西区（0）
    area_id = "1" if building_code.startswith("D") else "0"

    # floor: 取房间号首位
    floor_code = room_code[0] if room_code else ""
    if not floor_code.isdigit():
        raise RoomParseError("房间号格式不正确，首位应为楼层数字")

    # 查楼栋索引，若不存在则报错
    try:
        building_index = BUILDING_INDEX[int(area_id)][building_code]
    except Exception:
        raise RoomParseError(f"未找到楼栋映射: {building_code}")

    room_name = f"{building_code} {room_code}"

    return {
        "area_id": area_id,
        "building_code": building_code,
        "floor_code": floor_code,
        "room_code": room_code,
        "room_name": room_name,
        "building_index": str(building_index),
    }


def parse_room_name(room_name: str) -> Dict[str, str]:
    """从完整房间名（形如 'D9东 101' 或 '10南 101'）解析。"""
    if not room_name:
        raise RoomParseError("房间名不能为空")
    parts = room_name.strip().split()
    if len(parts) != 2:
        raise RoomParseError("房间名格式应为 '楼栋 房间号'，例如 D9东 101")
    return parse_building_room(parts[0], parts[1])
"""订阅房间解析工具：从楼栋+房间号推导各字段"""
from typing import Optional, Tuple

# 复用 Bot 版本的楼栋映射
BUILDINGS = [
    {
        "1东": 0, "1西": 1, "2东": 5, "2西": 6, "3北": 8, "3南": 9,
        "4东": 12, "4西": 13, "5北": 15, "5南": 16, "6东": 19, "6西": 20,
        "7北": 22, "7南": 23, "8东": 26, "8西": 27, "9北": 29, "9南": 30,
        "10北": 33, "10南": 34, "11北": 36, "11南": 37, "13": 39,
    },
    {
        "D1": 1, "D2": 2, "D3": 3, "D4东": 6, "D4西": 7, "D5": 8, "D6": 9,
        "D7东": 11, "D7西": 12, "D8": 13, "D9东": 14, "D9西": 15,
    },
]


class RoomParseError(ValueError):
    """房间解析异常"""


def _guess_area(building_name: str) -> int:
    """根据楼栋名判断校区 0=西区 1=东区"""
    return 1 if building_name.startswith("D") else 0


def parse_building_room(building_name: str, room_number: str) -> Tuple[str, str, str, str, str]:
    """
    输入楼栋名+房间号（如 D9东 + 425 或 10南 + 101），输出
    (room_name, area_id, building_code, floor_code, room_code)
    """
    if not building_name or not room_number:
        raise RoomParseError("楼栋或房间号不能为空")

    area_idx = _guess_area(building_name)
    if building_name not in BUILDINGS[area_idx]:
        raise RoomParseError(f"未知楼栋: {building_name}")

    room_number = room_number.strip()
    if not room_number.isdigit() or len(room_number) < 3:
        raise RoomParseError("房间号格式错误，应为数字，至少3位，例如 101/425")

    floor_code = room_number[0]  # 首位作为楼层
    room_code = room_number      # 完整房间编码

    room_name = f"{building_name} {room_number}"
    area_id = "1" if area_idx == 1 else "0"
    building_code = building_name

    return room_name, area_id, building_code, floor_code, room_code

