'''
实时监测Tracker（数据库版本）
从数据库读取订阅，查询电费并写入数据库历史记录
'''
import logging as pylog
import datetime
import sys
import os
import asyncio
import uuid
from pathlib import Path
from typing import Optional, Any, cast

# Ensure local packages are importable when running as a standalone script
BASE_DIR = Path(__file__).resolve().parent.parent
BOT_SRC_PATH = BASE_DIR / "Bot" / "src"
WEB_BACKEND_PATH = BASE_DIR / "Web" / "backend"

for path in (BOT_SRC_PATH, WEB_BACKEND_PATH):
    path_str = str(path)
    if path_str not in sys.path:
        sys.path.insert(0, path_str)

from core import Buildings
from bot.bot_command import ElectricityMonitor
from botpy.ext.cog_yaml import read  # type: ignore

from sqlmodel import Session, select, func
from sqlalchemy import desc, bindparam
from app.database import engine
from app.models.subscription import Subscription
from app.models.history import ElectricityHistory
from app.config import settings

# 配置日志记录器
pylog.basicConfig(
    level=pylog.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        pylog.FileHandler("tracker_log.log", encoding='utf-8'),  # 输出到文件
        pylog.StreamHandler()  # 同时输出到控制台
    ]
)

# --- 配置 ---

# 读取Bot配置文件
config = read(os.path.join(BASE_DIR, 'Bot', 'config.yaml'))
# 每次轮询之间的等待时间（秒）
WAIT_TIME = config.get("tracker", {}).get("check_interval", 3600)
# 数据上限（从Web后端配置读取）
HIS_LIMIT = settings.HISTORY_LIMIT if hasattr(settings, 'HISTORY_LIMIT') else 2400
# 时间字符串格式
TIME_FORMAT = "%Y-%m-%d %H:%M:%S"


def elect_require(target_name: str) -> float:
    """
    执行实际的查询操作。

    Args:
        target_name (str): 需要查询的目标名称（格式：楼栋 房间号，如 "10南 606"）。

    Returns:
        float: 查询到的电费余额。
    """
    pylog.info(f"开始为 '{target_name}' 执行查询...")
    
    parts = target_name.strip().split(' ')
    if len(parts) != 2:
        raise ValueError(f"查询 '{target_name}' 时参数数量不正确，应为2个（楼栋 房间号）")

    build_part = parts[0]
    room_part = parts[1]
    area = 1 if build_part.startswith('D') else 0

    buildIndex = Buildings.get_buildingIndex(area, build_part)
    floor = int(room_part[0]) - 1
    roomNum = int(room_part[1:]) - 1

    surplus, room_name = ElectricityMonitor.query_electricity(area, buildIndex, floor, roomNum)

    return surplus


def get_latest_history(session: Session, subscription_id: uuid.UUID) -> Optional[ElectricityHistory]:
    """获取订阅的最新历史记录"""
    timestamp_col = cast(Any, ElectricityHistory.timestamp)
    statement = select(ElectricityHistory).where(
        ElectricityHistory.subscription_id == subscription_id
    ).order_by(desc(timestamp_col)).limit(1)
    
    return session.exec(statement).first()


def should_add_history(session: Session, subscription_id: uuid.UUID, new_value: float) -> bool:
    """
    判断是否应该添加历史记录。
    如果上一次查询与本次电费相同，且时间差小于2小时，则不保存。
    """
    latest = get_latest_history(session, subscription_id)
    
    if not latest:
        return True
    
    # 如果值相同且时间差小于2小时，则不追加
    if latest.surplus == new_value:
        time_difference = datetime.datetime.utcnow() - latest.timestamp
        if time_difference < datetime.timedelta(hours=2):
            pylog.info(f"订阅 {subscription_id} 数据未变 (值: {new_value}) 且时间差小于2小时，跳过保存。")
            return False
    
    return True


