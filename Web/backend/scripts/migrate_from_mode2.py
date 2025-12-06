"""
Migration script to import data from Bot version JSON files to PostgreSQL.
"""
import json
import os
import sys
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlmodel import Session, select
from app.database import engine, init_db
from app.models.user import User
from app.models.subscription import Subscription
from app.models.history import ElectricityHistory
from app.models.config import Config
from app.utils.auth import get_password_hash


def load_json_file(filepath: str) -> Any:
    """Load JSON file."""
    if not os.path.exists(filepath):
        print(f"Warning: File {filepath} does not exist")
        return []
    
    with open(filepath, 'r', encoding='utf-8') as f:
        return json.load(f)


def create_default_user(session: Session) -> User:
    """Create a default user for migration."""
    # Check if default user exists
    statement = select(User).where(User.username == "migrated_user")
    existing_user = session.exec(statement).first()
    
    if existing_user:
        print("Default user already exists, using existing user")
        return existing_user
    
    # Create new default user
    user = User(
        username="migrated_user",
        email="migrated@example.com",
        hashed_password=get_password_hash("changeme"),
        is_active=True
    )
    session.add(user)
    session.commit()
    session.refresh(user)
    print(f"Created default user: {user.username} (ID: {user.id})")
    return user


def migrate_subscriptions(
    session: Session,
    user: User,
    sub_list: List[str],
    sub_his: List[Dict[str, Any]]
) -> Dict[str, str]:
    """
    Migrate subscriptions from JSON to database.
    
    Returns:
        Dictionary mapping room_name to subscription_id
    """
    room_to_subscription = {}
    
    for room_name in sub_list:
        # Find history for this room
        history_data = next((item for item in sub_his if item.get('name') == room_name), None)
        
        if not history_data:
            print(f"Warning: No history found for room {room_name}, skipping")
            continue
        
        # Parse room name to extract area, building, floor, room
        # Format: "D9东 425" or "10南 606"
        parts = room_name.strip().split(' ')
        if len(parts) != 2:
            print(f"Warning: Invalid room name format: {room_name}, skipping")
            continue
        
        # For now, we'll use placeholder values
        # In production, you might want to parse these from the room name
        area_id = "1" if parts[0].startswith('D') else "0"
        building_code = parts[0]
        floor_code = "1"  # Default, should be parsed from room number
        room_code = parts[1]
        
        # Extract floor from room number (e.g., "425" -> floor "4")
        if len(room_code) >= 3:
            try:
                floor_num = int(room_code[0])
                floor_code = str(floor_num)
            except ValueError:
                pass
        
        # Check if subscription already exists
        statement = select(Subscription).where(
            Subscription.user_id == user.id,
            Subscription.room_name == room_name
        )
        existing = session.exec(statement).first()
        
        if existing:
            print(f"Subscription for {room_name} already exists, skipping")
            room_to_subscription[room_name] = str(existing.id)
            continue
        
        # Create subscription
        subscription = Subscription(
            user_id=user.id,
            room_name=room_name,
            area_id=area_id,
            building_code=building_code,
            floor_code=floor_code,
            room_code=room_code,
            threshold=20.0,  # Default threshold
            email_recipients=[],  # Will need to be configured manually
            is_active=True
        )
        session.add(subscription)
        session.commit()
        session.refresh(subscription)
        
        room_to_subscription[room_name] = str(subscription.id)
        print(f"Created subscription for {room_name} (ID: {subscription.id})")
    
    return room_to_subscription


def migrate_history(
    session: Session,
    room_to_subscription: Dict[str, str],
    sub_his: List[Dict[str, Any]]
):
    """Migrate history data from JSON to database."""
    for history_item in sub_his:
        room_name = history_item.get('name')
        if not room_name:
            continue
        
        subscription_id = room_to_subscription.get(room_name)
        if not subscription_id:
            print(f"Warning: No subscription found for {room_name}, skipping history")
            continue
        
        history_records = history_item.get('his', [])
        
        for record in history_records:
            timestamp_str = record.get('timestamp')
            value = record.get('value')
            
            if not timestamp_str or value is None:
                continue
            
            try:
                # Parse timestamp
                timestamp = datetime.strptime(timestamp_str, "%Y-%m-%d %H:%M:%S")
            except ValueError:
                try:
                    timestamp = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
                except ValueError:
                    print(f"Warning: Invalid timestamp format: {timestamp_str}, skipping")
                    continue
            
            # Check if record already exists
            from sqlmodel import select
            statement = select(ElectricityHistory).where(
                ElectricityHistory.subscription_id == subscription_id,
                ElectricityHistory.timestamp == timestamp,
                ElectricityHistory.surplus == float(value)
            )
            existing = session.exec(statement).first()
            
            if existing:
                continue
            
            # Create history record
            history = ElectricityHistory(
                subscription_id=subscription_id,
                surplus=float(value),
                timestamp=timestamp
            )
            session.add(history)
        
        session.commit()
        print(f"Migrated {len(history_records)} history records for {room_name}")


def main():
    """Main migration function."""
    print("Starting migration from Bot version to PostgreSQL...")
    
    # Initialize database
    init_db()
    
    # Paths to Bot version data files
    # Script location: Web/backend/scripts/migrate_from_mode2.py
    # Need to go up to project root, then into Bot/
    bot_base = Path(__file__).parent.parent.parent.parent / "Bot"
    sub_file = bot_base / "data_files" / "sub.json"
    his_file = bot_base / "data_files" / "his.json"
    
    if not sub_file.exists():
        print(f"Error: Subscription file not found: {sub_file}")
        return
    
    if not his_file.exists():
        print(f"Error: History file not found: {his_file}")
        return
    
    # Load JSON files
    print("Loading JSON files...")
    sub_list = load_json_file(str(sub_file))
    sub_his = load_json_file(str(his_file))
    
    print(f"Found {len(sub_list)} subscriptions and {len(sub_his)} history entries")
    
    # Create database session
    with Session(engine) as session:
        # Create default user
        user = create_default_user(session)
        
        # Migrate subscriptions
        print("\nMigrating subscriptions...")
        room_to_subscription = migrate_subscriptions(session, user, sub_list, sub_his)
        
        # Migrate history
        print("\nMigrating history data...")
        migrate_history(session, room_to_subscription, sub_his)
        
        print("\nMigration completed successfully!")
        print(f"\nDefault user credentials:")
        print(f"  Username: migrated_user")
        print(f"  Password: changeme")
        print(f"\nPlease change the password after first login!")


if __name__ == "__main__":
    main()
