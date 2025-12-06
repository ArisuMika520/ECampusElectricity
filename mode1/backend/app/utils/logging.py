"""自定义日志配置：支持数据库和 WebSocket"""
import logging
import sys
from typing import List, Optional
from datetime import datetime
from app.models.log import Log
from sqlmodel import Session
from app.database import engine


class DatabaseLogHandler(logging.Handler):
    """写入数据库的日志处理器"""
    
    def __init__(self, session: Optional[Session] = None):
        super().__init__()
        self.session = session
    
    def emit(self, record: logging.LogRecord):
        """将日志记录写入数据库"""
        try:
            log_entry = Log(
                level=record.levelname,
                message=self.format(record),
                module=record.module if hasattr(record, 'module') else None,
                timestamp=datetime.utcnow()
            )
            if self.session:
                self.session.add(log_entry)
                self.session.commit()
            else:
                with Session(engine) as session:
                    session.add(log_entry)
                    session.commit()
        except Exception:
            pass


class WebSocketLogHandler(logging.Handler):
    """向 WebSocket 连接广播的日志处理器"""
    
    def __init__(self):
        super().__init__()
        self.connections: List = []
    
    def add_connection(self, websocket):
        """添加 WebSocket 连接"""
        self.connections.append(websocket)
    
    def remove_connection(self, websocket):
        """移除 WebSocket 连接"""
        if websocket in self.connections:
            self.connections.remove(websocket)
    
    def emit(self, record: logging.LogRecord):
        """向所有 WebSocket 连接发送日志记录"""
        try:
            message = {
                "level": record.levelname,
                "message": self.format(record),
                "module": record.module if hasattr(record, 'module') else None,
                "timestamp": datetime.utcnow().isoformat()
            }
            
            disconnected = []
            for conn in self.connections:
                try:
                    if hasattr(conn, '_message_queue'):
                        conn._message_queue.append(message)
                except Exception:
                    disconnected.append(conn)
            
            for conn in disconnected:
                self.remove_connection(conn)
        except Exception:
            pass


websocket_log_handler = WebSocketLogHandler()


def setup_logging(log_level: str = "INFO", log_file: Optional[str] = None):
    """
    设置日志配置
    
    Args:
        log_level: 日志级别 (DEBUG, INFO, WARNING, ERROR)
        log_file: 可选的日志文件路径
    """
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, log_level.upper()))
    
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)
    
    if log_file:
        import os
        os.makedirs(os.path.dirname(log_file), exist_ok=True)
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setFormatter(formatter)
        root_logger.addHandler(file_handler)
    
    db_handler = DatabaseLogHandler()
    db_handler.setFormatter(formatter)
    root_logger.addHandler(db_handler)
    
    websocket_log_handler.setFormatter(formatter)
    root_logger.addHandler(websocket_log_handler)
    
    return root_logger

