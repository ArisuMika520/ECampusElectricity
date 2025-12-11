"""订阅管理 API 路由"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, select
from typing import List
import uuid
from app.database import get_session
from app.models.user import User
from app.models.subscription import Subscription
from app.schemas.subscription import SubscriptionCreate, SubscriptionUpdate, SubscriptionResponse
from app.services.subscription import SubscriptionService
from app.services.electricity import ElectricityService
from app.dependencies import get_current_user
from app.models.user_subscription import UserSubscription
from app.utils.room_parser import RoomParseError

router = APIRouter()


@router.get("", response_model=List[SubscriptionResponse])
async def get_subscriptions(
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """获取当前用户的所有订阅；管理员可查看全部"""
    service = SubscriptionService(session)
    subscriptions = service.get_user_subscriptions(current_user.id, include_all=current_user.is_admin)
    results: List[SubscriptionResponse] = []
    for sub in subscriptions:
        mapping_stmt = select(UserSubscription).where(
            UserSubscription.subscription_id == sub.id,
            UserSubscription.user_id == current_user.id
        )
        mapping = session.exec(mapping_stmt).first()
        is_owner = bool(mapping.is_owner) if mapping else current_user.is_admin
        results.append(
            SubscriptionResponse(
                **sub.model_dump(),
                is_owner=is_owner,
            )
        )
    return results


@router.post("", response_model=SubscriptionResponse, status_code=status.HTTP_201_CREATED)
async def create_subscription(
    subscription_data: SubscriptionCreate,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """创建新订阅；若已存在则直接共享给当前用户"""
    service = SubscriptionService(session)
    try:
        subscription = service.create_subscription(current_user.id, subscription_data)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except RoomParseError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    # 重新查询映射以返回 is_owner
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
    """获取指定订阅"""
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
    """更新订阅"""
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
    """删除订阅"""
    service = SubscriptionService(session)
    success = service.delete_subscription(subscription_id, current_user.id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Subscription not found"
        )


@router.post("/{subscription_id}/test")
async def test_subscription(
    subscription_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """测试查询订阅的电费"""
    service = SubscriptionService(session)
    subscription = service.get_subscription(subscription_id, current_user.id)
    if not subscription:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Subscription not found"
        )
    
    electricity_service = ElectricityService(session, str(current_user.id))
    result = electricity_service.query_room_surplus(
        subscription.area_id,
        subscription.building_code,
        subscription.floor_code,
        subscription.room_code
    )
    return result



