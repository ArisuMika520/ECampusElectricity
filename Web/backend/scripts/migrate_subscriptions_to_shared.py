#!/usr/bin/env python3
"""将现有订阅数据迁移到共享订阅模式

1. 检查 subscriptions 表是否有 user_id 字段
2. 如果有，创建 user_subscriptions 表并迁移数据
3. 删除重复订阅（优先保留有历史数据的）
4. 删除 subscriptions 表的 user_id 字段
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlmodel import Session, select, func, text
from app.database import engine, init_db
from app.models.subscription import Subscription
from app.models.user_subscription import UserSubscription
from app.models.history import ElectricityHistory
from collections import defaultdict

def check_table_structure(session: Session):
    """检查 subscriptions 表结构"""
    try:
        # 尝试查询 user_id 字段
        result = session.exec(text("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'subscriptions' AND column_name = 'user_id'
        """)).first()
        return result is not None
    except:
        return False

def migrate_data(session: Session, dry_run: bool = True):
    """迁移数据到共享订阅模式"""
    print("=" * 60)
    print("迁移到共享订阅模式")
    print("=" * 60)
    
    has_user_id = check_table_structure(session)
    
    if not has_user_id:
        print("\n订阅表已经是新版本（不包含 user_id）")
        print("检查是否有 user_subscriptions 表...")
        
        try:
            result = session.exec(text("""
                SELECT COUNT(*) 
                FROM information_schema.tables 
                WHERE table_name = 'user_subscriptions'
            """)).first()
            
            if result == 0:
                print("user_subscriptions 表不存在，需要创建")
                init_db()  # 这会创建所有表
                print("✓ 已创建 user_subscriptions 表")
            else:
                print("✓ user_subscriptions 表已存在")
        except Exception as e:
            print(f"检查表结构时出错: {e}")
            init_db()
        
        # 检查是否有数据需要迁移
        all_subs = session.exec(select(Subscription)).all()
        user_subs_count = session.exec(select(func.count(UserSubscription.id))).first() or 0
        
        if user_subs_count == 0 and len(all_subs) > 0:
            print(f"\n发现 {len(all_subs)} 个订阅但没有用户关联，需要迁移")
            # 这里需要从其他地方获取用户信息，或者让用户重新添加订阅
            print("注意: 由于订阅表已经没有 user_id，无法自动迁移用户关联")
            print("建议: 让用户重新添加订阅，系统会自动创建关联")
        else:
            print(f"\n✓ 已有 {user_subs_count} 个用户-订阅关联")
        
        return
    
    print("\n检测到旧版订阅表（包含 user_id 字段）")
    print("开始迁移数据...")
    
    # 直接从数据库查询，包含 user_id
    result = session.exec(text("""
        SELECT id, user_id, room_name, area_id, building_code, floor_code, room_code, 
               threshold, email_recipients, is_active, created_at
        FROM subscriptions
    """))
    
    all_subs_data = []
    for row in result:
        all_subs_data.append({
            'id': row[0],
            'user_id': row[1],
            'room_name': row[2],
            'area_id': row[3],
            'building_code': row[4],
            'floor_code': row[5],
            'room_code': row[6],
            'threshold': row[7],
            'email_recipients': row[8],
            'is_active': row[9],
            'created_at': row[10]
        })
    
    print(f"当前订阅总数: {len(all_subs_data)}")
    
    # 按房间代码分组
    by_room_code = defaultdict(list)
    for sub_data in all_subs_data:
        key = (sub_data['area_id'], sub_data['building_code'], sub_data['floor_code'], sub_data['room_code'])
        by_room_code[key].append(sub_data)
    
    print(f"唯一房间数: {len(by_room_code)}")
    duplicates = {k: v for k, v in by_room_code.items() if len(v) > 1}
    print(f"重复房间数: {len(duplicates)}")
    
    subscriptions_to_keep = {}
    subscriptions_to_delete = []
    user_subscriptions_to_create = []
    
    for room_code_key, subs in by_room_code.items():
        if len(subs) == 1:
            # 只有一个订阅，直接保留
            sub_data = subs[0]
            subscriptions_to_keep[room_code_key] = sub_data
            
            # 创建用户关联
            if sub_data.get('user_id'):
                user_sub = UserSubscription(
                    user_id=sub_data['user_id'],
                    subscription_id=sub_data['id'],
                    threshold=sub_data['threshold'],
                    email_recipients=sub_data['email_recipients'],
                    is_active=sub_data['is_active']
                )
                user_subscriptions_to_create.append(user_sub)
        else:
            # 多个订阅，优先保留有历史数据的
            subs_with_history = []
            subs_without_history = []
            
            for sub_data in subs:
                history_count = session.exec(
                    select(func.count(ElectricityHistory.id)).where(
                        ElectricityHistory.subscription_id == sub_data['id']
                    )
                ).first() or 0
                
                if history_count > 0:
                    subs_with_history.append((sub_data, history_count))
                else:
                    subs_without_history.append(sub_data)
            
            if subs_with_history:
                # 选择历史记录最多的
                keep_sub_data, _ = max(subs_with_history, key=lambda x: x[1])
                subscriptions_to_keep[room_code_key] = keep_sub_data
                
                # 删除其他的（包括没有历史数据的）
                for sub_data, _ in subs_with_history:
                    if sub_data['id'] != keep_sub_data['id']:
                        subscriptions_to_delete.append(sub_data)
                for sub_data in subs_without_history:
                    subscriptions_to_delete.append(sub_data)
                
                # 为保留的订阅创建所有用户的关联
                for sub_data in subs:
                    if sub_data['id'] == keep_sub_data['id']:
                        if sub_data.get('user_id'):
                            user_sub = UserSubscription(
                                user_id=sub_data['user_id'],
                                subscription_id=sub_data['id'],
                                threshold=sub_data['threshold'],
                                email_recipients=sub_data['email_recipients'],
                                is_active=sub_data['is_active']
                            )
                            user_subscriptions_to_create.append(user_sub)
                    else:
                        # 为被删除的订阅的用户创建关联到保留的订阅
                        if sub_data.get('user_id'):
                            existing = session.exec(
                                select(UserSubscription).where(
                                    UserSubscription.user_id == sub_data['user_id'],
                                    UserSubscription.subscription_id == keep_sub_data['id']
                                )
                            ).first()
                            
                            if not existing:
                                user_sub = UserSubscription(
                                    user_id=sub_data['user_id'],
                                    subscription_id=keep_sub_data['id'],
                                    threshold=sub_data['threshold'],
                                    email_recipients=sub_data['email_recipients'],
                                    is_active=sub_data['is_active']
                                )
                                user_subscriptions_to_create.append(user_sub)
            else:
                # 都没有历史数据，选择最新的
                keep_sub_data = max(subs, key=lambda x: x['created_at'])
                subscriptions_to_keep[room_code_key] = keep_sub_data
                
                # 删除其他的
                for sub_data in subs:
                    if sub_data['id'] != keep_sub_data['id']:
                        subscriptions_to_delete.append(sub_data)
                
                # 为保留的订阅创建所有用户的关联
                for sub_data in subs:
                    if sub_data['id'] == keep_sub_data['id']:
                        if sub_data.get('user_id'):
                            user_sub = UserSubscription(
                                user_id=sub_data['user_id'],
                                subscription_id=sub_data['id'],
                                threshold=sub_data['threshold'],
                                email_recipients=sub_data['email_recipients'],
                                is_active=sub_data['is_active']
                            )
                            user_subscriptions_to_create.append(user_sub)
                    else:
                        if sub_data.get('user_id'):
                            existing = session.exec(
                                select(UserSubscription).where(
                                    UserSubscription.user_id == sub_data['user_id'],
                                    UserSubscription.subscription_id == keep_sub_data['id']
                                )
                            ).first()
                            
                            if not existing:
                                user_sub = UserSubscription(
                                    user_id=sub_data['user_id'],
                                    subscription_id=keep_sub_data['id'],
                                    threshold=sub_data['threshold'],
                                    email_recipients=sub_data['email_recipients'],
                                    is_active=sub_data['is_active']
                                )
                                user_subscriptions_to_create.append(user_sub)
    
    print(f"\n将保留 {len(subscriptions_to_keep)} 个订阅")
    print(f"将删除 {len(subscriptions_to_delete)} 个重复订阅")
    print(f"将创建 {len(user_subscriptions_to_create)} 个用户-订阅关联")
    
    if subscriptions_to_delete:
        print("\n将被删除的订阅:")
        for sub_data in subscriptions_to_delete:
            history_count = session.exec(
                select(func.count(ElectricityHistory.id)).where(
                    ElectricityHistory.subscription_id == sub_data['id']
                )
            ).first() or 0
            print(f"  - {sub_data['room_name']} (ID: {sub_data['id']}, 用户: {sub_data['user_id']}, 历史记录: {history_count})")
    
    if dry_run:
        print("\n这是预览模式，不会实际执行迁移")
        print("运行脚本时添加 --execute 参数来实际执行")
        return
    
    # 实际执行
    print("\n开始执行迁移...")
    
    # 1. 删除重复订阅的历史记录
    deleted_history_count = 0
    for sub_data in subscriptions_to_delete:
        history_records = session.exec(
            select(ElectricityHistory).where(
                ElectricityHistory.subscription_id == sub_data['id']
            )
        ).all()
        for history in history_records:
            session.delete(history)
            deleted_history_count += 1
    
    # 2. 删除重复订阅
    for sub_data in subscriptions_to_delete:
        sub = session.exec(select(Subscription).where(Subscription.id == sub_data['id'])).first()
        if sub:
            session.delete(sub)
    
    # 3. 创建用户-订阅关联
    for user_sub in user_subscriptions_to_create:
        existing = session.exec(
            select(UserSubscription).where(
                UserSubscription.user_id == user_sub.user_id,
                UserSubscription.subscription_id == user_sub.subscription_id
            )
        ).first()
        if not existing:
            session.add(user_sub)
    
    session.commit()
    
    print(f"\n迁移完成:")
    print(f"  - 删除了 {len(subscriptions_to_delete)} 个重复订阅")
    print(f"  - 删除了 {deleted_history_count} 条历史记录")
    print(f"  - 创建了 {len(user_subscriptions_to_create)} 个用户-订阅关联")
    
    # 4. 删除 user_id 列（需要 SQL）
    print("\n删除 subscriptions 表的 user_id 列...")
    try:
        session.exec(text("ALTER TABLE subscriptions DROP COLUMN IF EXISTS user_id;"))
        session.commit()
        print("✓ 已删除 user_id 列")
    except Exception as e:
        print(f"删除 user_id 列失败: {e}")
        print("请手动运行: ALTER TABLE subscriptions DROP COLUMN IF EXISTS user_id;")


