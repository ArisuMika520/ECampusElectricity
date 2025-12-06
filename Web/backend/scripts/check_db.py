#!/usr/bin/env python3
"""检查数据库连接和表结构"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.database import engine
from sqlmodel import text, Session
from app.models.user import User

try:
    with Session(engine) as session:
        # 检查 users 表是否存在
        result = session.exec(text("SELECT COUNT(*) FROM information_schema.tables WHERE table_name = 'users'"))
        table_exists = result.scalar() > 0
        
        if not table_exists:
            print("❌ users 表不存在！")
            print("请先运行: sudo -u postgres psql -d electricity_db -f scripts/init.sql")
            sys.exit(1)
        
        print("✓ users 表存在")
        
        # 检查 is_admin 字段是否存在
        result = session.exec(text("""
            SELECT COUNT(*) FROM information_schema.columns 
            WHERE table_name = 'users' AND column_name = 'is_admin'
        """))
        has_admin_column = result.scalar() > 0
        
        if not has_admin_column:
            print("⚠️  is_admin 字段不存在，需要迁移")
            print("运行: sudo -u postgres psql -d electricity_db -f scripts/add_admin_column.sql")
        else:
            print("✓ is_admin 字段存在")
        
        # 检查用户数量
        users = list(session.exec(text("SELECT COUNT(*) FROM users")).all())
        user_count = users[0] if users else 0
        print(f"✓ 当前用户数量: {user_count}")
        
        if user_count == 0:
            print("\n提示: 首次登录将自动创建管理员账号")
        else:
            # 列出所有用户
            if has_admin_column:
                all_users = session.exec(text("SELECT username, is_admin, is_active FROM users")).all()
                print("\n现有用户:")
                for user in all_users:
                    print(f"  - {user[0]} (管理员: {user[1]}, 活跃: {user[2]})")
            else:
                all_users = session.exec(text("SELECT username, is_active FROM users")).all()
                print("\n现有用户:")
                for user in all_users:
                    print(f"  - {user[0]} (活跃: {user[1]})")
        
except Exception as e:
    print(f"❌ 数据库连接失败: {e}")
    print("\n请检查:")
    print("1. PostgreSQL 服务是否运行")
    print("2. 数据库 electricity_db 是否已创建")
    print("3. .env 文件中的 DATABASE_URL 是否正确")
    sys.exit(1)

