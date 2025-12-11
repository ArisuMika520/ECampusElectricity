from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlmodel import Session, select, func
from typing import List, Optional
from datetime import datetime
import uuid
from app.database import get_session
from app.models.user import User
from app.models.history import ElectricityHistory
from app.schemas.history import ElectricityHistoryResponse, HistoryStatsResponse
from app.services.subscription import SubscriptionService
from app.dependencies import get_current_user
from app.utils.timezone import to_shanghai_naive

router = APIRouter()


@router.get("/subscriptions/{subscription_id}", response_model=List[ElectricityHistoryResponse])
async def get_subscription_history(
    subscription_id: uuid.UUID,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    start_time: Optional[datetime] = None,
    end_time: Optional[datetime] = None,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    service = SubscriptionService(session)
    subscription = service.get_subscription(subscription_id, current_user.id)
    if not subscription:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Subscription not found"
        )
    
    statement = select(ElectricityHistory).where(
        ElectricityHistory.subscription_id == subscription_id
    )
    
    if start_time:
        statement = statement.where(ElectricityHistory.timestamp >= start_time)
    if end_time:
        statement = statement.where(ElectricityHistory.timestamp <= end_time)
    
    statement = statement.order_by(ElectricityHistory.timestamp.desc())
    statement = statement.offset(skip).limit(limit)
    
    history = list(session.exec(statement).all())
    for item in history:
        item.timestamp = to_shanghai_naive(item.timestamp)
        item.created_at = to_shanghai_naive(item.created_at)
    return history


@router.get("/stats/{subscription_id}", response_model=HistoryStatsResponse)
async def get_history_stats(
    subscription_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    service = SubscriptionService(session)
    subscription = service.get_subscription(subscription_id, current_user.id)
    if not subscription:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Subscription not found"
        )
    
    statement = select(
        func.count(ElectricityHistory.id).label("total"),
        func.max(ElectricityHistory.surplus).label("max_surplus"),
        func.min(ElectricityHistory.surplus).label("min_surplus"),
        func.avg(ElectricityHistory.surplus).label("avg_surplus"),
        func.max(ElectricityHistory.timestamp).label("latest_timestamp")
    ).where(ElectricityHistory.subscription_id == subscription_id)
    
    result = session.exec(statement).first()
    
    latest_statement = select(ElectricityHistory).where(
        ElectricityHistory.subscription_id == subscription_id
    ).order_by(ElectricityHistory.timestamp.desc()).limit(1)
    latest = session.exec(latest_statement).first()
    
    if not result or result[0] == 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No history data found"
        )
    
    return HistoryStatsResponse(
        subscription_id=subscription_id,
        total_records=result[0] or 0,
        latest_surplus=latest.surplus if latest else 0.0,
        latest_timestamp=to_shanghai_naive(latest.timestamp) if latest else to_shanghai_naive(datetime.utcnow()),
        min_surplus=float(result[2] or 0.0),
        max_surplus=float(result[1] or 0.0),
        avg_surplus=float(result[3] or 0.0)
    )



