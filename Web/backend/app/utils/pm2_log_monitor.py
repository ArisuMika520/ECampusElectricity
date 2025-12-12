"""PM2日志监控器：读取PM2日志文件并推送到WebSocket和数据库"""
import asyncio
import os
from pathlib import Path
from typing import Dict, Optional
from datetime import datetime, timedelta
import logging
from app.utils.logging import websocket_log_handler
from app.utils.timezone import now_naive
from app.models.log import Log
from app.database import engine
from sqlmodel import Session, select

logger = logging.getLogger(__name__)

# PM2日志文件路径（相对于项目根目录）
# 从 Web/backend/app/utils/ 向上五级到项目根目录
# Web/backend/app/utils/pm2_log_monitor.py -> Web/backend/app/utils/ -> Web/backend/app/ -> Web/backend/ -> Web/ -> 项目根目录
PM2_LOG_DIR = Path(__file__).resolve().parent.parent.parent.parent.parent / "logs" / "pm2"

# 要监控的PM2日志文件（只监控这三个服务）
PM2_LOG_FILES = {
    "web-backend": ["web-backend.log", "web-backend-error.log", "web-backend-out.log"],
    "web-frontend": ["web-frontend.log", "web-frontend-error.log", "web-frontend-out.log"],
    "tracker": ["tracker.log", "tracker-error.log", "tracker-out.log"],
}

# 进程颜色映射（用于前端显示）
PROCESS_COLORS = {
    "web-backend": "blue",      # 蓝色
    "web-frontend": "green",    # 绿色
    "tracker": "yellow",        # 黄色
}


