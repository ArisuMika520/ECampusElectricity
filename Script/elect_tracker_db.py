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
import warnings
from pathlib import Path
from typing import Optional, Any, cast, Dict, List, Tuple
from zoneinfo import ZoneInfo
from dataclasses import dataclass, field
from enum import Enum

# 禁用urllib3的InsecureRequestWarning警告
# 因为xiaofubao.com的API服务器可能没有有效的SSL证书，我们需要禁用SSL验证
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
warnings.filterwarnings('ignore', message='Unverified HTTPS request')

BASE_DIR = Path(__file__).resolve().parent.parent
WEB_BACKEND_PATH = BASE_DIR / "Web" / "backend"

# 只需要添加 Web Backend 路径
if str(WEB_BACKEND_PATH) not in sys.path:
    sys.path.insert(0, str(WEB_BACKEND_PATH))

from sqlmodel import Session, select, func
from sqlalchemy import desc, bindparam
from app.database import engine
from app.models.subscription import Subscription
from app.models.history import ElectricityHistory
from app.config import settings
from app.core.electricity import ECampusElectricity
from app.core.buildings import get_building_index

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

# 从统一配置读取
WAIT_TIME = settings.TRACKER_CHECK_INTERVAL
HIS_LIMIT = settings.HISTORY_LIMIT
TIME_FORMAT = "%Y-%m-%d %H:%M:%S"
SHANGHAI_TZ = ZoneInfo("Asia/Shanghai")

# 重查机制配置
RETRY_INTERVAL_SECONDS = 60  # 重试间隔：1分钟
MAX_RETRY_COUNT = 3  # 最大重试次数：3次
RETRY_DELAY_AFTER_NORMAL_QUERY = 300  # 正常查询轮次结束后等待5分钟再重查
RETRY_LOG_RETENTION_DAYS = 7  # 重试日志保留7天


class ErrorType(Enum):
    """错误类型枚举"""
    NETWORK_ERROR = "network_error"  # 网络问题
    API_ERROR = "api_error"  # 抓包查询失败（API错误）
    PARAMETER_ERROR = "parameter_error"  # 参数错误（房间名格式无效等，不应重试）


@dataclass
class RetryRecord:
    """重查记录"""
    subscription_id: uuid.UUID
    room_name: str
    error_type: ErrorType
    error_message: str
    first_fail_time: datetime.datetime
    retry_count: int = 0
    last_retry_time: Optional[datetime.datetime] = None
    retry_logs: List[Tuple[datetime.datetime, str, bool]] = field(default_factory=list)  # (时间, 错误信息, 是否成功)


