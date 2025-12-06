# 管理员功能迁移指南

## 数据库迁移

如果数据库已经存在，需要添加 `is_admin` 字段：

```bash
cd backend/scripts
sudo -u postgres psql -d electricity_db -f add_admin_column.sql
```

或者手动执行：

```sql
ALTER TABLE users ADD COLUMN IF NOT EXISTS is_admin BOOLEAN DEFAULT FALSE;
CREATE INDEX IF NOT EXISTS idx_users_is_admin ON users(is_admin);
```

## 功能说明

### 1. 首次登录自动创建管理员

- 当数据库中没有任何用户时，第一个登录的用户会自动创建并成为管理员
- 使用任意用户名和密码即可登录
- 邮箱会自动设置为 `{username}@admin.local`

### 2. 注册功能控制

- 默认情况下，注册功能是关闭的
- 管理员可以在"管理员面板"中开启/关闭注册功能
- 当注册关闭时，用户无法通过注册页面创建账号

### 3. 管理员功能

管理员可以：
- 查看所有用户列表
- 创建新用户（可设置是否为管理员）
- 启用/停用用户
- 修改用户信息
- 开启/关闭注册功能

### 4. 管理员面板访问

- 只有管理员可以看到导航栏中的"管理员"链接
- 非管理员访问 `/admin` 会被重定向到仪表盘

## API 端点

### 管理员 API（需要管理员权限）

- `GET /api/admin/users` - 获取所有用户列表
- `POST /api/admin/users` - 创建新用户
- `PUT /api/admin/users/{id}` - 更新用户信息
- `DELETE /api/admin/users/{id}` - 删除用户
- `GET /api/admin/system/config` - 获取系统配置
- `PUT /api/admin/system/config` - 更新系统配置（开关注册）

### 认证 API

- `POST /api/auth/login` - 登录（首次登录自动创建管理员）
- `POST /api/auth/register` - 注册（需要注册功能开启）
- `GET /api/auth/me` - 获取当前用户信息

## 使用流程

1. **首次使用**：
   - 访问登录页面
   - 输入任意用户名和密码
   - 系统自动创建管理员账号并登录

2. **管理员操作**：
   - 登录后，导航栏会显示"管理员"链接
   - 进入管理员面板
   - 可以创建其他用户
   - 可以开启/关闭注册功能

3. **普通用户**：
   - 如果注册功能开启，可以通过注册页面创建账号
   - 或者由管理员创建账号



