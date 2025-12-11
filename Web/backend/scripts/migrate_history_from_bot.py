#!/usr/bin/env python3
"""从 Bot 版本的历史数据文件迁移历史记录到数据库"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import json
from datetime import datetime
from sqlmodel import Session, select
from app.database import engine, init_db
from app.models.subscription import Subscription
from app.models.history import ElectricityHistory
from collections import defaultdict

def migrate_history_data(session: Session, dry_run: bool = True):
    """迁移历史数据"""
    print("=" * 60)
    print("从 Bot 版本迁移历史数据")
    print("=" * 60)
    
    # 读取历史数据文件
    bot_base = Path(__file__).parent.parent.parent.parent / "Bot"
    history_file = bot_base / "data_files" / "his.json"
    
    if not history_file.exists():
        print(f"错误: 找不到历史数据文件: {history_file}")
        return
    
    print(f"\n读取历史数据文件: {history_file}")
    
    with open(history_file, 'r', encoding='utf-8') as f:
        history_data = json.load(f)
    
    print(f"找到 {len(history_data)} 个房间的历史数据")
    
    # 获取所有订阅（按房间名索引）
    all_subs = session.exec(select(Subscription)).all()
    subscriptions_by_name = {sub.room_name: sub for sub in all_subs}
    
    print(f"数据库中有 {len(subscriptions_by_name)} 个订阅")
    
    # 统计信息
    total_records = 0
    matched_rooms = 0
    unmatched_rooms = []
    records_to_insert = []
    duplicate_records = 0
    
    # 处理每个房间的历史数据
    for room_data in history_data:
        room_name = room_data.get('name')
        history_list = room_data.get('his', [])
        
        if not room_name:
            continue
        
        # 查找对应的订阅
        subscription = subscriptions_by_name.get(room_name)
        
        if not subscription:
            # 如果有历史数据但没有订阅，尝试创建订阅
            print(f"⚠️  未找到订阅: {room_name}，尝试创建订阅...")
            try:
                from app.utils.room_parser import parse_room_string
                parsed = parse_room_string(room_name)
                subscription = Subscription(
                    room_name=room_name,
                    area_id=parsed["area_id"],
                    building_code=parsed["building_code"],
                    floor_code=parsed["floor_code"],
                    room_code=parsed["room_code"],
                    threshold=20.0,
                    email_recipients=[],
                    is_active=True
                )
                session.add(subscription)
                session.commit()
                session.refresh(subscription)
                subscriptions_by_name[room_name] = subscription
                print(f"  ✓ 已创建订阅: {room_name} (ID: {subscription.id})")
            except Exception as e:
                unmatched_rooms.append(room_name)
                print(f"  ✗ 创建订阅失败: {e} (跳过 {len(history_list)} 条历史记录)")
                continue
        
        matched_rooms += 1
        print(f"\n处理房间: {room_name} (订阅ID: {subscription.id})")
        print(f"  历史记录数: {len(history_list)}")
        
        # 检查已存在的历史记录（按时间戳去重）
        existing_timestamps = set()
        existing_records = session.exec(
            select(ElectricityHistory).where(
                ElectricityHistory.subscription_id == subscription.id
            )
        ).all()
        
        for existing in existing_records:
            existing_timestamps.add(existing.timestamp.strftime("%Y-%m-%d %H:%M:%S"))
        
        # 解析并准备插入历史记录
        for hist_item in history_list:
            timestamp_str = hist_item.get('timestamp')
            value = hist_item.get('value')
            
            if not timestamp_str or value is None:
                continue
            
            # 解析时间戳
            try:
                timestamp = datetime.strptime(timestamp_str, "%Y-%m-%d %H:%M:%S")
            except ValueError:
                print(f"  ⚠️  无法解析时间戳: {timestamp_str}")
                continue
            
            # 检查是否已存在（去重）
            if timestamp_str in existing_timestamps:
                duplicate_records += 1
                continue
            
            # 创建历史记录对象
            history_record = ElectricityHistory(
                subscription_id=subscription.id,
                surplus=float(value),
                timestamp=timestamp
            )
            records_to_insert.append(history_record)
            total_records += 1
    
    # 打印统计信息
    print("\n" + "=" * 60)
    print("迁移统计")
    print("=" * 60)
    print(f"匹配的房间数: {matched_rooms}")
    print(f"未匹配的房间数: {len(unmatched_rooms)}")
    if unmatched_rooms:
        print(f"未匹配的房间: {', '.join(unmatched_rooms[:10])}")
        if len(unmatched_rooms) > 10:
            print(f"  ... 还有 {len(unmatched_rooms) - 10} 个房间")
    print(f"待插入的历史记录数: {len(records_to_insert)}")
    print(f"重复记录数（已跳过）: {duplicate_records}")
    
    if dry_run:
        print("\n这是预览模式，不会实际插入数据")
        print("运行脚本时添加 --execute 参数来实际执行")
        return
    
    # 实际插入数据
    if not records_to_insert:
        print("\n没有需要插入的数据")
        return
    
    print(f"\n开始插入 {len(records_to_insert)} 条历史记录...")
    
    inserted_count = 0
    error_count = 0
    
    # 批量插入（每批 100 条）
    batch_size = 100
    for i in range(0, len(records_to_insert), batch_size):
        batch = records_to_insert[i:i + batch_size]
        try:
            for record in batch:
                session.add(record)
            session.commit()
            inserted_count += len(batch)
            print(f"  已插入 {inserted_count}/{len(records_to_insert)} 条记录...")
        except Exception as e:
            session.rollback()
            error_count += len(batch)
            print(f"  ⚠️  插入批次失败: {e}")
            # 尝试逐条插入
            for record in batch:
                try:
                    session.add(record)
                    session.commit()
                    inserted_count += 1
                except Exception as e2:
                    session.rollback()
                    error_count += 1
                    print(f"    ⚠️  插入失败: {record.subscription_id} @ {record.timestamp}: {e2}")
    
    print("\n" + "=" * 60)
    print("迁移完成")
    print("=" * 60)
    print(f"成功插入: {inserted_count} 条记录")
    if error_count > 0:
        print(f"失败: {error_count} 条记录")


def main():
    import argparse
    parser = argparse.ArgumentParser(description='从 Bot 版本迁移历史数据')
    parser.add_argument('--execute', action='store_true', help='实际执行迁移（默认是预览模式）')
    args = parser.parse_args()
    
    init_db()
    
    with Session(engine) as session:
        migrate_history_data(session, dry_run=not args.execute)


if __name__ == '__main__':
    main()


import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import json
from datetime import datetime
from sqlmodel import Session, select
from app.database import engine, init_db
from app.models.subscription import Subscription
from app.models.history import ElectricityHistory
from collections import defaultdict

def migrate_history_data(session: Session, dry_run: bool = True):
    """迁移历史数据"""
    print("=" * 60)
    print("从 Bot 版本迁移历史数据")
    print("=" * 60)
    
    # 读取历史数据文件
    bot_base = Path(__file__).parent.parent.parent.parent / "Bot"
    history_file = bot_base / "data_files" / "his.json"
    
    if not history_file.exists():
        print(f"错误: 找不到历史数据文件: {history_file}")
        return
    
    print(f"\n读取历史数据文件: {history_file}")
    
    with open(history_file, 'r', encoding='utf-8') as f:
        history_data = json.load(f)
    
    print(f"找到 {len(history_data)} 个房间的历史数据")
    
    # 获取所有订阅（按房间名索引）
    all_subs = session.exec(select(Subscription)).all()
    subscriptions_by_name = {sub.room_name: sub for sub in all_subs}
    
    print(f"数据库中有 {len(subscriptions_by_name)} 个订阅")
    
    # 统计信息
    total_records = 0
    matched_rooms = 0
    unmatched_rooms = []
    records_to_insert = []
    duplicate_records = 0
    
    # 处理每个房间的历史数据
    for room_data in history_data:
        room_name = room_data.get('name')
        history_list = room_data.get('his', [])
        
        if not room_name:
            continue
        
        # 查找对应的订阅
        subscription = subscriptions_by_name.get(room_name)
        
        if not subscription:
            # 如果有历史数据但没有订阅，尝试创建订阅
            print(f"⚠️  未找到订阅: {room_name}，尝试创建订阅...")
            try:
                from app.utils.room_parser import parse_room_string
                parsed = parse_room_string(room_name)
                subscription = Subscription(
                    room_name=room_name,
                    area_id=parsed["area_id"],
                    building_code=parsed["building_code"],
                    floor_code=parsed["floor_code"],
                    room_code=parsed["room_code"],
                    threshold=20.0,
                    email_recipients=[],
                    is_active=True
                )
                session.add(subscription)
                session.commit()
                session.refresh(subscription)
                subscriptions_by_name[room_name] = subscription
                print(f"  ✓ 已创建订阅: {room_name} (ID: {subscription.id})")
            except Exception as e:
                unmatched_rooms.append(room_name)
                print(f"  ✗ 创建订阅失败: {e} (跳过 {len(history_list)} 条历史记录)")
                continue
        
        matched_rooms += 1
        print(f"\n处理房间: {room_name} (订阅ID: {subscription.id})")
        print(f"  历史记录数: {len(history_list)}")
        
        # 检查已存在的历史记录（按时间戳去重）
        existing_timestamps = set()
        existing_records = session.exec(
            select(ElectricityHistory).where(
                ElectricityHistory.subscription_id == subscription.id
            )
        ).all()
        
        for existing in existing_records:
            existing_timestamps.add(existing.timestamp.strftime("%Y-%m-%d %H:%M:%S"))
        
        # 解析并准备插入历史记录
        for hist_item in history_list:
            timestamp_str = hist_item.get('timestamp')
            value = hist_item.get('value')
            
            if not timestamp_str or value is None:
                continue
            
            # 解析时间戳
            try:
                timestamp = datetime.strptime(timestamp_str, "%Y-%m-%d %H:%M:%S")
            except ValueError:
                print(f"  ⚠️  无法解析时间戳: {timestamp_str}")
                continue
            
            # 检查是否已存在（去重）
            if timestamp_str in existing_timestamps:
                duplicate_records += 1
                continue
            
            # 创建历史记录对象
            history_record = ElectricityHistory(
                subscription_id=subscription.id,
                surplus=float(value),
                timestamp=timestamp
            )
            records_to_insert.append(history_record)
            total_records += 1
    
    # 打印统计信息
    print("\n" + "=" * 60)
    print("迁移统计")
    print("=" * 60)
    print(f"匹配的房间数: {matched_rooms}")
    print(f"未匹配的房间数: {len(unmatched_rooms)}")
    if unmatched_rooms:
        print(f"未匹配的房间: {', '.join(unmatched_rooms[:10])}")
        if len(unmatched_rooms) > 10:
            print(f"  ... 还有 {len(unmatched_rooms) - 10} 个房间")
    print(f"待插入的历史记录数: {len(records_to_insert)}")
    print(f"重复记录数（已跳过）: {duplicate_records}")
    
    if dry_run:
        print("\n这是预览模式，不会实际插入数据")
        print("运行脚本时添加 --execute 参数来实际执行")
        return
    
    # 实际插入数据
    if not records_to_insert:
        print("\n没有需要插入的数据")
        return
    
    print(f"\n开始插入 {len(records_to_insert)} 条历史记录...")
    
    inserted_count = 0
    error_count = 0
    
    # 批量插入（每批 100 条）
    batch_size = 100
    for i in range(0, len(records_to_insert), batch_size):
        batch = records_to_insert[i:i + batch_size]
        try:
            for record in batch:
                session.add(record)
            session.commit()
            inserted_count += len(batch)
            print(f"  已插入 {inserted_count}/{len(records_to_insert)} 条记录...")
        except Exception as e:
            session.rollback()
            error_count += len(batch)
            print(f"  ⚠️  插入批次失败: {e}")
            # 尝试逐条插入
            for record in batch:
                try:
                    session.add(record)
                    session.commit()
                    inserted_count += 1
                except Exception as e2:
                    session.rollback()
                    error_count += 1
                    print(f"    ⚠️  插入失败: {record.subscription_id} @ {record.timestamp}: {e2}")
    
    print("\n" + "=" * 60)
    print("迁移完成")
    print("=" * 60)
    print(f"成功插入: {inserted_count} 条记录")
    if error_count > 0:
        print(f"失败: {error_count} 条记录")


def main():
    import argparse
    parser = argparse.ArgumentParser(description='从 Bot 版本迁移历史数据')
    parser.add_argument('--execute', action='store_true', help='实际执行迁移（默认是预览模式）')
    args = parser.parse_args()
    
    init_db()
    
    with Session(engine) as session:
        migrate_history_data(session, dry_run=not args.execute)


if __name__ == '__main__':
    main()
