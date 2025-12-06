"""电费历史相关的 Pydantic 模式"""
from pydantic import BaseModel
from typing import Optional
from datetime import datetime
import uuid


class ElectricityHistoryResponse(BaseModel):
    """电费历史响应模式"""
    id: uuid.UUID
    subscription_id: uuid.UUID
    surplus: float
    timestamp: datetime
    created_at: datetime
    
    class Config:
        from_attributes = True


class HistoryStatsResponse(BaseModel):
    """历史统计响应模式"""
    subscription_id: uuid.UUID
    total_records: int
    latest_surplus: float
    latest_timestamp: datetime
    min_surplus: float
    max_surplus: float
    avg_surplus: float



