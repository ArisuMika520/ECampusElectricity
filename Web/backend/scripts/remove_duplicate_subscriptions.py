#!/usr/bin/env python3
"""删除重复的订阅数据"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlmodel import Session, select, func
from app.database import engine, init_db
from app.models.subscription import Subscription
from app.models.history import ElectricityHistory
from app.models.user import User
from collections import defaultdict

def find_duplicates(session: Session):
    """查找重复的订阅"""
    # 方法1: 按房间名和用户ID查找重复
    duplicates_by_name = defaultdict(list)
    all_subs = session.exec(select(Subscription)).all()
    
    for sub in all_subs:
        key = (sub.room_name, sub.user_id)
        duplicates_by_name[key].append(sub)
    
    # 方法2: 按房间代码和用户ID查找重复
    duplicates_by_code = defaultdict(list)
    for sub in all_subs:
        key = (
            sub.area_id,
            sub.building_code,
            sub.floor_code,
            sub.room_code,
            sub.user_id
        )
        duplicates_by_code[key].append(sub)
    
    # 方法3: 按房间代码查找重复（跨用户，可能是迁移数据问题）
    duplicates_by_code_only = defaultdict(list)
    for sub in all_subs:
        key = (
            sub.area_id,
            sub.building_code,
            sub.floor_code,
            sub.room_code
        )
        duplicates_by_code_only[key].append(sub)
    
    return duplicates_by_name, duplicates_by_code, duplicates_by_code_only


def remove_duplicates(session: Session, dry_run: bool = True):
    """删除重复的订阅，保留最新的一个"""
    duplicates_by_name, duplicates_by_code, duplicates_by_code_only = find_duplicates(session)
    
    to_delete = set()
    
    # 处理按房间名重复的
    print("=" * 60)
    print("按房间名和用户ID查找重复:")
    print("=" * 60)
    for (room_name, user_id), subs in duplicates_by_name.items():
        if len(subs) > 1:
            # 按创建时间排序，保留最新的
            subs_sorted = sorted(subs, key=lambda x: x.created_at, reverse=True)
            keep = subs_sorted[0]
            delete_list = subs_sorted[1:]
            
            print(f"\n房间: {room_name} (用户ID: {user_id})")
            print(f"  保留: {keep.id} (创建于: {keep.created_at})")
            print(f"  删除: {len(delete_list)} 个重复订阅")
            for sub in delete_list:
                print(f"    - {sub.id} (创建于: {sub.created_at})")
                to_delete.add(sub.id)
    
    # 处理按房间代码重复的（但房间名可能不同，同一用户）
    print("\n" + "=" * 60)
    print("按房间代码和用户ID查找重复（同一用户）:")
    print("=" * 60)
    found_duplicates = False
    for key, subs in duplicates_by_code.items():
        if len(subs) > 1:
            found_duplicates = True
            area_id, building_code, floor_code, room_code, user_id = key
            # 按创建时间排序，保留最新的
            subs_sorted = sorted(subs, key=lambda x: x.created_at, reverse=True)
            keep = subs_sorted[0]
            delete_list = subs_sorted[1:]
            
            # 检查是否已经在 to_delete 中
            if keep.id not in to_delete:
                print(f"\n房间代码: {area_id}/{building_code}/{floor_code}/{room_code} (用户ID: {user_id})")
                print(f"  保留: {keep.id} - {keep.room_name} (创建于: {keep.created_at})")
                print(f"  删除: {len(delete_list)} 个重复订阅")
                for sub in delete_list:
                    if sub.id not in to_delete:
                        print(f"    - {sub.id} - {sub.room_name} (创建于: {sub.created_at})")
                        to_delete.add(sub.id)
    
    if not found_duplicates:
        print("  无重复")
    
    # 处理跨用户的重复（按房间名，可能是迁移数据问题）
    # 优先删除没有历史数据的订阅
    print("\n" + "=" * 60)
    print("按房间名查找跨用户重复（优先删除没有历史数据的）:")
    print("=" * 60)
    by_room_name_only = defaultdict(list)
    all_subs = session.exec(select(Subscription)).all()
    for sub in all_subs:
        by_room_name_only[sub.room_name].append(sub)
    
    found_cross_user = False
    for room_name, subs in by_room_name_only.items():
        if len(subs) > 1:
            # 检查是否属于不同用户
            user_ids = set(sub.user_id for sub in subs)
            if len(user_ids) > 1:
                found_cross_user = True
                
                # 检查每个订阅的历史记录数
                subs_with_history = []
                subs_without_history = []
                
                for sub in subs:
                    history_count = session.exec(
                        select(func.count(ElectricityHistory.id)).where(
                            ElectricityHistory.subscription_id == sub.id
                        )
                    ).scalar()
                    
                    if history_count > 0:
                        subs_with_history.append((sub, history_count))
                    else:
                        subs_without_history.append(sub)
                
                # 优先保留有历史数据的，如果都有则保留最新的
                if subs_with_history:
                    # 保留历史记录最多的
                    keep_sub, _ = max(subs_with_history, key=lambda x: x[1])
                    delete_list = [s for s, _ in subs_with_history if s.id != keep_sub.id] + subs_without_history
                else:
                    # 都没有历史数据，保留最新的
                    keep_sub = max(subs, key=lambda x: x.created_at)
                    delete_list = [s for s in subs if s.id != keep_sub.id]
                
                # 检查是否已经在 to_delete 中
                if keep_sub.id not in to_delete:
                    print(f"\n房间名: {room_name}")
                    history_count = session.exec(
                        select(func.count(ElectricityHistory.id)).where(
                            ElectricityHistory.subscription_id == keep_sub.id
                        )
                    ).scalar()
                    print(f"  保留: {keep_sub.id} - 用户: {keep_sub.user_id} (历史记录: {history_count}, 创建于: {keep_sub.created_at})")
                    print(f"  删除: {len(delete_list)} 个重复订阅")
                    for sub in delete_list:
                        if sub.id not in to_delete:
                            history_count = session.exec(
                                select(func.count(ElectricityHistory.id)).where(
                                    ElectricityHistory.subscription_id == sub.id
                                )
                            ).scalar()
                            print(f"    - {sub.id} - 用户: {sub.user_id} (历史记录: {history_count}, 创建于: {sub.created_at})")
                            to_delete.add(sub.id)
    
    if not found_cross_user:
        print("  无跨用户重复")
    
    # 处理跨用户的重复（按房间代码，可能是迁移数据问题）
    print("\n" + "=" * 60)
    print("按房间代码查找跨用户重复（可能是迁移数据问题）:")
    print("=" * 60)
    found_cross_user_code = False
    for key, subs in duplicates_by_code_only.items():
        if len(subs) > 1:
            # 检查是否属于不同用户
            user_ids = set(sub.user_id for sub in subs)
            if len(user_ids) > 1:
                found_cross_user_code = True
                area_id, building_code, floor_code, room_code = key
                # 按创建时间排序，保留最新的
                subs_sorted = sorted(subs, key=lambda x: x.created_at, reverse=True)
                keep = subs_sorted[0]
                delete_list = subs_sorted[1:]
                
                # 检查是否已经在 to_delete 中
                if keep.id not in to_delete:
                    print(f"\n房间代码: {area_id}/{building_code}/{floor_code}/{room_code}")
                    print(f"  保留: {keep.id} - {keep.room_name} (用户: {keep.user_id}, 创建于: {keep.created_at})")
                    print(f"  删除: {len(delete_list)} 个重复订阅")
                    for sub in delete_list:
                        if sub.id not in to_delete:
                            print(f"    - {sub.id} - {sub.room_name} (用户: {sub.user_id}, 创建于: {sub.created_at})")
                            to_delete.add(sub.id)
    
    if not found_cross_user_code:
        print("  无跨用户重复")
    
    if not to_delete:
        print("\n没有找到重复的订阅")
        return
    
    print("\n" + "=" * 60)
    print(f"总计需要删除 {len(to_delete)} 个重复订阅")
    print("=" * 60)
    
    if dry_run:
        print("\n这是预览模式，不会实际删除数据")
        print("运行脚本时添加 --execute 参数来实际删除")
        return
    
    # 实际删除
    deleted_count = 0
    deleted_history_count = 0
    
    for sub_id in to_delete:
        # 先删除关联的历史记录
        history_count = session.exec(
            select(ElectricityHistory).where(ElectricityHistory.subscription_id == sub_id)
        ).all()
        
        for history in history_count:
            session.delete(history)
            deleted_history_count += 1
        
        # 删除订阅
        sub = session.exec(select(Subscription).where(Subscription.id == sub_id)).first()
        if sub:
            session.delete(sub)
            deleted_count += 1
    
    session.commit()
    
    print(f"\n删除完成:")
    print(f"  - 删除了 {deleted_count} 个重复订阅")
    print(f"  - 删除了 {deleted_history_count} 条关联的历史记录")


def main():
    import argparse
    parser = argparse.ArgumentParser(description='删除重复的订阅数据')
    parser.add_argument('--execute', action='store_true', help='实际执行删除操作（默认是预览模式）')
    args = parser.parse_args()
    
    # 确保数据库表已创建
    init_db()
    
    with Session(engine) as session:
        remove_duplicates(session, dry_run=not args.execute)


if __name__ == '__main__':
    main()


import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlmodel import Session, select, func
from app.database import engine, init_db
from app.models.subscription import Subscription
from app.models.history import ElectricityHistory
from app.models.user import User
from collections import defaultdict

def find_duplicates(session: Session):
    """查找重复的订阅"""
    # 方法1: 按房间名和用户ID查找重复
    duplicates_by_name = defaultdict(list)
    all_subs = session.exec(select(Subscription)).all()
    
    for sub in all_subs:
        key = (sub.room_name, sub.user_id)
        duplicates_by_name[key].append(sub)
    
    # 方法2: 按房间代码和用户ID查找重复
    duplicates_by_code = defaultdict(list)
    for sub in all_subs:
        key = (
            sub.area_id,
            sub.building_code,
            sub.floor_code,
            sub.room_code,
            sub.user_id
        )
        duplicates_by_code[key].append(sub)
    
    # 方法3: 按房间代码查找重复（跨用户，可能是迁移数据问题）
    duplicates_by_code_only = defaultdict(list)
    for sub in all_subs:
        key = (
            sub.area_id,
            sub.building_code,
            sub.floor_code,
            sub.room_code
        )
        duplicates_by_code_only[key].append(sub)
    
    return duplicates_by_name, duplicates_by_code, duplicates_by_code_only


def remove_duplicates(session: Session, dry_run: bool = True):
    """删除重复的订阅，保留最新的一个"""
    duplicates_by_name, duplicates_by_code, duplicates_by_code_only = find_duplicates(session)
    
    to_delete = set()
    
    # 处理按房间名重复的
    print("=" * 60)
    print("按房间名和用户ID查找重复:")
    print("=" * 60)
    for (room_name, user_id), subs in duplicates_by_name.items():
        if len(subs) > 1:
            # 按创建时间排序，保留最新的
            subs_sorted = sorted(subs, key=lambda x: x.created_at, reverse=True)
            keep = subs_sorted[0]
            delete_list = subs_sorted[1:]
            
            print(f"\n房间: {room_name} (用户ID: {user_id})")
            print(f"  保留: {keep.id} (创建于: {keep.created_at})")
            print(f"  删除: {len(delete_list)} 个重复订阅")
            for sub in delete_list:
                print(f"    - {sub.id} (创建于: {sub.created_at})")
                to_delete.add(sub.id)
    
    # 处理按房间代码重复的（但房间名可能不同，同一用户）
    print("\n" + "=" * 60)
    print("按房间代码和用户ID查找重复（同一用户）:")
    print("=" * 60)
    found_duplicates = False
    for key, subs in duplicates_by_code.items():
        if len(subs) > 1:
            found_duplicates = True
            area_id, building_code, floor_code, room_code, user_id = key
            # 按创建时间排序，保留最新的
            subs_sorted = sorted(subs, key=lambda x: x.created_at, reverse=True)
            keep = subs_sorted[0]
            delete_list = subs_sorted[1:]
            
            # 检查是否已经在 to_delete 中
            if keep.id not in to_delete:
                print(f"\n房间代码: {area_id}/{building_code}/{floor_code}/{room_code} (用户ID: {user_id})")
                print(f"  保留: {keep.id} - {keep.room_name} (创建于: {keep.created_at})")
                print(f"  删除: {len(delete_list)} 个重复订阅")
                for sub in delete_list:
                    if sub.id not in to_delete:
                        print(f"    - {sub.id} - {sub.room_name} (创建于: {sub.created_at})")
                        to_delete.add(sub.id)
    
    if not found_duplicates:
        print("  无重复")
    
    # 处理跨用户的重复（按房间名，可能是迁移数据问题）
    # 优先删除没有历史数据的订阅
    print("\n" + "=" * 60)
    print("按房间名查找跨用户重复（优先删除没有历史数据的）:")
    print("=" * 60)
    by_room_name_only = defaultdict(list)
    all_subs = session.exec(select(Subscription)).all()
    for sub in all_subs:
        by_room_name_only[sub.room_name].append(sub)
    
    found_cross_user = False
    for room_name, subs in by_room_name_only.items():
        if len(subs) > 1:
            # 检查是否属于不同用户
            user_ids = set(sub.user_id for sub in subs)
            if len(user_ids) > 1:
                found_cross_user = True
                
                # 检查每个订阅的历史记录数
                subs_with_history = []
                subs_without_history = []
                
                for sub in subs:
                    history_count = session.exec(
                        select(func.count(ElectricityHistory.id)).where(
                            ElectricityHistory.subscription_id == sub.id
                        )
                    ).scalar()
                    
                    if history_count > 0:
                        subs_with_history.append((sub, history_count))
                    else:
                        subs_without_history.append(sub)
                
                # 优先保留有历史数据的，如果都有则保留最新的
                if subs_with_history:
                    # 保留历史记录最多的
                    keep_sub, _ = max(subs_with_history, key=lambda x: x[1])
                    delete_list = [s for s, _ in subs_with_history if s.id != keep_sub.id] + subs_without_history
                else:
                    # 都没有历史数据，保留最新的
                    keep_sub = max(subs, key=lambda x: x.created_at)
                    delete_list = [s for s in subs if s.id != keep_sub.id]
                
                # 检查是否已经在 to_delete 中
                if keep_sub.id not in to_delete:
                    print(f"\n房间名: {room_name}")
                    history_count = session.exec(
                        select(func.count(ElectricityHistory.id)).where(
                            ElectricityHistory.subscription_id == keep_sub.id
                        )
                    ).scalar()
                    print(f"  保留: {keep_sub.id} - 用户: {keep_sub.user_id} (历史记录: {history_count}, 创建于: {keep_sub.created_at})")
                    print(f"  删除: {len(delete_list)} 个重复订阅")
                    for sub in delete_list:
                        if sub.id not in to_delete:
                            history_count = session.exec(
                                select(func.count(ElectricityHistory.id)).where(
                                    ElectricityHistory.subscription_id == sub.id
                                )
                            ).scalar()
                            print(f"    - {sub.id} - 用户: {sub.user_id} (历史记录: {history_count}, 创建于: {sub.created_at})")
                            to_delete.add(sub.id)
    
    if not found_cross_user:
        print("  无跨用户重复")
    
    # 处理跨用户的重复（按房间代码，可能是迁移数据问题）
    print("\n" + "=" * 60)
    print("按房间代码查找跨用户重复（可能是迁移数据问题）:")
    print("=" * 60)
    found_cross_user_code = False
    for key, subs in duplicates_by_code_only.items():
        if len(subs) > 1:
            # 检查是否属于不同用户
            user_ids = set(sub.user_id for sub in subs)
            if len(user_ids) > 1:
                found_cross_user_code = True
                area_id, building_code, floor_code, room_code = key
                # 按创建时间排序，保留最新的
                subs_sorted = sorted(subs, key=lambda x: x.created_at, reverse=True)
                keep = subs_sorted[0]
                delete_list = subs_sorted[1:]
                
                # 检查是否已经在 to_delete 中
                if keep.id not in to_delete:
                    print(f"\n房间代码: {area_id}/{building_code}/{floor_code}/{room_code}")
                    print(f"  保留: {keep.id} - {keep.room_name} (用户: {keep.user_id}, 创建于: {keep.created_at})")
                    print(f"  删除: {len(delete_list)} 个重复订阅")
                    for sub in delete_list:
                        if sub.id not in to_delete:
                            print(f"    - {sub.id} - {sub.room_name} (用户: {sub.user_id}, 创建于: {sub.created_at})")
                            to_delete.add(sub.id)
    
    if not found_cross_user_code:
        print("  无跨用户重复")
    
    if not to_delete:
        print("\n没有找到重复的订阅")
        return
    
    print("\n" + "=" * 60)
    print(f"总计需要删除 {len(to_delete)} 个重复订阅")
    print("=" * 60)
    
    if dry_run:
        print("\n这是预览模式，不会实际删除数据")
        print("运行脚本时添加 --execute 参数来实际删除")
        return
    
    # 实际删除
    deleted_count = 0
    deleted_history_count = 0
    
    for sub_id in to_delete:
        # 先删除关联的历史记录
        history_count = session.exec(
            select(ElectricityHistory).where(ElectricityHistory.subscription_id == sub_id)
        ).all()
        
        for history in history_count:
            session.delete(history)
            deleted_history_count += 1
        
        # 删除订阅
        sub = session.exec(select(Subscription).where(Subscription.id == sub_id)).first()
        if sub:
            session.delete(sub)
            deleted_count += 1
    
    session.commit()
    
    print(f"\n删除完成:")
    print(f"  - 删除了 {deleted_count} 个重复订阅")
    print(f"  - 删除了 {deleted_history_count} 条关联的历史记录")


def main():
    import argparse
    parser = argparse.ArgumentParser(description='删除重复的订阅数据')
    parser.add_argument('--execute', action='store_true', help='实际执行删除操作（默认是预览模式）')
    args = parser.parse_args()
    
    # 确保数据库表已创建
    init_db()
    
    with Session(engine) as session:
        remove_duplicates(session, dry_run=not args.execute)


if __name__ == '__main__':
    main()