class PM2LogMonitor:
    """PM2日志文件监控器"""
    
    def __init__(self):
        self.file_positions: Dict[str, int] = {}
        self.running = False
        self.monitor_task: Optional[asyncio.Task] = None
        self.cleanup_task: Optional[asyncio.Task] = None
        self.last_cleanup_time: Optional[datetime] = None
    
    def parse_pm2_log_line(self, line: str, source: str) -> Optional[dict]:
        """
        解析PM2日志行
        
        PM2日志格式示例：
        2025-01-12 19:02:03 +08:00: [INFO] Some message
        或
        2025-01-12 19:02:03 +08:00: Some message
        或（没有时间戳）
        Some message
        """
        line = line.strip()
        if not line:
            return None
        
        timestamp_str = None
        message = line
        level = "INFO"
        
        # 尝试解析PM2时间戳格式：YYYY-MM-DD HH:mm:ss Z
        # 例如：2025-01-12 19:02:03 +08:00: message
        if len(line) >= 19 and line[4] == '-' and line[7] == '-' and line[10] == ' ':
            try:
                # PM2日志格式：2025-01-12 19:02:03 +08:00: message
                # 查找第一个冒号后的空格（时间戳结束位置）
                # 格式：YYYY-MM-DD HH:mm:ss +HH:MM: message
                colon_pos = line.find(':', 19)  # 从第19个字符开始查找冒号（时间部分）
                if colon_pos > 0:
                    # 提取时间戳部分
                    timestamp_part = line[:colon_pos].strip()
                    message = line[colon_pos + 1:].strip()
                    
                    # 尝试解析时间戳
                    try:
                        # PM2格式：2025-01-12 19:02:03 +08:00
                        # 移除时区部分进行解析
                        if ' ' in timestamp_part and len(timestamp_part) > 19:
                            dt_str = timestamp_part[:19]  # 取前19个字符（日期和时间部分）
                            dt = datetime.strptime(dt_str, "%Y-%m-%d %H:%M:%S")
                            timestamp_str = dt.isoformat()
                    except ValueError:
                        pass
            except Exception:
                pass
        
        # 尝试从消息中提取日志级别
        message_upper = message.upper()
        if message_upper.startswith("[ERROR]") or message_upper.startswith("ERROR:"):
            level = "ERROR"
            message = message.replace("[ERROR]", "").replace("ERROR:", "").strip()
        elif message_upper.startswith("[WARN]") or message_upper.startswith("[WARNING]") or message_upper.startswith("WARN:") or message_upper.startswith("WARNING:"):
            level = "WARNING"
            message = message.replace("[WARN]", "").replace("[WARNING]", "").replace("WARN:", "").replace("WARNING:", "").strip()
        elif message_upper.startswith("[DEBUG]") or message_upper.startswith("DEBUG:"):
            level = "DEBUG"
            message = message.replace("[DEBUG]", "").replace("DEBUG:", "").strip()
        elif message_upper.startswith("[INFO]") or message_upper.startswith("INFO:"):
            level = "INFO"
            message = message.replace("[INFO]", "").replace("INFO:", "").strip()
        
        # 如果消息为空，使用原始行
        if not message:
            message = line
        
        # 提取服务名称（用于颜色标识）
        service_name = source.split('.')[0] if '.' in source else source
        
        return {
            "level": level,
            "message": message,
            "module": f"pm2.{source}",
            "timestamp": timestamp_str or now_naive().isoformat(),
            "process": service_name,  # 添加进程名称用于前端颜色区分
        }
    
    async def read_new_lines(self, file_path: Path, source: str):
        """读取文件的新行"""
        if not file_path.exists():
            return
        
        file_key = str(file_path)
        current_position = self.file_positions.get(file_key, 0)
        
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                # 移动到上次读取的位置
                f.seek(current_position)
                
                # 读取新行
                new_lines = f.readlines()
                
                # 更新位置
                self.file_positions[file_key] = f.tell()
                
                # 处理新行
                for line in new_lines:
                    log_entry = self.parse_pm2_log_line(line, source)
                    if log_entry:
                        # 推送到WebSocket
                        try:
                            message = {
                                "level": log_entry["level"],
                                "message": log_entry["message"],
                                "module": log_entry["module"],
                                "timestamp": log_entry["timestamp"],
                                "process": log_entry.get("process", "unknown"),  # 添加进程名称
                            }
                            
                            # 添加到所有WebSocket连接的消息队列
                            disconnected = []
                            for conn in websocket_log_handler.connections:
                                try:
                                    if hasattr(conn, '_message_queue'):
                                        conn._message_queue.append(message)
                                except Exception:
                                    disconnected.append(conn)
                            
                            # 移除断开的连接
                            for conn in disconnected:
                                websocket_log_handler.remove_connection(conn)
                        except Exception as e:
                            logger.debug(f"Failed to send PM2 log to WebSocket: {e}")
                        
                        # 写入数据库（用于历史日志查询）
                        try:
                            self.save_to_database(log_entry)
                        except Exception as e:
                            logger.debug(f"Failed to save PM2 log to database: {e}")
        except Exception as e:
            logger.debug(f"Failed to read PM2 log file {file_path}: {e}")
    
    def save_to_database(self, log_entry: dict):
        """将PM2日志保存到数据库"""
        try:
            timestamp_str = log_entry.get("timestamp")
            if isinstance(timestamp_str, str):
                try:
                    # 处理ISO格式时间戳
                    if 'T' in timestamp_str:
                        timestamp = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
                    else:
                        timestamp = datetime.fromisoformat(timestamp_str)
                except:
                    timestamp = now_naive()
            else:
                timestamp = now_naive()
            
            log_db = Log(
                level=log_entry["level"],
                message=log_entry["message"],
                module=log_entry["module"],
                timestamp=timestamp
            )
            
            with Session(engine) as session:
                session.add(log_db)
                session.commit()
        except Exception as e:
            logger.debug(f"Failed to save PM2 log to database: {e}")
    
    def cleanup_old_logs(self, session: Session):
        """清理超过30天的旧日志（批量清理，避免频繁操作）"""
        try:
            # 每小时清理一次
            now = datetime.utcnow()
            if self.last_cleanup_time and (now - self.last_cleanup_time).total_seconds() < 3600:
                return
            
            cutoff = now - timedelta(days=30)
            stmt = select(Log).where(Log.timestamp < cutoff)
            old_logs = list(session.exec(stmt).all())
            if old_logs:
                for log_entry in old_logs:
                    session.delete(log_entry)
                session.commit()
                self.last_cleanup_time = now
                logger.info(f"Cleaned up {len(old_logs)} old log entries (older than 30 days)")
        except Exception as e:
            logger.debug(f"Failed to cleanup old logs: {e}")
    
    async def cleanup_loop(self):
        """定期清理旧日志的后台任务"""
        while self.running:
            try:
                await asyncio.sleep(3600)  # 每小时执行一次
                if self.running:
                    try:
                        with Session(engine) as session:
                            self.cleanup_old_logs(session)
                    except Exception as e:
                        logger.error(f"Error in cleanup loop: {e}")
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in cleanup loop: {e}")
                await asyncio.sleep(3600)
    
    async def monitor_loop(self):
        """监控循环"""
        logger.info("PM2 log monitor started")
        
        while self.running:
            try:
                # 遍历所有要监控的日志文件
                for service_name, log_files in PM2_LOG_FILES.items():
                    for log_file in log_files:
                        file_path = PM2_LOG_DIR / log_file
                        source = f"{service_name}.{log_file.replace('.log', '')}"
                        await self.read_new_lines(file_path, source)
                
                # 等待1秒后再次检查
                await asyncio.sleep(1)
            except Exception as e:
                logger.error(f"Error in PM2 log monitor loop: {e}")
                await asyncio.sleep(5)
    
    def start(self):
        """启动监控器"""
        if self.running:
            logger.warning("PM2 log monitor is already running")
            return
        
        # 检查日志目录是否存在，如果不存在则创建
        if not PM2_LOG_DIR.exists():
            try:
                PM2_LOG_DIR.mkdir(parents=True, exist_ok=True)
                logger.info(f"Created PM2 log directory: {PM2_LOG_DIR}")
            except Exception as e:
                logger.warning(f"PM2 log directory does not exist and cannot be created: {PM2_LOG_DIR}, error: {e}")
                logger.info("PM2 log monitor will not start. Create the directory to enable PM2 log monitoring.")
                return
        
        self.running = True
        
        # 初始化文件位置（从文件末尾开始读取，只读取新日志）
        for service_name, log_files in PM2_LOG_FILES.items():
            for log_file in log_files:
                file_path = PM2_LOG_DIR / log_file
                file_key = str(file_path)
                if file_path.exists():
                    try:
                        # 从文件末尾开始读取（只读取新日志）
                        self.file_positions[file_key] = file_path.stat().st_size
                    except Exception:
                        self.file_positions[file_key] = 0
                else:
                    # 文件不存在时，位置设为0，等待文件创建
                    self.file_positions[file_key] = 0
                    logger.debug(f"PM2 log file does not exist yet: {file_path}, will monitor for creation")
        
        # 启动监控任务（在当前的asyncio事件循环中）
        try:
            loop = asyncio.get_running_loop()
            self.monitor_task = loop.create_task(self.monitor_loop())
            self.cleanup_task = loop.create_task(self.cleanup_loop())
        except RuntimeError:
            # 如果没有运行中的事件循环，创建一个新的
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            self.monitor_task = loop.create_task(self.monitor_loop())
            self.cleanup_task = loop.create_task(self.cleanup_loop())
        
        logger.info("PM2 log monitor started successfully")
    
    def stop(self):
        """停止监控器"""
        if not self.running:
            return
        
        self.running = False
        if self.monitor_task:
            self.monitor_task.cancel()
        if self.cleanup_task:
            self.cleanup_task.cancel()
        logger.info("PM2 log monitor stopped")


# 全局监控器实例
pm2_log_monitor = PM2LogMonitor()

