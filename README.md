# ECampusElectricity
采用易校园大学寝室电费获取，可查询电费，电费余额告警（邮箱告警和QQ机器人告警）

# 出现的缘由
闲来无事，周末寝室玩游戏，但是电费不足停电了，气死我了！
遂写了一个电费自动告警程序

# 已实现功能
* [x] 通过易校园抓取寝室电费
* [x] 设置电费阈值与邮箱告警
* [x] 接入QQ机器人，在QQ就可以随时查询电费

# 未来更新计划
* [ ] 实现QQ机器人的id绑定，一键查询
* [ ] 历史电费数据分析

# 告警模式
* mode1使用邮箱告警，采用STMP，默认QQ邮箱，其他自行更改
* mode2则采用QQ机器人，需学QQ机器人（官方API）的使用和部署，可以通过机器人查询指定寝室的电费

# 开始
* 模拟器或者安卓手机安装 ***易校园*** 和 ***HttpCanary***，IOS手机则安装***易校园*** 和 ***Stream***
（具体抓包方法自行搜索学习）
* 登录易校园后开启抓包，在里面点一点东西，随后在 ***HttpCanary***或者***Stream***抓到的包中看参数
* 需要找到两个参数：**shiroJID** 和 **ymId**
  （**shiroJID** 在cookie里 / **ymId** 是一串数字）
* 随后在代码中找到**shiroJID**和**ymId**，相应填入即可
（mode1翻一翻就找到了，mode2在config.yaml里）

# 注意：
本项目的buildingData数据只适用于本人学校，如需修改，请通过遍历抓取字典中的所有楼寝室与对应的索引

# 参考
参照 [Example](https://github.com/ArisuMika520/ECampusElectricity/tree/main/example) 
