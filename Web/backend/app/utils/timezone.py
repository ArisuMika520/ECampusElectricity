"""时间相关的辅助函数"""
from datetime import datetime, timezone
from zoneinfo import ZoneInfo


def now_utc() -> datetime:
    """返回当前 UTC 时间（带 tzinfo）"""
    return datetime.now(timezone.utc)


def now_naive() -> datetime:
    """返回当前 UTC 时间的 naive 版本，用于数据库默认值"""
    return datetime.utcnow().replace(tzinfo=None)


def to_shanghai_naive(dt: datetime | None) -> datetime | None:
    """
    将给定时间转换为上海时区的 naive 时间。
    - 支持 tz-aware 和 naive（默认按 UTC 解释）输入
    """
    if dt is None:
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    sh_tz = ZoneInfo("Asia/Shanghai")
    return dt.astimezone(sh_tz).replace(tzinfo=None)