class RetryQueue:
    """重查队列管理器"""
    
    def __init__(self):
        self.queue: Dict[uuid.UUID, RetryRecord] = {}
    
    def add_failed_subscription(
        self,
        subscription_id: uuid.UUID,
        room_name: str,
        error_type: ErrorType,
        error_message: str
    ):
        """添加失败的订阅到重查队列"""
        if subscription_id in self.queue:
            record = self.queue[subscription_id]
            record.error_type = error_type
            record.error_message = error_message
            record.last_retry_time = get_shanghai_time()
            pylog.warning(f"订阅 {room_name} (ID: {subscription_id}) 已在重查队列中，更新错误信息")
        else:
            record = RetryRecord(
                subscription_id=subscription_id,
                room_name=room_name,
                error_type=error_type,
                error_message=error_message,
                first_fail_time=get_shanghai_time()
            )
            self.queue[subscription_id] = record
            pylog.warning(f"订阅 {room_name} (ID: {subscription_id}) 查询失败，已加入重查队列。错误类型: {error_type.value}, 错误信息: {error_message}")
    
    def get_ready_for_retry(self) -> List[RetryRecord]:
        """获取可以重试的记录（达到重试间隔）"""
        current_time = get_shanghai_time()
        ready_records = []
        
        for record in self.queue.values():
            if record.last_retry_time is None:
                time_since_last = current_time - record.first_fail_time
            else:
                time_since_last = current_time - record.last_retry_time
            
            if time_since_last >= datetime.timedelta(seconds=RETRY_INTERVAL_SECONDS) and record.retry_count < MAX_RETRY_COUNT:
                ready_records.append(record)
        
        return ready_records
    
    def mark_retry_success(self, subscription_id: uuid.UUID, message: str = ""):
        """标记重试成功，从队列移除"""
        if subscription_id in self.queue:
            record = self.queue.pop(subscription_id)
            retry_time = get_shanghai_time()
            record.retry_logs.append((retry_time, message or "重试成功", True))
            pylog.info(f"订阅 {record.room_name} (ID: {subscription_id}) 重试成功，已从重查队列移除。共重试 {record.retry_count} 次")
            self._save_retry_log(record)
    
    def mark_retry_failed(self, subscription_id: uuid.UUID, error_message: str):
        """标记重试失败，增加重试次数"""
        if subscription_id in self.queue:
            record = self.queue[subscription_id]
            record.retry_count += 1
            record.last_retry_time = get_shanghai_time()
            retry_time = get_shanghai_time()
            record.retry_logs.append((retry_time, error_message, False))
            
            if record.retry_count >= MAX_RETRY_COUNT:
                self.queue.pop(subscription_id)
                pylog.error(f"订阅 {record.room_name} (ID: {subscription_id}) 已达到最大重试次数 ({MAX_RETRY_COUNT})，已从重查队列移除")
                self._save_retry_log(record)
            else:
                pylog.warning(f"订阅 {record.room_name} (ID: {subscription_id}) 第 {record.retry_count} 次重试失败: {error_message}")
    
    def clear_all(self):
        """清空队列（当所有记录都处理完成时）"""
        if self.queue:
            pylog.info(f"清空重查队列，共 {len(self.queue)} 条记录")
            for record in list(self.queue.values()):
                self._save_retry_log(record)
            self.queue.clear()
    
    def is_empty(self) -> bool:
        """检查队列是否为空"""
        return len(self.queue) == 0
    
    def _save_retry_log(self, record: RetryRecord):
        """保存重试日志到文件（保留最近一周）"""
        log_file = Path("tracker_retry_log.log")
        current_time = get_shanghai_time()
        
        existing_logs = []
        if log_file.exists():
            try:
                with open(log_file, 'r', encoding='utf-8') as f:
                    for line in f:
                        if line.strip():
                            try:
                                parts = line.split(' | ', 5)
                                if len(parts) >= 2:
                                    log_time_str = parts[0]
                                    log_time = datetime.datetime.strptime(log_time_str, TIME_FORMAT)
                                    log_time = log_time.replace(tzinfo=SHANGHAI_TZ)
                                    if (current_time - log_time).days < RETRY_LOG_RETENTION_DAYS:
                                        existing_logs.append(line)
                            except Exception:
                                existing_logs.append(line)
            except Exception as e:
                pylog.warning(f"读取重试日志文件失败: {e}")
        
        for retry_time, message, success in record.retry_logs:
            status = "成功" if success else "失败"
            log_line = (
                f"{retry_time.strftime(TIME_FORMAT)} | "
                f"{record.subscription_id} | "
                f"{record.room_name} | "
                f"第{record.retry_count}次重试 | "
                f"{record.error_type.value} | "
                f"{status} | "
                f"{message}\n"
            )
            existing_logs.append(log_line)
        
        try:
            with open(log_file, 'w', encoding='utf-8') as f:
                f.writelines(existing_logs)
        except Exception as e:
            pylog.warning(f"写入重试日志文件失败: {e}")


retry_queue = RetryQueue()

# 初始化电费查询服务
electricity_service = ECampusElectricity({
    "shiroJID": settings.SHIRO_JID or "",
    "floor_offset_file": None
})


def get_shanghai_time() -> datetime.datetime:
    """获取上海时区的当前时间（带时区信息）"""
    return datetime.datetime.now(SHANGHAI_TZ)


