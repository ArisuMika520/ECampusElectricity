from fastapi import APIRouter, Depends, Query
from sqlmodel import Session, select
from typing import List, Optional
from datetime import datetime
from app.database import get_session
from app.models.user import User
from app.models.log import Log
from app.schemas.log import LogResponse
from app.dependencies import get_current_user
from app.utils.timezone import to_shanghai_naive

router = APIRouter()


@router.get("", response_model=List[LogResponse])
async def get_logs(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    level: Optional[str] = None,
    module: Optional[str] = None,
    start_time: Optional[datetime] = None,
    end_time: Optional[datetime] = None,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    statement = select(Log)
    
    if level:
        statement = statement.where(Log.level == level.upper())
    if module:
        statement = statement.where(Log.module == module)
    if start_time:
        statement = statement.where(Log.timestamp >= start_time)
    if end_time:
        statement = statement.where(Log.timestamp <= end_time)
    
    statement = statement.order_by(Log.timestamp.desc())
    statement = statement.offset(skip).limit(limit)
    
    logs = list(session.exec(statement).all())
    result = []
    for log in logs:
        timestamp = log.timestamp if log.timestamp else datetime.utcnow()
        log_dict = {
            "id": log.id,
            "level": log.level,
            "message": log.message,
            "module": log.module,
            "timestamp": to_shanghai_naive(timestamp)
        }
        result.append(LogResponse(**log_dict))
    return result

