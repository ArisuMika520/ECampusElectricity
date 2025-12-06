-- 添加 is_admin 字段到 users 表（如果字段不存在）
-- 执行方法: sudo -u postgres psql -d electricity_db -f add_admin_column.sql

-- 检查并添加 is_admin 字段
DO $$ 
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'users' AND column_name = 'is_admin'
    ) THEN
        ALTER TABLE users ADD COLUMN is_admin BOOLEAN DEFAULT FALSE;
        CREATE INDEX IF NOT EXISTS idx_users_is_admin ON users(is_admin);
        RAISE NOTICE 'Added is_admin column to users table';
    ELSE
        RAISE NOTICE 'is_admin column already exists';
    END IF;
END $$;