def elect_require(target_name: str) -> Tuple[float, Optional[ErrorType], Optional[str]]:
    """
    执行实际的查询操作。

    Args:
        target_name (str): 需要查询的目标名称（格式：楼栋 房间号，如 "10南 606"）。

    Returns:
        Tuple[float, Optional[ErrorType], Optional[str]]: 
            - 成功时返回 (电费余额, None, None)
            - 失败时返回 (0.0, ErrorType, 错误信息)
    """
    pylog.info(f"开始为 '{target_name}' 执行查询...")
    
    parts = target_name.strip().split(' ')
    if len(parts) != 2:
        error_msg = f"查询 '{target_name}' 时参数数量不正确，应为2个（楼栋 房间号）"
        return (0.0, ErrorType.PARAMETER_ERROR, error_msg)  # 参数错误，不重试

    build_part = parts[0]
    room_part = parts[1]
    area = 1 if build_part.startswith('D') else 0

    building_idx = get_building_index(area, build_part)
    floor = int(room_part[0]) - 1
    room_num = int(room_part[1:]) - 1

    try:
        result = electricity_service.query_room_surplus_by_human(
            area_index=area,
            building_name=build_part,
            floor_number=int(room_part[0]),
            room_number=int(room_part)
        )
        
        if result.get("exception"):
            error_msg = f"网络错误: {result.get('exception', '未知网络错误')}"
            return (0.0, ErrorType.NETWORK_ERROR, error_msg)
        
        if result.get("error") == 0:
            return (result["data"]["surplus"], None, None)
        else:
            error_msg = result.get("error_description", "未知错误")
            return (0.0, ErrorType.API_ERROR, error_msg)
    
    except Exception as e:
        error_msg = f"查询异常: {str(e)}"
        if "timeout" in str(e).lower() or "connection" in str(e).lower() or "network" in str(e).lower():
            return (0.0, ErrorType.NETWORK_ERROR, error_msg)
        else:
            return (0.0, ErrorType.API_ERROR, error_msg)



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
    
    if latest.surplus == new_value:
        current_time = get_shanghai_time()
        if latest.timestamp.tzinfo is None:
            latest_time = latest.timestamp.replace(tzinfo=SHANGHAI_TZ)
        else:
            latest_time = latest.timestamp.astimezone(SHANGHAI_TZ)
        
        time_difference = current_time - latest_time
        if time_difference < datetime.timedelta(hours=2):
            pylog.info(f"订阅 {subscription_id} 数据未变 (值: {new_value}) 且时间差小于2小时，跳过保存。")
            return False
    
    return True


