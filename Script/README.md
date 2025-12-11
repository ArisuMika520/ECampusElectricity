# 电费追踪器脚本（数据库版本）

## 说明

`elect_tracker_db.py` 是原 `Bot/scripts/Elect_tracker.py` 的数据库版本改造。

## 主要改动

1. **数据源**：从JSON文件读取订阅改为从数据库读取活跃订阅（`Subscription`表，`is_active=True`）
2. **数据存储**：历史记录写入数据库（`ElectricityHistory`表）而不是JSON文件
3. **核心逻辑保持不变**：
   - 定时查询所有活跃订阅的电费
   - 2小时去重逻辑（如果电费值相同且时间差小于2小时，不保存）
   - 自动清理超出限制的历史记录（默认上限2400条）

## 使用方法

### 前置要求

1. 确保Web后端数据库已初始化并包含订阅数据
2. 确保Bot配置文件 `Bot/config.yaml` 存在且配置正确
3. 确保Web后端配置文件 `Web/backend/.env` 存在且数据库连接配置正确

### 运行脚本

```bash
cd /home/arisu/pro/ECampusElectricity/Script
python elect_tracker_db.py
```

### 配置说明

- **查询间隔**：从 `Bot/config.yaml` 的 `tracker.check_interval` 读取（默认3600秒）
- **历史记录上限**：从Web后端配置的 `HISTORY_LIMIT` 读取（默认2400条）
- **数据库连接**：从Web后端配置的 `DATABASE_URL` 读取

### 日志

脚本会输出日志到：
- 控制台（标准输出）
- 文件：`tracker_log.log`（脚本运行目录）

## 与原脚本的对比

| 功能 | 原脚本（JSON版本） | 新脚本（数据库版本） |
|------|-------------------|---------------------|
| 订阅来源 | JSON文件 | 数据库 `subscriptions` 表 |
| 历史存储 | JSON文件 | 数据库 `electricity_history` 表 |
| 查询逻辑 | 相同（使用Bot的查询方法） | 相同 |
| 去重逻辑 | 相同（2小时去重） | 相同 |
| 数据清理 | 相同（超出上限自动清理） | 相同 |

## 注意事项

1. 脚本需要同时访问Bot和Web后端的代码，确保路径配置正确
2. 确保数据库连接正常，否则脚本会报错并重试
3. 脚本会持续运行，使用 `Ctrl+C` 可以中断