def main():
    import argparse
    parser = argparse.ArgumentParser(description='迁移到共享订阅模式')
    parser.add_argument('--execute', action='store_true', help='实际执行迁移（默认是预览模式）')
    args = parser.parse_args()
    
    init_db()
    
    with Session(engine) as session:
        migrate_data(session, dry_run=not args.execute)


if __name__ == '__main__':
    main()



1. 检查 subscriptions 表是否有 user_id 字段
2. 如果有，创建 user_subscriptions 表并迁移数据
3. 删除重复订阅（优先保留有历史数据的）
4. 删除 subscriptions 表的 user_id 字段
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlmodel import Session, select, func, text
from app.database import engine, init_db
from app.models.subscription import Subscription
from app.models.user_subscription import UserSubscription
from app.models.history import ElectricityHistory
from collections import defaultdict

def check_table_structure(session: Session):
    """检查 subscriptions 表结构"""
    try:
        # 尝试查询 user_id 字段
        result = session.exec(text("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'subscriptions' AND column_name = 'user_id'
        """)).first()
        return result is not None
    except:
        return False

def migrate_data(session: Session, dry_run: bool = True):
    """迁移数据到共享订阅模式"""
    print("=" * 60)
    print("迁移到共享订阅模式")
    print("=" * 60)
    
    has_user_id = check_table_structure(session)
    
    if not has_user_id:
        print("\n订阅表已经是新版本（不包含 user_id）")
        print("检查是否有 user_subscriptions 表...")
        
        try:
            result = session.exec(text("""
                SELECT COUNT(*) 
                FROM information_schema.tables 
                WHERE table_name = 'user_subscriptions'
            """)).first()
            
            if result == 0:
                print("user_subscriptions 表不存在，需要创建")
                init_db()  # 这会创建所有表
                print("✓ 已创建 user_subscriptions 表")
            else:
                print("✓ user_subscriptions 表已存在")
        except Exception as e:
            print(f"检查表结构时出错: {e}")
            init_db()
        
        # 检查是否有数据需要迁移
        all_subs = session.exec(select(Subscription)).all()
        user_subs_count = session.exec(select(func.count(UserSubscription.id))).first() or 0
        
        if user_subs_count == 0 and len(all_subs) > 0:
            print(f"\n发现 {len(all_subs)} 个订阅但没有用户关联，需要迁移")
            # 这里需要从其他地方获取用户信息，或者让用户重新添加订阅
            print("注意: 由于订阅表已经没有 user_id，无法自动迁移用户关联")
            print("建议: 让用户重新添加订阅，系统会自动创建关联")
        else:
            print(f"\n✓ 已有 {user_subs_count} 个用户-订阅关联")
        
        return
    
    print("\n检测到旧版订阅表（包含 user_id 字段）")
    print("开始迁移数据...")
    
    # 直接从数据库查询，包含 user_id
    result = session.exec(text("""
        SELECT id, user_id, room_name, area_id, building_code, floor_code, room_code, 
               threshold, email_recipients, is_active, created_at
        FROM subscriptions
    """))
    
    all_subs_data = []
    for row in result:
        all_subs_data.append({
            'id': row[0],
            'user_id': row[1],
            'room_name': row[2],
            'area_id': row[3],
            'building_code': row[4],
            'floor_code': row[5],
            'room_code': row[6],
            'threshold': row[7],
            'email_recipients': row[8],
            'is_active': row[9],
            'created_at': row[10]
        })
    
    print(f"当前订阅总数: {len(all_subs_data)}")
    
    # 按房间代码分组
    by_room_code = defaultdict(list)
    for sub_data in all_subs_data:
        key = (sub_data['area_id'], sub_data['building_code'], sub_data['floor_code'], sub_data['room_code'])
        by_room_code[key].append(sub_data)
    
    print(f"唯一房间数: {len(by_room_code)}")
    duplicates = {k: v for k, v in by_room_code.items() if len(v) > 1}
    print(f"重复房间数: {len(duplicates)}")
    
    subscriptions_to_keep = {}
    subscriptions_to_delete = []
    user_subscriptions_to_create = []
    
    for room_code_key, subs in by_room_code.items():
        if len(subs) == 1:
            # 只有一个订阅，直接保留
            sub_data = subs[0]
            subscriptions_to_keep[room_code_key] = sub_data
            
            # 创建用户关联
            if sub_data.get('user_id'):
                user_sub = UserSubscription(
                    user_id=sub_data['user_id'],
                    subscription_id=sub_data['id'],
                    threshold=sub_data['threshold'],
                    email_recipients=sub_data['email_recipients'],
                    is_active=sub_data['is_active']
                )
                user_subscriptions_to_create.append(user_sub)
        else:
            # 多个订阅，优先保留有历史数据的
            subs_with_history = []
            subs_without_history = []
            
            for sub_data in subs:
                history_count = session.exec(
                    select(func.count(ElectricityHistory.id)).where(
                        ElectricityHistory.subscription_id == sub_data['id']
                    )
                ).first() or 0
                
                if history_count > 0:
                    subs_with_history.append((sub_data, history_count))
                else:
                    subs_without_history.append(sub_data)
            
            if subs_with_history:
                # 选择历史记录最多的
                keep_sub_data, _ = max(subs_with_history, key=lambda x: x[1])
                subscriptions_to_keep[room_code_key] = keep_sub_data
                
                # 删除其他的（包括没有历史数据的）
                for sub_data, _ in subs_with_history:
                    if sub_data['id'] != keep_sub_data['id']:
                        subscriptions_to_delete.append(sub_data)
                for sub_data in subs_without_history:
                    subscriptions_to_delete.append(sub_data)
                
                # 为保留的订阅创建所有用户的关联
                for sub_data in subs:
                    if sub_data['id'] == keep_sub_data['id']:
                        if sub_data.get('user_id'):
                            user_sub = UserSubscription(
                                user_id=sub_data['user_id'],
                                subscription_id=sub_data['id'],
                                threshold=sub_data['threshold'],
                                email_recipients=sub_data['email_recipients'],
                                is_active=sub_data['is_active']
                            )
                            user_subscriptions_to_create.append(user_sub)
                    else:
                        # 为被删除的订阅的用户创建关联到保留的订阅
                        if sub_data.get('user_id'):
                            existing = session.exec(
                                select(UserSubscription).where(
                                    UserSubscription.user_id == sub_data['user_id'],
                                    UserSubscription.subscription_id == keep_sub_data['id']
                                )
                            ).first()
                            
                            if not existing:
                                user_sub = UserSubscription(
                                    user_id=sub_data['user_id'],
                                    subscription_id=keep_sub_data['id'],
                                    threshold=sub_data['threshold'],
                                    email_recipients=sub_data['email_recipients'],
                                    is_active=sub_data['is_active']
                                )
                                user_subscriptions_to_create.append(user_sub)
            else:
                # 都没有历史数据，选择最新的
                keep_sub_data = max(subs, key=lambda x: x['created_at'])
                subscriptions_to_keep[room_code_key] = keep_sub_data
                
                # 删除其他的
                for sub_data in subs:
                    if sub_data['id'] != keep_sub_data['id']:
                        subscriptions_to_delete.append(sub_data)
                
                # 为保留的订阅创建所有用户的关联
                for sub_data in subs:
                    if sub_data['id'] == keep_sub_data['id']:
                        if sub_data.get('user_id'):
                            user_sub = UserSubscription(
                                user_id=sub_data['user_id'],
                                subscription_id=sub_data['id'],
                                threshold=sub_data['threshold'],
                                email_recipients=sub_data['email_recipients'],
                                is_active=sub_data['is_active']
                            )
                            user_subscriptions_to_create.append(user_sub)
                    else:
                        if sub_data.get('user_id'):
                            existing = session.exec(
                                select(UserSubscription).where(
                                    UserSubscription.user_id == sub_data['user_id'],
                                    UserSubscription.subscription_id == keep_sub_data['id']
                                )
                            ).first()
                            
                            if not existing:
                                user_sub = UserSubscription(
                                    user_id=sub_data['user_id'],
                                    subscription_id=keep_sub_data['id'],
                                    threshold=sub_data['threshold'],
                                    email_recipients=sub_data['email_recipients'],
                                    is_active=sub_data['is_active']
                                )
                                user_subscriptions_to_create.append(user_sub)
    
    print(f"\n将保留 {len(subscriptions_to_keep)} 个订阅")
    print(f"将删除 {len(subscriptions_to_delete)} 个重复订阅")
    print(f"将创建 {len(user_subscriptions_to_create)} 个用户-订阅关联")
    
    if subscriptions_to_delete:
        print("\n将被删除的订阅:")
        for sub_data in subscriptions_to_delete:
            history_count = session.exec(
                select(func.count(ElectricityHistory.id)).where(
                    ElectricityHistory.subscription_id == sub_data['id']
                )
            ).first() or 0
            print(f"  - {sub_data['room_name']} (ID: {sub_data['id']}, 用户: {sub_data['user_id']}, 历史记录: {history_count})")
    
    if dry_run:
        print("\n这是预览模式，不会实际执行迁移")
        print("运行脚本时添加 --execute 参数来实际执行")
        return
    
    # 实际执行
    print("\n开始执行迁移...")
    
    # 1. 删除重复订阅的历史记录
    deleted_history_count = 0
    for sub_data in subscriptions_to_delete:
        history_records = session.exec(
            select(ElectricityHistory).where(
                ElectricityHistory.subscription_id == sub_data['id']
            )
        ).all()
        for history in history_records:
            session.delete(history)
            deleted_history_count += 1
    
    # 2. 删除重复订阅
    for sub_data in subscriptions_to_delete:
        sub = session.exec(select(Subscription).where(Subscription.id == sub_data['id'])).first()
        if sub:
            session.delete(sub)
    
    # 3. 创建用户-订阅关联
    for user_sub in user_subscriptions_to_create:
        existing = session.exec(
            select(UserSubscription).where(
                UserSubscription.user_id == user_sub.user_id,
                UserSubscription.subscription_id == user_sub.subscription_id
            )
        ).first()
        if not existing:
            session.add(user_sub)
    
    session.commit()
    
    print(f"\n迁移完成:")
    print(f"  - 删除了 {len(subscriptions_to_delete)} 个重复订阅")
    print(f"  - 删除了 {deleted_history_count} 条历史记录")
    print(f"  - 创建了 {len(user_subscriptions_to_create)} 个用户-订阅关联")
    
    # 4. 删除 user_id 列（需要 SQL）
    print("\n删除 subscriptions 表的 user_id 列...")
    try:
        session.exec(text("ALTER TABLE subscriptions DROP COLUMN IF EXISTS user_id;"))
        session.commit()
        print("✓ 已删除 user_id 列")
    except Exception as e:
        print(f"删除 user_id 列失败: {e}")
        print("请手动运行: ALTER TABLE subscriptions DROP COLUMN IF EXISTS user_id;")


def main():
    import argparse
    parser = argparse.ArgumentParser(description='迁移到共享订阅模式')
    parser.add_argument('--execute', action='store_true', help='实际执行迁移（默认是预览模式）')
    args = parser.parse_args()
    
    init_db()
    
    with Session(engine) as session:
        migrate_data(session, dry_run=not args.execute)


if __name__ == '__main__':
    main()