async def process_retry_queue():
    """
    处理重查队列中的失败订阅
    注意：此函数内部会创建自己的数据库会话，避免长时间持有连接
    """
    if not retry_queue.queue:
        return
    
    pylog.info(f"开始处理重查队列，共 {len(retry_queue.queue)} 个失败的订阅")
    
    max_iterations = 100  # 防止无限循环
    iteration = 0
    
    while retry_queue.queue and iteration < max_iterations:
        iteration += 1
        ready_records = retry_queue.get_ready_for_retry()
        
        if not ready_records:
            if retry_queue.queue:
                min_wait_time = RETRY_INTERVAL_SECONDS
                current_time = get_shanghai_time()
                
                for record in retry_queue.queue.values():
                    if record.last_retry_time is None:
                        time_since_last = current_time - record.first_fail_time
                    else:
                        time_since_last = current_time - record.last_retry_time
                    
                    remaining = RETRY_INTERVAL_SECONDS - time_since_last.total_seconds()
                    if remaining > 0 and remaining < min_wait_time:
                        min_wait_time = int(remaining) + 1
                
                if min_wait_time < RETRY_INTERVAL_SECONDS:
                    pylog.info(f"等待 {min_wait_time} 秒后继续重查...")
                    await asyncio.sleep(min_wait_time)
                    continue
            break
        
        # 重试批次创建新的数据库会话
        with Session(engine) as session:
            for record in ready_records:
                try:
                    pylog.info(f"重试查询订阅 {record.room_name} (ID: {record.subscription_id})，第 {record.retry_count + 1} 次重试")
                    
                    new_value, error_type, error_message = elect_require(record.room_name)
                    
                    if error_type is None:
                        record_time = get_shanghai_time().replace(tzinfo=None)
                        
                        if should_add_history(session, record.subscription_id, new_value):
                            history = ElectricityHistory(
                                subscription_id=record.subscription_id,
                                surplus=new_value,
                                timestamp=record_time
                            )
                            session.add(history)
                            session.commit()
                            pylog.info(f"房间 {record.room_name} (ID: {record.subscription_id}) 重试成功，得到新数据，值: {new_value}, 时间: {record_time.strftime(TIME_FORMAT)}")
                        else:
                            pylog.info(f"房间 {record.room_name} (ID: {record.subscription_id}) 重试成功，但数据未变化，跳过保存")
                        
                        cleanup_old_history(session, record.subscription_id)
                        
                        retry_queue.mark_retry_success(
                            record.subscription_id,
                            f"重试成功，电费余额: {new_value}"
                        )
                    else:
                        retry_queue.mark_retry_failed(
                            record.subscription_id,
                            f"{error_type.value}: {error_message}"
                        )
                        
                except Exception as e:
                    error_msg = f"重试异常: {str(e)}"
                    pylog.error(f"重试订阅 {record.room_name} (ID: {record.subscription_id}) 时发生异常: {e}")
                    retry_queue.mark_retry_failed(record.subscription_id, error_msg)
        
        await asyncio.sleep(1)
    
    if retry_queue.is_empty():
        pylog.info("重查队列已清空，所有失败的订阅都已处理完成")
    else:
        remaining_count = len(retry_queue.queue)
        pylog.info(f"重查队列处理完成，仍有 {remaining_count} 个订阅待重试（可能已达到最大重试次数，将在下次正常查询后继续重试）")


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
        current_time_str = get_shanghai_time().strftime(TIME_FORMAT)
        pylog.info(f"现在时间是 {current_time_str}，准备开始查询——")

        try:
            with Session(engine) as session:
                statement = select(Subscription).where(Subscription.is_active == True)
                subscriptions = list(session.exec(statement).all())
                pylog.info(f"成功从数据库读取订阅，共找到 {len(subscriptions)} 条活跃订阅。")
                
                if len(subscriptions) == 0:
                    pylog.warning(f"没有找到活跃订阅，将在 {WAIT_TIME} 秒后重试...")
                    await asyncio.sleep(WAIT_TIME)
                    continue

                for subscription in subscriptions:
                    try:
                        if subscription.id is None:
                            pylog.warning(f"订阅 {subscription.room_name} 缺少 ID，已跳过。")
                            continue
                        sub_id: uuid.UUID = cast(uuid.UUID, subscription.id)

                        # 执行查询
                        new_value, error_type, error_message = elect_require(subscription.room_name)
                        
                        # 查询失败，处理错误
                        if error_type is not None:
                            if error_type == ErrorType.PARAMETER_ERROR:
                                pylog.error(f"订阅 {subscription.room_name} (ID: {sub_id}) 参数错误，跳过处理: {error_message}")
                                continue
                            
                            retry_queue.add_failed_subscription(
                                subscription_id=sub_id,
                                room_name=subscription.room_name,
                                error_type=error_type,
                                error_message=error_message or "未知错误"
                            )
                            continue
                        
                        # 查询成功，处理数据
                        record_time = get_shanghai_time().replace(tzinfo=None)
                        
                        if should_add_history(session, sub_id, new_value):
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
                        if subscription.id:
                            retry_queue.add_failed_subscription(
                                subscription_id=cast(uuid.UUID, subscription.id),
                                room_name=subscription.room_name,
                                error_type=ErrorType.NETWORK_ERROR,
                                error_message=f"未知异常: {str(e)}"
                            )
                        continue
                
                pylog.info(f"所有订阅房间已查询完毕，数据已写入数据库。")
            
            if not retry_queue.is_empty():
                pylog.info(f"发现 {len(retry_queue.queue)} 个失败的订阅，将在 {RETRY_DELAY_AFTER_NORMAL_QUERY} 秒后开始重查...")
                await asyncio.sleep(RETRY_DELAY_AFTER_NORMAL_QUERY)
                
                await process_retry_queue()

        except Exception as e:
            pylog.error(f"数据库操作失败: {e}")
            pylog.info(f"将在 {WAIT_TIME} 秒后重试...")
            await asyncio.sleep(WAIT_TIME)
            continue

        # 等待
        pylog.info(f"本轮查询结束，程序将休眠 {WAIT_TIME} 秒。")
        now = get_shanghai_time()
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

