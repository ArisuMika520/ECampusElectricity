# 项目结构说明

## 项目组织方式

本项目采用**单分支（main）共存**的方式，包含两个独立的实现版本：

- **Web 版本** (`Web/` 目录): FastAPI + Next.js WebUI 实现
- **Bot 版本** (`Bot/` 目录): QQ 机器人实现

两个版本**共存于 main 分支**，用户可以根据自己的需求选择使用。

## 目录结构

```
ECampusElectricity/
├── Web/                    # WebUI 版本（FastAPI + Next.js）
│   ├── backend/            # FastAPI 后端
│   ├── frontend/           # Next.js 前端
│   └── scripts/            # 启动脚本
├── Bot/                    # QQ 机器人版本
│   ├── src/
│   ├── scripts/
│   └── data_files/
├── example/                # 示例文件
├── scripts/                # 工具脚本
├── README.md               # 主文档
└── LICENSE                 # 许可证
```

## 如何选择版本

### 选择 Web 版本，如果您需要：
- ✅ 现代化的 Web 界面
- ✅ 多用户支持
- ✅ 数据库存储（PostgreSQL）
- ✅ 实时日志监控
- ✅ 历史数据可视化
- ✅ 管理员面板

### 选择 Bot 版本，如果您需要：
- ✅ QQ 机器人交互
- ✅ 简单部署（无需数据库）
- ✅ 个人使用
- ✅ JSON 文件存储

## 使用说明

### Web 版本

详细文档请查看 [Web/README.md](Web/README.md)

```bash
cd Web
npm run setup
npm run dev
```

### Bot 版本

详细文档请查看 [Bot/README.md](Bot/README.md)（如果存在）

```bash
cd Bot
pip install -r requirements.txt
python src/bot/Elect_bot.py
```

## 注意事项

1. **两个版本独立**: Web 和 Bot 版本是完全独立的，可以单独使用
2. **数据不共享**: Web 版本使用 PostgreSQL，Bot 版本使用 JSON 文件
3. **配置独立**: 每个版本都有自己的配置文件
4. **可以共存**: 可以在同一台服务器上同时运行两个版本

## 迁移数据

如果您之前使用 Bot 版本，现在想迁移到 Web 版本：

```bash
cd Web
npm run db:migrate-mode2
```

这将从 `Bot/data_files/` 目录读取数据并导入到 PostgreSQL。

## 开发建议

- 开发 Web 版本时，在 `Web/` 目录下工作
- 开发 Bot 版本时，在 `Bot/` 目录下工作
- 两个版本的代码互不影响

## 常见问题

### Q: 可以同时使用两个版本吗？
A: 可以，但需要分别配置，数据不会自动同步。

### Q: 如何从 Bot 迁移到 Web？
A: 使用 `npm run db:migrate-mode2` 命令迁移数据。

### Q: 两个版本有什么区别？
A: Web 版本提供 WebUI 界面和数据库存储，Bot 版本提供 QQ 机器人交互和 JSON 存储。

---

**注意**: 本项目不再使用分支分离的方式，所有代码都在 main 分支上。
