"""使用 APScheduler 的任务调度器"""
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from sqlmodel import Session
from app.database import get_session
from app.services.tracker import TrackerService
from app.config import settings
import logging

logger = logging.getLogger(__name__)

scheduler = AsyncIOScheduler()


def start_scheduler():
    """启动任务调度器"""
    if scheduler.running:
        logger.warning("Scheduler is already running")
        return
    scheduler.add_job(
        check_subscriptions_job,
        trigger=IntervalTrigger(seconds=settings.TRACKER_CHECK_INTERVAL),
        id='check_subscriptions',
        name='Check all active subscriptions',
        replace_existing=True
    )
    
    scheduler.start()
    logger.info(f"Scheduler started with interval: {settings.TRACKER_CHECK_INTERVAL} seconds")


def stop_scheduler():
    """停止任务调度器"""
    if scheduler.running:
        scheduler.shutdown()
        logger.info("Scheduler stopped")


def check_subscriptions_job():
    """检查所有订阅的任务函数"""
    try:
        session_gen = get_session()
        session = next(session_gen)
        
        try:
            tracker = TrackerService(session)
            tracker.check_all_subscriptions()
        finally:
            session.close()
    except Exception as e:
        logger.error(f"Error in check_subscriptions_job: {e}")



