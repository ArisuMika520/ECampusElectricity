from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, select
from typing import List
import uuid
from app.database import get_session
from app.models.user import User
from app.models.config import Config
from app.schemas.config import ConfigResponse, ConfigUpdate
from app.utils.timezone import now_naive
from app.dependencies import get_current_user
from app.utils.env_sync import read_env_file, sync_config_to_env

router = APIRouter()


@router.get("", response_model=List[ConfigResponse])
async def get_configs(
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    statement = select(Config).where(Config.user_id == current_user.id)
    configs = list(session.exec(statement).all())
    
    env_vars = read_env_file()
    config_keys_in_db = {c.key for c in configs}
    
    env_to_config_mapping = {
        'SHIRO_JID': 'shiroJID',
        'SMTP_SERVER': 'smtp_server',
        'SMTP_PORT': 'smtp_port',
        'SMTP_USER': 'smtp_user',
        'SMTP_PASS': 'smtp_pass',
        'FROM_EMAIL': 'from_email',
        'USE_TLS': 'use_tls',
    }
    
    for env_key, config_key in env_to_config_mapping.items():
        if config_key not in config_keys_in_db and env_key in env_vars:
            env_value = env_vars[env_key]
            if env_key == 'SMTP_PORT':
                try:
                    env_value = int(env_value)
                except:
                    env_value = 465
            elif env_key == 'USE_TLS':
                env_value = env_value.lower() in ('true', '1', 'yes')
            
            from app.schemas.config import ConfigResponse
            configs.append(ConfigResponse(
                id=uuid.uuid4(),
                user_id=current_user.id,
                key=config_key,
                value={"value": env_value},
                updated_at=now_naive()
            ))
    
    return configs


@router.get("/{key}", response_model=ConfigResponse)
async def get_config(
    key: str,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    statement = select(Config).where(Config.key == key)
    config = session.exec(statement).first()
    
    if not config:
        env_vars = read_env_file()
        env_to_config_mapping = {
            'SHIRO_JID': 'shiroJID',
            'SMTP_SERVER': 'smtp_server',
            'SMTP_PORT': 'smtp_port',
            'SMTP_USER': 'smtp_user',
            'SMTP_PASS': 'smtp_pass',
            'FROM_EMAIL': 'from_email',
            'USE_TLS': 'use_tls',
        }
        
        config_to_env_mapping = {v: k for k, v in env_to_config_mapping.items()}
        env_key = config_to_env_mapping.get(key)
        
        if env_key and env_key in env_vars:
            env_value = env_vars[env_key]
            if env_key == 'SMTP_PORT':
                try:
                    env_value = int(env_value)
                except:
                    env_value = 465
            elif env_key == 'USE_TLS':
                env_value = env_value.lower() in ('true', '1', 'yes')
            
            return ConfigResponse(
                id=uuid.uuid4(),
                user_id=current_user.id,
                key=key,
                value={"value": env_value},
                updated_at=now_naive()
            )
        
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
    statement = select(Config).where(Config.key == key)
    config = session.exec(statement).first()
    
    actual_value = config_data.value
    if isinstance(actual_value, dict):
        actual_value = actual_value.get('value', actual_value)
    
    if config:
        config.value = config_data.value
        config.updated_at = now_naive()
        config.user_id = current_user.id
    else:
        config = Config(
            user_id=current_user.id,
            key=key,
            value=config_data.value,
            updated_at=now_naive()
        )
        session.add(config)
    
    session.commit()
    session.refresh(config)
    
    try:
        sync_config_to_env(key, actual_value)
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.warning(f"Failed to sync config {key} to .env: {e}")
    
    return config


