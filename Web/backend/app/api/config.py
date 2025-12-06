"""配置管理 API 路由"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, select
from typing import List, Dict, Any
from datetime import datetime
import uuid
from app.database import get_session
from app.models.user import User
from app.models.config import Config
from app.schemas.config import ConfigResponse, ConfigUpdate
from app.dependencies import get_current_user

router = APIRouter()


@router.get("", response_model=List[ConfigResponse])
async def get_configs(
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """获取当前用户的所有配置"""
    statement = select(Config).where(Config.user_id == current_user.id)
    configs = list(session.exec(statement).all())
    return configs


@router.get("/{key}", response_model=ConfigResponse)
async def get_config(
    key: str,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """获取指定配置"""
    statement = select(Config).where(
        Config.key == key,
        Config.user_id == current_user.id
    )
    config = session.exec(statement).first()
    if not config:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Configuration not found"
        )
    return config


@router.put("/{key}", response_model=ConfigResponse)
async def update_config(
    key: str,
    config_data: ConfigUpdate,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """更新或创建配置"""
    statement = select(Config).where(
        Config.key == key,
        Config.user_id == current_user.id
    )
    config = session.exec(statement).first()
    
    if config:
        config.value = config_data.value
        config.updated_at = datetime.utcnow()
    else:
        config = Config(
            user_id=current_user.id,
            key=key,
            value=config_data.value,
            updated_at=datetime.utcnow()
        )
        session.add(config)
    
    session.commit()
    session.refresh(config)
    return config


@router.delete("/{key}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_config(
    key: str,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """删除配置"""
    statement = select(Config).where(
        Config.key == key,
        Config.user_id == current_user.id
    )
    config = session.exec(statement).first()
    if not config:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Configuration not found"
        )
    
    session.delete(config)
    session.commit()



