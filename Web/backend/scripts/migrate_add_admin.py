#!/usr/bin/env python3
"""添加 is_admin 字段到 users 表"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.database import engine
from sqlmodel import text, Session

def main():
    """添加 is_admin 字段"""
    try:
        with Session(engine) as session:
            # 检查字段是否已存在
            result = session.exec(text("""
                SELECT COUNT(*) FROM information_schema.columns 
                WHERE table_name = 'users' AND column_name = 'is_admin'
            """))
            exists = result.scalar() > 0
            
            if exists:
                print("✓ is_admin 字段已存在，无需迁移")
                return
            
            print("正在添加 is_admin 字段...")
            
            # 添加字段
            session.exec(text("ALTER TABLE users ADD COLUMN is_admin BOOLEAN DEFAULT FALSE"))
            session.commit()
            
            # 创建索引
            session.exec(text("CREATE INDEX IF NOT EXISTS idx_users_is_admin ON users(is_admin)"))
            session.commit()
            
            print("✓ 成功添加 is_admin 字段")
            print("✓ 成功创建索引")
            
            # 将现有用户设置为非管理员（如果字段刚添加，默认值已经是 FALSE）
            print("\n提示: 现有用户默认不是管理员")
            print("如果需要将某个用户设置为管理员，可以在数据库中执行:")
            print("  UPDATE users SET is_admin = TRUE WHERE username = 'your_username';")
            
    except Exception as e:
        print(f"❌ 迁移失败: {e}")
        print("\n如果遇到权限问题，请使用 SQL 脚本:")
        print("  sudo -u postgres psql -d electricity_db -f scripts/add_admin_column.sql")
        sys.exit(1)

if __name__ == "__main__":
    main()



