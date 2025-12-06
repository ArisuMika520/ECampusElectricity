## ECampusElectricity
<div align="center"> 
  <p><strong>对于采用易校园的大学寝室电费获取</strong></p>
  <p>可查询电费，电费余额告警</p>
</div>

> **愿景**: 让大学生们及时得知电费情况，避免断电导致的不良影响

## 出现的缘由
闲来无事，周末寝室玩游戏，但是电费不足停电了，气死我了！
遂写了一个电费自动告警程序

## ✅ 已实现功能
* [x] 通过易校园抓取寝室电费
* [x] 设置电费阈值与邮箱告警
* [x] 接入QQ机器人，在QQ就可以随时查询电费
* [x] 实现电费消耗预测
* [x] 历史电费数据分析
* [x] 电费消耗/余额图形化
* [x] 实现数据库偏移缓存命中自动更新、异常处理
* [x] WebUI 图形化界面（FastAPI + Next.js）
* [x] PostgreSQL 数据库存储
* [x] 实时日志监控（WebSocket）
      
## 🏗️ 项目模式

本项目提供两种实现方式，**请根据您的需求选择**：

### 🌐 Web 版本（推荐）
- **位置**: `Web/` 目录
- **技术栈**: FastAPI + Next.js + PostgreSQL
- **特点**: 
  - 现代化的 WebUI 界面
  - 多用户认证系统
  - 实时日志监控
  - 历史数据可视化
  - 管理员面板
  - 数据库存储（PostgreSQL）
- **适用场景**: 需要 Web 界面管理、多用户使用、需要数据持久化

### 🤖 Bot 版本
- **位置**: `Bot/` 目录
- **技术栈**: Python + QQ 机器人 API
- **特点**:
  - QQ 机器人交互
  - 通过 QQ 查询电费
  - 电费消耗预测
  - 图形化展示
  - JSON 文件存储
- **适用场景**: 喜欢 QQ 机器人交互、简单部署、个人使用

## 🚀 快速开始

### 前置要求
- Python 3.10+
- Node.js 18+（仅 Web 版本需要）
- PostgreSQL 12+（仅 Web 版本需要）

### 抓取 shiroJID
* 模拟器或者安卓手机安装 ***易校园*** 和 ***HttpCanary***，IOS手机则安装***Stream***
* 登录易校园后开启抓包，在里面点一点东西
* 在抓到的包中找到参数：**shiroJID**（在 cookie 里）
* 将 **shiroJID** 填入代码配置中

### Web 版本快速开始

```bash
# 1. 进入 Web 目录
cd Web

# 2. 一键设置环境
npm run setup

# 3. 配置环境变量
cp backend/.env.example backend/.env
# 编辑 backend/.env，设置数据库连接等

# 4. 初始化数据库
npm run db:init

# 5. 启动开发模式
npm run dev
```

详细文档请查看 [Web/README.md](Web/README.md)

### Bot 版本快速开始

```bash
# 1. 进入 Bot 目录
cd Bot

# 2. 安装依赖
pip install -r requirements.txt

# 3. 配置 config.yaml
cp config.yaml.example config.yaml
# 编辑 config.yaml，填入 shiroJID、QQ 机器人配置等

# 4. 运行机器人
python src/bot/Elect_bot.py
```

**注意**: Bot 版本需要根据个人具体情况进行部分重构（例如图床API、appid等）

## ⚙️ 项目结构

```
ECampusElectricity/
├── Web/                    # WebUI 版本（FastAPI + Next.js）
│   ├── backend/            # FastAPI 后端
│   ├── frontend/           # Next.js 前端
│   └── scripts/            # 启动脚本
├── Bot/                    # QQ 机器人版本
│   ├── src/
│   │   ├── bot/           # Bot 相关模块
│   │   ├── core/          # 核心逻辑模块
│   │   ├── data/          # 数据模块
│   │   └── utils/         # 工具函数模块
│   ├── scripts/           # 独立脚本目录
│   ├── data_files/        # 存放数据（JSON）
│   └── assets/            # 存放静态资源
├── example/                # 示例文件
├── scripts/                # 工具脚本
├── README.md               # 本文件
└── LICENSE                 # 许可证
```

## 📖 详细文档

- **Web 版本**: 查看 [Web/README.md](Web/README.md)
- **Bot 版本**: 查看 [Bot/README.md](Bot/README.md)（如果存在）

## ❗ 警告

如果你是 iOS + 小程序抓不到相关数据，目前已找到解决方法，正在编写教程中。

## 📄 许可证

本项目采用 MIT 许可证 - 详情请参阅 [LICENSE](LICENSE) 文件

## 📬 联系我们

- **GitHub Issues**: [提交问题或建议](https://github.com/ArisuMika520/ECampusElectricity/issues)

---

<div align="center">
  <p>⭐️ 如果你喜欢这个项目，别忘了给它一个星！ ⭐️</p>
  <p>杜绝停电危机！</p>
</div>

---

## 注意

<div>
<p>本项目的 buildingData 数据只适用于本人学校，如需修改，请通过遍历抓取字典中的所有楼寝室与对应的索引</p>
<p>根据具体寝室结构调整具体代码（如果你要用 Bot 版本的话）</p>
</div>

## 参考

参照 [Example](https://github.com/ArisuMika520/ECampusElectricity/tree/main/example)
