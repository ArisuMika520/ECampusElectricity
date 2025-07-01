# -*- coding: utf-8 -*-
import asyncio
import os
from typing import Dict
import botpy
from botpy import logging
from botpy.ext.cog_yaml import read
from botpy.message import C2CMessage
from botpy.message import Message
from botpy.message import GroupMessage
import Electricity
import buildingData

# 读取配置文件
config = read(os.path.join(os.path.dirname(__file__), "config.yaml"))
_log = logging.get_logger()

class ElectricityMonitor:
    def __init__(self, config: Dict):
        self.config = config
        self.ece = Electricity.ECampusElectricity(config["electricity"])

    async def query_electricity(self,area,buildIndex,floor,roomNum):
        """查询电费"""
        surplus, room_name = Electricity.ECampusElectricity.get_myRoom(area,buildIndex,floor,roomNum,self.ece)
        return surplus,room_name

class EnhancedQQBot(botpy.Client):
    def __init__(self, intents, monitor: ElectricityMonitor):
        super().__init__(intents=intents)
        self.monitor = monitor

    async def on_ready(self):
        _log.info(f"机器人「{self.robot.name}」已上线！")

    async def monitor_task(self,user_id: str):
        """定时检测任务"""
        while True:
            surplus, room_name = await self.monitor.query_electricity()
            if(surplus < 200.0):
                alert_msg = (
                    f"⚠️ 电费告警！\n"
                    f"房间：{room_name}\n"
                    f"当前余额：{surplus}元\n"
                    f"阈值：200.0元\n"
                    "请及时充值！"
                )
                await self.api.post_c2c_message(openid=user_id,content=alert_msg)
            await asyncio.sleep(3600)
            # 这里添加定时检测逻辑

    async def on_c2c_message_create(self, message: C2CMessage):
        user_id = message.author.user_openid
        content = message.content.strip()
        
        if content == "查询电费":
            try:
                surplus, room_name = await self.monitor.query_electricity(1,14,3,24)
                await message._api.post_c2c_message(
                    openid=message.author.user_openid,
                    msg_type=0, msg_id=message.id,
                    content=f"""呼呼~杂鱼欧尼酱果然还是想到我了呢~！\n⚡ 当前电费：{surplus}元\n房间：{room_name}\n哦呀哦呀~还有一些呢！哼~"""
                )
            except Exception as e:
                _log.error(f"查询失败: {str(e)}")
                await message._api.post_c2c_message(
                    openid=message.author.user_openid,
                    msg_type=0, msg_id=message.id,
                    content="⚠️ 电费查询失败，请稍后再试"
                )
        elif content.startswith("/查询指定电费"):
            parts = message.content.strip().split(' ')
            if len(parts) < 3:
                await message._api.post_c2c_message(
                    openid=message.author.user_openid,
                    msg_type=0, msg_id=message.id,
                    content=f"⚠️ 参数不足"
                )
                raise ValueError("参数不足")
            else:
                if parts[1][0] == 'D':
                    area = 1
                    buildNum = parts[1]
                    buildIndex = buildingData.get_buildingIndex(area,buildNum)
                    floor = int(parts[2][0])-1
                    roomNum = int(parts[2][1:])-1
                    surplus, room_name = await self.monitor.query_electricity(area,buildIndex,floor,roomNum)
                    await message._api.post_c2c_message(
                        openid=message.author.user_openid,
                        msg_type=0, msg_id=message.id,
                        content=f"""啊呀，居然想指定查询！真是麻烦呐~！\n⚡ 当前电费：{surplus}元\n房间：{room_name}\n这是谁的寝室呢~"""
                    )
                else:
                    area = 0
                    buildNum = parts[1]
                    buildIndex = buildingData.get_buildingIndex(area,buildNum)
                    floor = int(parts[2][0])-1
                    roomNum = int(parts[2][1:])-1
                    surplus, room_name = await self.monitor.query_electricity(area,buildIndex,floor,roomNum)
                    await message._api.post_c2c_message(
                        openid=message.author.user_openid,
                        msg_type=0, msg_id=message.id,
                        content=f"""啊呀，居然想指定查询！真是麻烦呐~！\n⚡ 当前电费：{surplus}元\n房间：{room_name}\n这是谁的寝室呢~"""
                    )
        else:
            await self.send_help(message)
            
    async def on_group_at_message_create(self, message: GroupMessage):
        content = message.content.strip()
        if message.content.strip() == "查询电费":
            surplus, room_name = await self.monitor.query_electricity(1,14,3,24)
            await message._api.post_group_message(
                group_openid=message.group_openid,
                msg_type=0, 
                msg_id=message.id,
                content=f"""啊呀，居然想指定查询！真是麻烦呐~！\n⚡ 当前电费：{surplus}元\n房间：{room_name}\n这是谁的寝室呢~"""
                )
        elif message.content.strip() == "我爱你":
            await message._api.post_group_message(
                group_openid=message.group_openid,
                msg_type=0, 
                msg_id=message.id,
                content=f"啊呀，欧尼酱真的是~o(*////▽////*)q我也爱你呀~喵！ο(=•ω＜=)ρ⌒☆"
                )
        elif message.content.strip() == "爱你":
            await message._api.post_group_message(
                group_openid=message.group_openid,
                msg_type=0, 
                msg_id=message.id,
                content=f"欧尼酱！！！唔唔~~~（脸红害羞）"
                )
        elif message.content.strip() == "Ciallo～(∠・ω< )⌒★":
            await message._api.post_group_message(
                group_openid=message.group_openid,
                msg_type=0, 
                msg_id=message.id,
                content=f"欧尼酱！！！Ciallo～(∠・ω< )⌒★"
                )
        elif content.startswith("/查询指定电费"):
            parts = message.content.strip().split(' ')
            if len(parts) < 3:
                await message._api.post_group_message(
                    group_openid=message.group_openid,
                    msg_type=0, 
                    msg_id=message.id,
                    content=f"参数不足"
                )
                await self.send_help(message)
                raise ValueError("参数不足")
            if parts[1][0] == 'D':
                area = 1
                buildNum = parts[1]
                buildIndex = buildingData.get_buildingIndex(area,buildNum)
                floor = int(parts[2][0])-1
                roomNum = int(parts[2][1:])-1
                surplus, room_name = await self.monitor.query_electricity(area,buildIndex,floor,roomNum)
                await message._api.post_group_message(
                    group_openid=message.group_openid,
                    msg_type=0, 
                    msg_id=message.id,
                    content=f"""啊呀，居然想指定查询！真是麻烦呐~！┑(￣Д ￣)┍\n⚡ 当前电费：{surplus}元\n房间：{room_name}\n这是谁的寝室呢~"""
                )
            else:
                area = 0
                buildNum = parts[1]
                buildIndex = buildingData.get_buildingIndex(area,buildNum)
                floor = int(parts[2][0])-1
                roomNum = int(parts[2][1:])-1
                surplus, room_name = await self.monitor.query_electricity(area,buildIndex,floor,roomNum)
                await message._api.post_group_message(
                    group_openid=message.group_openid,
                    msg_type=0, 
                    msg_id=message.id,
                    content=f"""啊呀，居然想指定查询！真是麻烦呐~！┑(￣Д ￣)┍\n⚡ 当前电费：{surplus}元\n房间：{room_name}\n这是谁的寝室呢~"""
                )
        elif message.content.strip() == "你打d3吗":
            await message._api.post_group_message(
                group_openid=message.group_openid,
                msg_type=0, 
                msg_id=message.id,
                content=r"欧尼酱~！你什么意思！你还是自己加油吧！\(￣︶￣*\))"
                )
        elif message.content.strip() == "你打abc吗":
            await message._api.post_group_message(
                group_openid=message.group_openid,
                msg_type=0, 
                msg_id=message.id,
                content=r"欧尼酱~！信不信我揍你！Pia!(ｏ ‵-′)ノ”(ノ﹏<。)"
                )
        else:
            await self.send_group_help(message)
    
    async def send_group_help(self, message: GroupMessage):
        """发送帮助信息"""
        help_text = """
        ✡️电费机器人使用指南：
        1. 查询电费：发送「查询电费」
        2. 查阅指定电费：发送「查询指定电费 房间号」\n示例：西校区：\n✅查阅指定电费 10南 101\n格式：几号楼+东南西北（如果有就加，没有就不加）+寝室号
             东校区：\n✅查阅指定电费 D9东 101\n格式：D+几号楼+东南西北（如果有就加，没有就不加）+寝室号
        """
        await message._api.post_group_message(
                group_openid=message.group_openid,
                msg_type=0, 
                msg_id=message.id,
                content = help_text
                )
        
    async def send_help(self, message: C2CMessage):
        """发送帮助信息"""
        help_text = """
        ✡️电费机器人使用指南：
        1. 查询电费：发送「查询电费」
        2. 查阅指定电费：发送「查询指定电费 房间号」\n示例：西校区：\n✅查阅指定电费 10南 101\n格式：几号楼+东南西北（如果有就加，没有就不加）+寝室号
             东校区：\n✅查阅指定电费 D9东 101\n格式：D+几号楼+东南西北（如果有就加，没有就不加）+寝室号
        """
        await message._api.post_c2c_message(
            openid=message.author.user_openid,
            msg_type=0, msg_id=message.id,
            content=help_text
        )

if __name__ == "__main__":
    # 初始化监控模块
    monitor = ElectricityMonitor(config)
    
    # 配置机器人权限（启用私聊消息）
    intents = botpy.Intents(public_messages=True)
    
    # 启动机器人
    client = EnhancedQQBot(intents=intents, monitor=monitor)
    client.run(
        appid=config["qq"]["appid"],
        secret=config["qq"]["secret"]
    )
