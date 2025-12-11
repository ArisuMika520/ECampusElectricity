"""
楼栋索引映射表。
- 通过 get_building_index(area, building_name) 获取上游接口需要的楼栋索引。
"""

from typing import Dict

# 西区、东区楼栋映射
BUILDINGS = [
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


def get_building_index(area: int, building_name: str) -> int:
    """
    根据校区与楼栋名称获取索引。

    Args:
        area: 0 表示西区，1 表示东区
        building_name: 楼栋名称（如 10南、D9东）
    """
    return BUILDINGS[area][building_name]

