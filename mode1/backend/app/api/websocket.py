"""WebSocket API 路由：实时日志流"""
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from app.utils.logging import websocket_log_handler
import logging
import asyncio
from collections import deque

router = APIRouter()
logger = logging.getLogger(__name__)


@router.websocket("/logs")
async def websocket_logs(websocket: WebSocket):
    """WebSocket 端点：实时日志流"""
    await websocket.accept()
    
    message_queue = deque()
    websocket._message_queue = message_queue
    websocket_log_handler.add_connection(websocket)
    logger.info("WebSocket connection established for log streaming")
    
    async def send_messages():
        """后台任务：发送队列中的消息"""
        while True:
            if message_queue:
                try:
                    message = message_queue.popleft()
                    await websocket.send_json(message)
                except Exception as e:
                    logger.error(f"Error sending message: {e}")
                    break
            await asyncio.sleep(0.1)
    
    send_task = asyncio.create_task(send_messages())
    
    try:
        while True:
            try:
                data = await websocket.receive_text()
                await websocket.send_json({"type": "ack", "message": "received"})
            except Exception as e:
                logger.error(f"Error in websocket loop: {e}")
                break
    except WebSocketDisconnect:
        send_task.cancel()
        websocket_log_handler.remove_connection(websocket)
        logger.info("WebSocket connection closed")
    except Exception as e:
        send_task.cancel()
        logger.error(f"WebSocket error: {e}")
        websocket_log_handler.remove_connection(websocket)
