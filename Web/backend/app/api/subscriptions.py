from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, select, func
from typing import List
import uuid
from datetime import datetime, timedelta
from app.database import get_session
from app.models.user import User
from app.models.subscription import Subscription
from app.schemas.subscription import SubscriptionCreate, SubscriptionUpdate, SubscriptionResponse
from app.services.subscription import SubscriptionService
from app.services.electricity import ElectricityService
from app.dependencies import get_current_user
from app.models.user_subscription import UserSubscription
from app.models.history import ElectricityHistory
from app.utils.timezone import to_shanghai_naive, now_naive
from app.utils.room_parser import RoomParseError
from app.config import settings

router = APIRouter()


@router.get("", response_model=List[SubscriptionResponse])
async def get_subscriptions(
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    service = SubscriptionService(session)
    subscriptions = service.get_user_subscriptions(current_user.id, include_all=current_user.is_admin)
    results: List[SubscriptionResponse] = []
    for sub in subscriptions:
        mapping_stmt = select(UserSubscription).where(
            UserSubscription.subscription_id == sub.id,
            UserSubscription.user_id == current_user.id
        )
        mapping = session.exec(mapping_stmt).first()
        is_owner = current_user.is_admin or (bool(mapping.is_owner) if mapping else False)

        latest_stmt = (
            select(ElectricityHistory)
            .where(ElectricityHistory.subscription_id == sub.id)
            .order_by(ElectricityHistory.timestamp.desc())
            .limit(1)
        )
        latest = session.exec(latest_stmt).first()
        current_surplus = float(latest.surplus) if latest else None
        last_query_time = to_shanghai_naive(latest.timestamp) if latest else None

        results.append(
            SubscriptionResponse(
                **sub.model_dump(),
                is_owner=is_owner,
                current_surplus=current_surplus,
                last_query_time=last_query_time,
                email_recipient_count=len(sub.email_recipients or []),
            )
        )
    return results


@router.post("", response_model=SubscriptionResponse, status_code=status.HTTP_201_CREATED)
async def create_subscription(
    subscription_data: SubscriptionCreate,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    service = SubscriptionService(session)
    try:
        subscription = service.create_subscription(current_user.id, subscription_data)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except RoomParseError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    
    mapping_stmt = select(UserSubscription).where(
        UserSubscription.subscription_id == subscription.id,
        UserSubscription.user_id == current_user.id
    )
    mapping = session.exec(mapping_stmt).first()
    is_owner = bool(mapping.is_owner) if mapping else False
    return SubscriptionResponse(**subscription.model_dump(), is_owner=is_owner)


@router.get("/{subscription_id}", response_model=SubscriptionResponse)
async def get_subscription(
    subscription_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    service = SubscriptionService(session)
    subscription = service.get_subscription(subscription_id, current_user.id, is_admin=current_user.is_admin)
    if not subscription:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Subscription not found"
        )
    is_owner = current_user.is_admin
    if not is_owner:
        mapping_stmt = select(UserSubscription).where(
            UserSubscription.subscription_id == subscription.id,
            UserSubscription.user_id == current_user.id
        )
        mapping = session.exec(mapping_stmt).first()
        is_owner = bool(mapping.is_owner) if mapping else False
    return SubscriptionResponse(**subscription.model_dump(), is_owner=is_owner)


@router.put("/{subscription_id}", response_model=SubscriptionResponse)
async def update_subscription(
    subscription_id: uuid.UUID,
    subscription_data: SubscriptionUpdate,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    service = SubscriptionService(session)
    subscription = service.update_subscription(
        subscription_id, current_user.id, subscription_data, is_admin=current_user.is_admin
    )
    if not subscription:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Subscription not found"
        )
    is_owner = current_user.is_admin
    if not is_owner:
        mapping_stmt = select(UserSubscription).where(
            UserSubscription.subscription_id == subscription.id,
            UserSubscription.user_id == current_user.id
        )
        mapping = session.exec(mapping_stmt).first()
        is_owner = bool(mapping.is_owner) if mapping else False
    return SubscriptionResponse(**subscription.model_dump(), is_owner=is_owner)


@router.delete("/{subscription_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_subscription(
    subscription_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    service = SubscriptionService(session)
    success = service.delete_subscription(subscription_id, current_user.id, is_admin=current_user.is_admin)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Subscription not found"
        )

@router.post("/{subscription_id}/query")
async def query_subscription(
    subscription_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    service = SubscriptionService(session)
    subscription = service.get_subscription(subscription_id, current_user.id, is_admin=current_user.is_admin)
    if not subscription:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Subscription not found"
        )

    owner_stmt = (
        select(UserSubscription)
        .where(UserSubscription.subscription_id == subscription.id)
        .order_by(UserSubscription.is_owner.desc(), UserSubscription.created_at.asc())
    )
    mapping = session.exec(owner_stmt).first()
    target_user_id = str(mapping.user_id) if mapping else str(subscription.user_id or current_user.id)

    electricity_service = ElectricityService(session, target_user_id)
    room_info = electricity_service.query_room_surplus_by_room_name(subscription.room_name)

    if room_info.get("error") != 0:
        try:
            cfg = electricity_service._get_ece_instance().config  # type: ignore
            sj = cfg.get("shiroJID", "")
            masked = f"{len(sj)} chars" if sj else "empty"
        except Exception:
            masked = "unknown"
        import logging
        logging.getLogger(__name__).warning(
            "Electricity query failed: %s (shiroJID=%s)", room_info, masked
        )
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail={
                "error": room_info.get("error"),
                "message": room_info.get("error_description", "Query failed"),
                "raw": room_info,
            },
        )

    surplus = float(room_info["data"]["surplus"])
    timestamp = now_naive()  # 使用上海时间

    latest_stmt = (
        select(ElectricityHistory)
        .where(ElectricityHistory.subscription_id == subscription.id)
        .order_by(ElectricityHistory.timestamp.desc())
        .limit(1)
    )
    latest = session.exec(latest_stmt).first()
    should_add = True
    if latest and latest.surplus == surplus:
        if timestamp - latest.timestamp < timedelta(hours=2):
            should_add = False

    if should_add:
        history = ElectricityHistory(
            subscription_id=subscription.id,
            surplus=surplus,
            timestamp=timestamp
        )
        session.add(history)
        session.commit()
    else:
        session.rollback()

    count_stmt = select(func.count(ElectricityHistory.id)).where(
        ElectricityHistory.subscription_id == subscription.id
    )
    count = session.exec(count_stmt).first()
    if count and count > settings.HISTORY_LIMIT:
        keep_stmt = (
            select(ElectricityHistory)
            .where(ElectricityHistory.subscription_id == subscription.id)
            .order_by(ElectricityHistory.timestamp.desc())
            .limit(settings.HISTORY_LIMIT)
        )
        keep_ids = {r.id for r in session.exec(keep_stmt).all()}
        all_stmt = select(ElectricityHistory).where(ElectricityHistory.subscription_id == subscription.id)
        for record in session.exec(all_stmt).all():
            if record.id not in keep_ids:
                session.delete(record)
        session.commit()

    return {
        "surplus": surplus,
        "room_name": room_info["data"].get("roomName"),
        "added_history": should_add,
        "timestamp": timestamp.isoformat() + "Z"
    }


@router.post("/{subscription_id}/test")
async def test_subscription(
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
    
    electricity_service = ElectricityService(session, str(current_user.id))
    result = electricity_service.query_room_surplus_by_room_name(subscription.room_name)
    return result



