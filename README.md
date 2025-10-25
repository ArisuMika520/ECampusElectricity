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
* [x] 实现数据库偏移自动更新、异常处理
      
## 🔄 未来更新计划
* [ ] 为mode1新增mode2也有的功能（通过被动触发）
* [ ] 将mode1与mode2进行融合
* [ ] 实现QQ机器人的id绑定，一键查询

## 🏗️ 项目模式
* mode1使用邮箱告警，采用STMP，默认QQ邮箱，其他自行更改
* mode2则采用QQ机器人，需学QQ机器人（官方API）的使用和部署，可以通过机器人查询指定寝室的电费

## ❗‼️⁉️警告
现在最新版的易校园已经似乎已经抓不到相关数据了，目前只有老的cookie生效，目前正在想办法进行脚本破解，但是本人并非网安技术栈方向，所以不知道能不能做出来。

## 🚀 快速开始
* 模拟器或者安卓手机安装 ***易校园*** 和 ***HttpCanary***，IOS手机则安装***易校园*** 和 ***Stream***
（具体抓包方法自行搜索学习）
* 登录易校园后开启抓包，在里面点一点东西，随后在 ***HttpCanary***或者***Stream***抓到的包中看参数
* 需要找到两个参数：**shiroJID** 和 **ymId**
  （**shiroJID** 在cookie里 / **ymId** 是一串数字）
* 随后在代码中找到**shiroJID**和**ymId**，相应填入即可
* mode2的机器人快速开始不了，需要根据个人具体情况进行部分的重构（例如图床API，appid等）

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
│       │   ├── Electricity.py         # 封装所有与电费查询相关的API交互
│       │   └── Building.py            # 负责提供楼栋数据索引
│       │
│       ├── data/                      # 数据模块
│       │   ├── __init__.py
│       │   └── sub_storage.py         # 负责JSON文件的读写（订阅信息、历史记录）
│       │
│       ├── bot/                       # Bot相关模块
│       │   ├── __init__.py
│       │   ├── bot_command.py         # 存放所有具体的命令方法（如订阅、查询）
│       │   └── Elect_bot.py           # 机器人入口，负责启动和注册处理器
│       │
│       └── utils/                     # 工具函数模块
│           ├── __init__.py
│           ├── plotter.py             # 专门用于绘制电费历史折线图
│           ├── image_uploader.py      # 图片上传图床的脚本
│           └── predictor.py           # 专门用于预测剩余时间的逻辑
│
├── scripts/                         # 独立脚本目录
│   └── Elect_tracker.py             # 重构后的电费定时追踪脚本
│
├── data_files/                      # 存放数据
│   ├── sub.json                     # 订阅数据
│   ├── his.json                     # 历史数据
│   ├── image_upload_records.json    # 图床上传的旧图片key（负责删除旧图片）
│   └── plot/                        # 图形数据
│
├── assets/                          # 存放静态
│   └── fonts/
│       ├── YaHei Ubuntu Mono.ttf
│       └── simhei.ttf
│
├── tests/                           # 测试代码目录
│
├── config.yaml.example              # 配置模板
├── .gitignore
└── README.md
```

## 详细分析文档

[![Ask DeepWiki](https://deepwiki.com/badge.svg)](https://deepwiki.com/ArisuMika520/ECampusElectricity)

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

## 注意:
<div>
<p>本项目的buildingData数据只适用于本人学校，如需修改，请通过遍历抓取字典中的所有楼寝室与对应的索引</p>
<p>跟据具体寝室结构调整具体代码（如果你要用mode2的话）</p>
</div>



## 参考
参照 [Example](https://github.com/ArisuMika520/ECampusElectricity/tree/main/example) 
