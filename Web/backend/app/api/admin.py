"""管理员 API 路由：用户管理和系统配置"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, select
from typing import List, Dict, Any
import uuid
from app.database import get_session
from app.models.user import User
from app.models.config import Config
from app.schemas.admin import UserCreate, UserUpdate, SystemConfigUpdate, UserResponse as AdminUserResponse
from app.utils.auth import get_password_hash, verify_password
from app.dependencies import get_current_user
from datetime import datetime
from app.config import settings

router = APIRouter()


def require_admin(current_user: User = Depends(get_current_user)) -> User:
    """要求管理员权限的依赖项"""
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin privileges required"
        )
    return current_user


@router.get("/users", response_model=List[AdminUserResponse])
async def list_users(
    current_user: User = Depends(require_admin),
    session: Session = Depends(get_session)
):
    """获取所有用户列表（仅管理员）"""
    statement = select(User)
    users = list(session.exec(statement).all())
    return users


@router.post("/users", response_model=AdminUserResponse, status_code=status.HTTP_201_CREATED)
async def create_user(
    user_data: UserCreate,
    current_user: User = Depends(require_admin),
    session: Session = Depends(get_session)
):
    """创建新用户（仅管理员）"""
    statement = select(User).where(User.username == user_data.username)
    existing_user = session.exec(statement).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already exists"
        )
    
    statement = select(User).where(User.email == user_data.email)
    existing_user = session.exec(statement).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already exists"
        )
    
    hashed_password = get_password_hash(user_data.password)
    user = User(
        username=user_data.username,
        email=user_data.email,
        hashed_password=hashed_password,
        is_active=user_data.is_active,
        is_admin=user_data.is_admin
    )
    session.add(user)
    session.commit()
    session.refresh(user)
    
    return user


@router.put("/users/{user_id}", response_model=AdminUserResponse)
async def update_user(
    user_id: uuid.UUID,
    user_data: UserUpdate,
    current_user: User = Depends(require_admin),
    session: Session = Depends(get_session)
):
    """更新用户信息（仅管理员）"""
    statement = select(User).where(User.id == user_id)
    user = session.exec(statement).first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # 防止管理员移除自己的管理员权限
    if user.id == current_user.id and user_data.is_admin is False:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot remove your own admin privileges"
        )
    
    if user_data.email is not None:
        email_statement = select(User).where(User.email == user_data.email, User.id != user_id)
        existing = session.exec(email_statement).first()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already exists"
            )
        user.email = user_data.email
    
    if user_data.password is not None:
        user.hashed_password = get_password_hash(user_data.password)
    
    if user_data.is_admin is not None:
        user.is_admin = user_data.is_admin
    
    if user_data.is_active is not None:
        user.is_active = user_data.is_active
    
    user.updated_at = datetime.utcnow()
    session.add(user)
    session.commit()
    session.refresh(user)
    
    return user


@router.delete("/users/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(
    user_id: uuid.UUID,
    current_user: User = Depends(require_admin),
    session: Session = Depends(get_session)
):
    """删除用户（仅管理员）"""
    # 防止管理员删除自己的账号
    if user_id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete your own account"
        )
    
    statement = select(User).where(User.id == user_id)
    user = session.exec(statement).first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    session.delete(user)
    session.commit()


@router.get("/system/config")
async def get_system_config(
    current_user: User = Depends(require_admin),
    session: Session = Depends(get_session)
):
    """获取系统配置（仅管理员）"""
    statement = select(Config).where(Config.key == "allow_registration")
    config = session.exec(statement).first()
    
    allow_registration = False
    if config and config.value.get("value") is True:
        allow_registration = True
    
    return {
        "allow_registration": allow_registration
    }


@router.put("/system/config")
async def update_system_config(
    config_data: SystemConfigUpdate,
    current_user: User = Depends(require_admin),
    session: Session = Depends(get_session)
):
    """更新系统配置（仅管理员）"""
    statement = select(Config).where(Config.key == "allow_registration")
    config = session.exec(statement).first()
    
    if config:
        config.value = {"value": config_data.allow_registration}
        config.updated_at = datetime.utcnow()
    else:
        config = Config(
            key="allow_registration",
            value={"value": config_data.allow_registration},
            updated_at=datetime.utcnow()
        )
        session.add(config)
    
    session.commit()
    session.refresh(config)
    
    return {
        "allow_registration": config_data.allow_registration
    }


ENV_KEYS = [
    "SMTP_SERVER",
    "SMTP_PORT",
    "SMTP_USER",
    "SMTP_PASS",
    "FROM_EMAIL",
    "SHIRO_JID",
]


@router.get("/env", response_model=Dict[str, Any])
async def get_env_settings(
    current_user: User = Depends(require_admin),
    session: Session = Depends(get_session)
):
    """获取当前运行时 Settings（仅管理员），并合并数据库覆盖项"""
    data = {k: v for k, v in settings.model_dump().items() if k in ENV_KEYS}
    override_stmt = select(Config).where(Config.key == "env_overrides")
    override_cfg = session.exec(override_stmt).first()
    if override_cfg:
        overrides = {k: v for k, v in (override_cfg.value or {}).items() if k in ENV_KEYS}
        data.update(overrides)
    return data


@router.put("/env", response_model=Dict[str, Any])
async def update_env_settings(
    payload: Dict[str, Any],
    current_user: User = Depends(require_admin),
    session: Session = Depends(get_session)
):
    """更新 Settings 覆盖项（仅管理员）。写入数据库，需重启后生效。"""
    overrides = {k: v for k, v in payload.items() if k in ENV_KEYS}

    stmt = select(Config).where(Config.key == "env_overrides")
    cfg = session.exec(stmt).first()
    if cfg:
        cfg.value = overrides
        cfg.updated_at = datetime.utcnow()
    else:
        cfg = Config(
            key="env_overrides",
            value=overrides,
            updated_at=datetime.utcnow()
        )
        session.add(cfg)
    session.commit()
    session.refresh(cfg)
    return overrides



