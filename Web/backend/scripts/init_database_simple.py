#!/usr/bin/env python3
"""
简单的数据库初始化脚本（不依赖应用配置）
直接使用 SQL 创建表结构
"""
import sys

def get_init_sql():
    """返回初始化 SQL 语句"""
    return """
-- 创建用户表
CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    hashed_password VARCHAR(255) NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_users_username ON users(username);
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);

-- 创建订阅表
CREATE TABLE IF NOT EXISTS subscriptions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    room_name VARCHAR(100) NOT NULL,
    area_id VARCHAR(50) NOT NULL,
    building_code VARCHAR(50) NOT NULL,
    floor_code VARCHAR(50) NOT NULL,
    room_code VARCHAR(50) NOT NULL,
    threshold FLOAT DEFAULT 20.0,
    email_recipients JSONB DEFAULT '[]'::jsonb,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_subscriptions_user_id ON subscriptions(user_id);
CREATE INDEX IF NOT EXISTS idx_subscriptions_room_name ON subscriptions(room_name);
CREATE INDEX IF NOT EXISTS idx_subscriptions_is_active ON subscriptions(is_active);

-- 创建历史数据表
CREATE TABLE IF NOT EXISTS electricity_history (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    subscription_id UUID NOT NULL REFERENCES subscriptions(id) ON DELETE CASCADE,
    surplus FLOAT NOT NULL,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_history_subscription_id ON electricity_history(subscription_id);
CREATE INDEX IF NOT EXISTS idx_history_timestamp ON electricity_history(timestamp);

-- 创建配置表
CREATE TABLE IF NOT EXISTS config (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    key VARCHAR(100) UNIQUE NOT NULL,
    value JSONB DEFAULT '{}'::jsonb,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_config_user_id ON config(user_id);
CREATE INDEX IF NOT EXISTS idx_config_key ON config(key);

-- 创建日志表
CREATE TABLE IF NOT EXISTS logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    level VARCHAR(20) NOT NULL,
    message TEXT NOT NULL,
    module VARCHAR(100),
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_logs_level ON logs(level);
CREATE INDEX IF NOT EXISTS idx_logs_module ON logs(module);
CREATE INDEX IF NOT EXISTS idx_logs_timestamp ON logs(timestamp);
"""


def main():
    """主函数"""
    sql = get_init_sql()
    
    print("=" * 60)
    print("数据库初始化 SQL 脚本")
    print("=" * 60)
    print("\n请使用以下命令执行初始化：")
    print("\n方法1: 使用 psql")
    print("  sudo -u postgres psql -d electricity_db -f - << 'EOF'")
    print(sql)
    print("EOF")
    print("\n方法2: 直接执行 SQL")
    print("  sudo -u postgres psql electricity_db")
    print("  然后粘贴以下 SQL 语句：\n")
    print(sql)
    print("\n方法3: 保存为文件后执行")
    print("  将 SQL 保存到 init.sql，然后执行：")
    print("  sudo -u postgres psql -d electricity_db -f init.sql")
    print("\n" + "=" * 60)
    
    # 询问是否要保存 SQL 文件
    save_file = input("\n是否要将 SQL 保存到 init.sql 文件？(y/n): ").strip().lower()
    if save_file == 'y':
        with open('init.sql', 'w', encoding='utf-8') as f:
            f.write(sql)
        print("✓ SQL 已保存到 init.sql")
        print("执行: sudo -u postgres psql -d electricity_db -f init.sql")


if __name__ == "__main__":
    main()



