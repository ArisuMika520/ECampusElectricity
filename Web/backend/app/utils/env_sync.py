"""同步配置到 .env 的工具"""
import os
from typing import Dict
from dotenv import dotenv_values


ENV_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), ".env")


def read_env_file() -> Dict[str, str]:
    """读取 .env 文件为字典；不存在时返回空字典"""
    if not os.path.exists(ENV_PATH):
        return {}
    return dotenv_values(ENV_PATH)  # type: ignore


def sync_config_to_env(key: str, value) -> None:
    """将配置写入 .env（覆盖或追加），仅在应用侧使用，简单实现"""
    os.makedirs(os.path.dirname(ENV_PATH), exist_ok=True)
    env_data = read_env_file()
    env_data[key] = str(value)

    lines = [f"{k}={v}" for k, v in env_data.items()]
    with open(ENV_PATH, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
