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

## 🔄 未来更新计划
* [ ] 实现QQ机器人的id绑定，一键查询
* [ ] 对mode1的邮箱进行电费消耗预测，数据分析以及图形化服务

## 🏗️ 项目模式
* mode1使用邮箱告警，采用STMP，默认QQ邮箱，其他自行更改
* mode2则采用QQ机器人，需学QQ机器人（官方API）的使用和部署，可以通过机器人查询指定寝室的电费

## 🚀 快速开始
* 模拟器或者安卓手机安装 ***易校园*** 和 ***HttpCanary***，IOS手机则安装***易校园*** 和 ***Stream***
（具体抓包方法自行搜索学习）
* 登录易校园后开启抓包，在里面点一点东西，随后在 ***HttpCanary***或者***Stream***抓到的包中看参数
* 需要找到两个参数：**shiroJID** 和 **ymId**
  （**shiroJID** 在cookie里 / **ymId** 是一串数字）
* 随后在代码中找到**shiroJID**和**ymId**，相应填入即可
（mode1翻一翻就找到了，mode2在config.yaml里）

## ⚙️ 项目结构
### mode1
```
ECampusElectricity/
└── mode1/
     └── Electricity.py # 服务器后台脚本，查询电费和邮箱告警
```
### mode 2
```
ECampusElectricityBot/
├── src/
│   └── elect_bot/
│       ├── __init__.py
│       ├── core/                      # 核心逻辑模块
│       │   ├── __init__.py
│       │   ├── electricity.py         # 封装所有与电费查询相关的API交互
│       │   └── building.py            # 负责提供楼栋数据索引
│       │
│       ├── data/                      # 数据模块
│       │   ├── __init__.py
│       │   └── storage.py             # 负责JSON文件的读写（订阅信息、历史记录）
│       │
│       ├── bot/                       # Bot相关模块
│       │   ├── __init__.py
│       │   ├── handlers.py            # 存放所有具体的命令方法（如订阅、查询）
│       │   └── main.py                # 机器人入口，负责启动和注册处理器
│       │
│       └── utils/                     # 工具函数模块
│           ├── __init__.py
│           ├── plotter.py             # 专门用于绘制电费历史折线图
│           └── time_predictor.py      # 专门用于预测剩余时间的逻辑
│
├── scripts/                         # 独立脚本目录
│   └── tracker.py                   # 重构后的电费定时追踪脚本
│
├── data_files/                      # 存放数据
│   ├── sub.json
│   ├── his.json
│   ├── plot/                        # 存放曲线图
│   └── bot.log
│
├── assets/                          # 存放静态
│   └── fonts/
│       ├── YaHei Ubuntu Mono.ttf
│       └── simhei.ttf
│
├── tests/                           # 测试代码目录
│   ├── test_core.py
│   └── test_storage.py
│
├── config.yaml                      # 最终使用的配置文件
├── config.yaml.example              # 配置模板
├── .gitignore
└── README.md
```

## 📄 许可证

本项目采用 MIT 许可证 - 详情请参阅 [LICENSE](LICENSE) 文件
## 📬 联系我们

- **GitHub Issues**: [提交问题或建议](https://github.com/OpenEasyAgent/EasyAgent/issues)

---

<div align="center">
  <p>⭐️ 如果你喜欢这个项目，别忘了给它一个星！ ⭐️</p>
  <p>杜绝停电危机！</p>
</div>

---

## 注意：
本项目的buildingData数据只适用于本人学校，如需修改，请通过遍历抓取字典中的所有楼寝室与对应的索引

## 参考
参照 [Example](https://github.com/ArisuMika520/ECampusElectricity/tree/main/example) 
