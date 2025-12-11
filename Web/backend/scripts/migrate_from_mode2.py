"""
从 Bot 版本迁移数据到 PostgreSQL 的脚本。
"""
import json
import os
import sys
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any

sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlmodel import Session, select
from app.database import engine, init_db
from app.models.user import User
from app.models.subscription import Subscription
from app.models.history import ElectricityHistory
from app.models.config import Config
from app.utils.auth import get_password_hash


def load_json_file(filepath: str) -> Any:
    """加载 JSON 文件。"""
    if not os.path.exists(filepath):
        print(f"警告: 文件 {filepath} 不存在")
        return []
    
    with open(filepath, 'r', encoding='utf-8') as f:
        return json.load(f)


def create_default_user(session: Session) -> User:
    """创建默认用户用于迁移。"""
    statement = select(User).where(User.username == "migrated_user")
    existing_user = session.exec(statement).first()
    
    if existing_user:
        print("默认用户已存在，使用现有用户")
        return existing_user
    
    user = User(
        username="migrated_user",
        email="migrated@example.com",
        hashed_password=get_password_hash("changeme"),
        is_active=True
    )
    session.add(user)
    session.commit()
    session.refresh(user)
    print(f"已创建默认用户: {user.username} (ID: {user.id})")
    return user


def migrate_subscriptions(
    session: Session,
    user: User,
    sub_list: List[str],
    sub_his: List[Dict[str, Any]]
) -> Dict[str, str]:
    """从 JSON 迁移订阅数据到数据库。返回房间名到订阅ID的映射。"""
    room_to_subscription = {}
    
    for room_name in sub_list:
        history_data = next((item for item in sub_his if item.get('name') == room_name), None)
        
        if not history_data:
            print(f"警告: 房间 {room_name} 未找到历史数据，跳过")
            continue
        
        parts = room_name.strip().split(' ')
        if len(parts) != 2:
            print(f"警告: 无效的房间名格式: {room_name}，跳过")
            continue
        
        area_id = "1" if parts[0].startswith('D') else "0"
        building_code = parts[0]
        floor_code = "1"
        room_code = parts[1]
        
        if len(room_code) >= 3:
            try:
                floor_num = int(room_code[0])
                floor_code = str(floor_num)
            except ValueError:
                pass
        
        statement = select(Subscription).where(
            Subscription.user_id == user.id,
            Subscription.room_name == room_name
        )
        existing = session.exec(statement).first()
        
        if existing:
            print(f"房间 {room_name} 的订阅已存在，跳过")
            room_to_subscription[room_name] = str(existing.id)
            continue
        
        subscription = Subscription(
            user_id=user.id,
            room_name=room_name,
            area_id=area_id,
            building_code=building_code,
            floor_code=floor_code,
            room_code=room_code,
            threshold=20.0,
            email_recipients=[],
            is_active=True
        )
        session.add(subscription)
        session.commit()
        session.refresh(subscription)
        
        room_to_subscription[room_name] = str(subscription.id)
        print(f"已创建房间 {room_name} 的订阅 (ID: {subscription.id})")
    
    return room_to_subscription


def migrate_history(
    session: Session,
    room_to_subscription: Dict[str, str],
    sub_his: List[Dict[str, Any]]
):
    """从 JSON 迁移历史数据到数据库。"""
    for history_item in sub_his:
        room_name = history_item.get('name')
        if not room_name:
            continue
        
        subscription_id = room_to_subscription.get(room_name)
        if not subscription_id:
            print(f"警告: 房间 {room_name} 未找到订阅，跳过历史数据")
            continue
        
        history_records = history_item.get('his', [])
        
        for record in history_records:
            timestamp_str = record.get('timestamp')
            value = record.get('value')
            
            if not timestamp_str or value is None:
                continue
            
            try:
                timestamp = datetime.strptime(timestamp_str, "%Y-%m-%d %H:%M:%S")
            except ValueError:
                try:
                    timestamp = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
                except ValueError:
                    print(f"警告: 无效的时间戳格式: {timestamp_str}，跳过")
                    continue
            
            statement = select(ElectricityHistory).where(
                ElectricityHistory.subscription_id == subscription_id,
                ElectricityHistory.timestamp == timestamp,
                ElectricityHistory.surplus == float(value)
            )
            existing = session.exec(statement).first()
            
            if existing:
                continue
            
            history = ElectricityHistory(
                subscription_id=subscription_id,
                surplus=float(value),
                timestamp=timestamp
            )
            session.add(history)
        
        session.commit()
        print(f"已迁移房间 {room_name} 的 {len(history_records)} 条历史记录")


def main():
    """主迁移函数。"""
    print("开始从 Bot 版本迁移数据到 PostgreSQL...")
    
    init_db()
    
    bot_base = Path(__file__).parent.parent.parent.parent / "Bot"
    sub_file = bot_base / "data_files" / "sub.json"
    his_file = bot_base / "data_files" / "his.json"
    
    if not sub_file.exists():
        print(f"错误: 未找到订阅文件: {sub_file}")
        return
    
    if not his_file.exists():
        print(f"错误: 未找到历史文件: {his_file}")
        return
    
    print("正在加载 JSON 文件...")
    sub_list = load_json_file(str(sub_file))
    sub_his = load_json_file(str(his_file))
    
    print(f"找到 {len(sub_list)} 个订阅和 {len(sub_his)} 条历史记录")
    
    with Session(engine) as session:
        user = create_default_user(session)
        
        print("\n正在迁移订阅...")
        room_to_subscription = migrate_subscriptions(session, user, sub_list, sub_his)
        
        print("\n正在迁移历史数据...")
        migrate_history(session, room_to_subscription, sub_his)
        
        print("\n迁移完成！")
        print(f"\n默认用户凭据:")
        print(f"  用户名: migrated_user")
        print(f"  密码: changeme")
        print(f"\n请首次登录后立即修改密码！")


if __name__ == "__main__":
    main()