def cleanup_old_history(session: Session, subscription_id: Optional[uuid.UUID]):
    """清理超出限制的旧历史记录"""
    if subscription_id is None:
        return
    sub_id: uuid.UUID = subscription_id
    sub_expr = bindparam("subscription_id", value=sub_id)
    id_col = cast(Any, ElectricityHistory.id)
    count_statement = select(func.count(id_col)).where(
        ElectricityHistory.subscription_id == sub_expr
    )
    count = session.exec(count_statement).first()
    
    if count and count > HIS_LIMIT:
        # 获取需要保留的记录（最新的）
        timestamp_col = cast(Any, ElectricityHistory.timestamp)
        keep_statement = cast(
            Any,
            select(ElectricityHistory).where(
                ElectricityHistory.subscription_id == sub_expr
            ).order_by(desc(timestamp_col)).limit(HIS_LIMIT),
        )
        
        keep_records = list(session.exec(keep_statement).all())
        keep_ids = {r.id for r in keep_records}
        
        all_statement = select(ElectricityHistory).where(
            ElectricityHistory.subscription_id == sub_expr
        )
        all_records = list(session.exec(all_statement).all())
        
        deleted = 0
        for record in all_records:
            if record.id not in keep_ids:
                session.delete(record)
                deleted += 1
        
        if deleted > 0:
            session.commit()
            pylog.info(f"订阅 {subscription_id} 历史数据超出数据上限，已删除 {deleted} 条旧记录")


async def main():
    """
    主函数，运行无限循环的定时查询任务。
    """
    pylog.info("正在初始化电费查询模块...")
    pylog.info("模块初始化成功。")

    while True:
        # 输出信息
        current_time_str = datetime.datetime.now().strftime(TIME_FORMAT)
        pylog.info(f"现在时间是 {current_time_str}，准备开始查询——")

        # 从数据库读取活跃订阅
        try:
            with Session(engine) as session:
                statement = select(Subscription).where(Subscription.is_active == True)
                subscriptions = list(session.exec(statement).all())
                pylog.info(f"成功从数据库读取订阅，共找到 {len(subscriptions)} 条活跃订阅。")
                
                if len(subscriptions) == 0:
                    pylog.warning(f"没有找到活跃订阅，将在 {WAIT_TIME} 秒后重试...")
                    await asyncio.sleep(WAIT_TIME)
                    continue

                # 对每个订阅进行查询并更新数据
                for subscription in subscriptions:
                    try:
                        if subscription.id is None:
                            pylog.warning(f"订阅 {subscription.room_name} 缺少 ID，已跳过。")
                            continue
                        sub_id: uuid.UUID = cast(uuid.UUID, subscription.id)

                        # 执行查询
                        new_value = elect_require(subscription.room_name)
                        
                        # 获取当前时间作为记录时间
                        record_time = datetime.datetime.utcnow()
                        
                        # 判断是否需要添加历史记录
                        if should_add_history(session, sub_id, new_value):
                            # 创建历史记录
                            history = ElectricityHistory(
                                subscription_id=sub_id,
                                surplus=new_value,
                                timestamp=record_time
                            )
                            session.add(history)
                            session.commit()
                            pylog.info(f"房间 {subscription.room_name} (ID: {sub_id}) 得到新数据，值: {new_value}, 时间: {record_time.strftime(TIME_FORMAT)}")
                        else:
                            pylog.info(f"房间 {subscription.room_name} (ID: {sub_id}) 数据未变化，跳过保存")
                        
                        # 清理旧的历史记录
                        cleanup_old_history(session, sub_id)
                        
                    except Exception as e:
                        pylog.error(f"处理房间 '{subscription.room_name}' (ID: {getattr(subscription, 'id', None)}) 时发生错误，已跳过。错误详情: {e}")
                        continue
                
                pylog.info(f"所有订阅房间已查询完毕，数据已写入数据库。")

        except Exception as e:
            pylog.error(f"数据库操作失败: {e}")
            pylog.info(f"将在 {WAIT_TIME} 秒后重试...")
            await asyncio.sleep(WAIT_TIME)
            continue

        # 等待
        pylog.info(f"本轮查询结束，程序将休眠 {WAIT_TIME} 秒。")
        now = datetime.datetime.now()
        next_run_time = now + datetime.timedelta(seconds=WAIT_TIME)
        next_run_time_str = next_run_time.strftime(TIME_FORMAT)
        pylog.info(f"下一次查询预计将于 {next_run_time_str} 进行。\n" + 30 * "-")
        await asyncio.sleep(WAIT_TIME)


if __name__ == "__main__":
    pylog.info("启动电费追踪器（数据库版本）...")
    pylog.info(f"数据库连接: {settings.DATABASE_URL}")
    pylog.info(f"查询间隔: {WAIT_TIME} 秒")
    pylog.info(f"历史记录上限: {HIS_LIMIT} 条")
    
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n程序被用户中断。")
        pylog.info("程序被用户中断。")

