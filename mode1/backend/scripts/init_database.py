"""
Database initialization script.
Run this script to create all database tables.
"""
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.database import init_db, engine
from app.models import User, Subscription, ElectricityHistory, Config, Log
from sqlmodel import SQLModel
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def main():
    """Initialize database by creating all tables."""
    try:
        logger.info("开始初始化数据库...")
        logger.info(f"数据库连接: {engine.url}")
        
        # Create all tables
        SQLModel.metadata.create_all(engine)
        
        logger.info("✓ 数据库表创建成功！")
        logger.info("已创建的表:")
        logger.info("  - users (用户表)")
        logger.info("  - subscriptions (订阅表)")
        logger.info("  - electricity_history (历史数据表)")
        logger.info("  - config (配置表)")
        logger.info("  - logs (日志表)")
        logger.info("")
        logger.info("数据库初始化完成！")
        
    except Exception as e:
        logger.error(f"数据库初始化失败: {e}")
        logger.error("请检查:")
        logger.error("  1. PostgreSQL 服务是否运行")
        logger.error("  2. 数据库 electricity_db 是否已创建")
        logger.error("  3. .env 文件中的 DATABASE_URL 配置是否正确")
        sys.exit(1)


if __name__ == "__main__":
    main()



