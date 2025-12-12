"""
配置桥接工具
从统一的 .env 文件生成 Bot 所需的 config.yaml
"""
import os
import sys
from pathlib import Path
from typing import Dict, Any
import yaml

# 添加 backend 路径以使用统一配置
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "Web" / "backend"))

from app.config import settings


def generate_bot_config() -> Dict[str, Any]:
    """从 .env 配置生成 Bot config.yaml 内容"""
    config = {
        "qq": {
            "appid": settings.QQ_APPID or "",
            "secret": settings.QQ_SECRET or ""
        },
        "electricity": {
            "api_endpoint": settings.API_BASE_URL,
            "default_threshold": 20.0,
            "shiroJID": settings.SHIRO_JID or ""
        },
        "tracker": {
            "check_interval": settings.TRACKER_CHECK_INTERVAL,
            "his_limit": settings.HISTORY_LIMIT
        },
        "path": {
            "SUBSCRIPTION_LIST_FILE": "data_files/sub.json",
            "SUBSCRIPTION_HISTORY_FILE": "data_files/his.json",
            "TIME_FORMAT": "%Y-%m-%d %H:%M:%S",
            "PLOT_DIR": "data_files/plot",
            "UPLOAD_RECORD_FILE": "data_files/image_upload_records.json",
            "FLOOR_OFFSET_FILE": ""
        },
        "uploader": {
            "token": settings.UPLOADER_TOKEN or "",
            "album_id": settings.UPLOADER_ALBUM_ID or ""
        }
    }
    return config


def sync_bot_config():
    """同步配置到 Bot/config.yaml"""
    bot_config_path = PROJECT_ROOT / "Bot" / "config.yaml"
    
    # 生成配置
    config = generate_bot_config()
    
    # 写入文件
    with open(bot_config_path, 'w', encoding='utf-8') as f:
        yaml.dump(config, f, allow_unicode=True, default_flow_style=False, sort_keys=False)
    
    print(f"✓ Bot 配置已同步到: {bot_config_path}")
    print(f"  - QQ AppID: {'已配置' if settings.QQ_APPID else '未配置'}")
    print(f"  - SHIRO_JID: {'已配置' if settings.SHIRO_JID else '未配置'}")
    print(f"  - Tracker 间隔: {settings.TRACKER_CHECK_INTERVAL}秒")


if __name__ == "__main__":
    print("从统一配置文件同步 Bot 配置...")
    print(f"配置源: {PROJECT_ROOT}/.env")
    sync_bot_config()
