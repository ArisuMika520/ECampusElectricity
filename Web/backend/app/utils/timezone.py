"""时间相关的辅助函数"""
from datetime import datetime, timezone
from zoneinfo import ZoneInfo

# 上海时区
SHANGHAI_TZ = ZoneInfo("Asia/Shanghai")


def now_utc() -> datetime:
    """返回当前 UTC 时间（带 tzinfo）"""
    return datetime.now(timezone.utc)


def now_naive() -> datetime:
    """返回当前上海时间的 naive 版本，用于数据库默认值"""
    return datetime.now(SHANGHAI_TZ).replace(tzinfo=None)


def to_shanghai_naive(dt: datetime | None) -> datetime | None:
    """
    将给定时间转换为上海时区的 naive 时间。
    - 如果输入是 tz-aware 时间，转换为上海时间
    - 如果输入是 naive 时间，假设它已经是上海时间（数据库中存储的都是上海时间），直接返回
    """
    if dt is None:
        return None
    if dt.tzinfo is None:
        # 数据库中存储的时间已经是上海时间的 naive 版本，直接返回
        return dt
    # 如果是 tz-aware 时间，转换为上海时间
    return dt.astimezone(SHANGHAI_TZ).replace(tzinfo=None)
