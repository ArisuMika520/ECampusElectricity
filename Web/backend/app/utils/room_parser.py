from typing import Dict
import re

BUILDING_INDEX = [
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
    pass


def parse_building_room(building: str, room_number: str) -> Dict[str, str]:
    if not building or not room_number:
        raise RoomParseError("楼栋与房间号均不能为空")

    building_code = building.strip()
    room_code = room_number.strip()
    area_id = "1" if building_code.startswith("D") else "0"

    floor_code = room_code[0] if room_code else ""
    if not floor_code.isdigit():
        raise RoomParseError("房间号格式不正确，首位应为楼层数字")

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
    if not room_name:
        raise RoomParseError("房间名不能为空")
    parts = room_name.strip().split()
    building = None
    room_number = None
    if len(parts) == 2:
        building, room_number = parts
    elif len(parts) == 1:
        m = re.match(r"^(.+?)(\d{3,4})$", parts[0])
        if m:
            building, room_number = m.group(1), m.group(2)
    if not building or not room_number:
        raise RoomParseError("房间名格式应为 '楼栋 房间号'，例如 D9东 425")
    return parse_building_room(building, room_number)

