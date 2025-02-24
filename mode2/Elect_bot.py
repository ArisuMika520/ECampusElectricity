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

# 读取配置文件
config = read(os.path.join(os.path.dirname(__file__), "config.yaml"))
_log = logging.get_logger()

class ElectricityMonitor:
    def __init__(self, config: Dict):
        self.config = config
        self.ece = Electricity.ECampusElectricity(config["electricity"])

    async def query_electricity(self):
        """查询电费"""
        # 获取校区    
        area_info = self.ece.query_area()
        area_id = area_info['data'][0]['id']
        
        # 获取宿舍楼
        building_list = self.ece.query_building(area_id)
        building_code = building_list['data'][0]['buildingCode']
        
        # 获取楼层
        floor_list = self.ece.query_floor(area_id, building_code)
        floor_code = floor_list['data'][0]['floorCode']
        
        # 获取房间
        room_list = self.ece.query_room(area_id, building_code, floor_code)
        room_code = room_list['data'][0]['roomCode']
        
        # 获取电费信息
        room_info = self.ece.query_room_surplus(area_id, building_code, floor_code, room_code)
        return (
            room_info['data']['surplus'],
            room_info['data']['roomName']
        )

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
                surplus, room_name = await self.monitor.query_electricity()
                await message._api.post_c2c_message(
                    openid=message.author.user_openid,
                    msg_type=0, msg_id=message.id,
                    content=f"⚠️电费预警⚠️\n房间：{room_name}\n当前余额：{surplus}元"
                )
            except Exception as e:
                _log.error(f"查询失败: {str(e)}")
                await message._api.post_c2c_message(
                    openid=message.author.user_openid,
                    msg_type=0, msg_id=message.id,
                    content="⚠️ 电费查询失败，请稍后再试"
                )
        else:
            await self.send_help(message)
            
    async def on_group_at_message_create(self, message: GroupMessage):
        if message.content.strip() == "查询电费":
            surplus, room_name = await self.monitor.query_electricity()
            await message._api.post_group_message(
                group_openid=message.group_openid,
                msg_type=0, 
                msg_id=message.id,
                content=f"⚠️电费预警⚠️\n房间：{room_name}\n当前余额：{surplus}元"
            )
        else:
            await self.send_group_help(message)
    
    async def send_group_help(self, message: GroupMessage):
        """发送帮助信息"""
        help_text = """
        🤖 电费机器人使用指南：
        1. 查询电费：发送「查询电费」
        2. 订阅提醒：发送「订阅电费 房间号 阈值」
        示例：订阅电费 D9-402 20
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
        🤖 电费机器人使用指南：
        1. 查询电费：发送「查询电费」
        2. 订阅提醒：发送「订阅电费 房间号 阈值」
        示例：订阅电费 D9-402 20
        """
        await message._api.post_c2c_message(
            openid=message.author.user_openid,
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
