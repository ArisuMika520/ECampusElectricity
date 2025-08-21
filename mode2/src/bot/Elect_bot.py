'''
QQ机器人的主交互逻辑

Refactor by ArisuMika
'''
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
import datetime
import bot_command

# 读取配置文件
config = read(os.path.join(os.path.dirname(__file__), '..', '..', 'config.yaml'))
_log = logging.get_logger()

# 机器人交互逻辑
class EnhancedQQBot(botpy.Client):
    def __init__(self, intents):
        super().__init__(intents=intents)

    async def on_ready(self):
        _log.info(f"机器人「{self.robot.name}」已上线！")
    # Group群聊交互逻辑
    async def on_group_at_message_create(self, message: GroupMessage):
        content = message.content.strip()
        # 查询指定电费
        if content.startswith("/查询指定电费"):
            if (bot_command.Content_split.query_electricity(content)):
                area,buildIndex,floor,roomNum = bot_command.Content_split.query_electricity(content)
                surplus, room_name = bot_command.ElectricityMonitor.query_electricity(area,buildIndex,floor,roomNum)
                now = datetime.datetime.now()
                formatted_time = now.strftime("%Y-%m-%d %H:%M:%S")
                await message._api.post_group_message(
                    group_openid=message.group_openid,
                    msg_type=0, 
                    msg_id=message.id,
                    content=f"""啊呀，居然想指定查询！真是麻烦呐~！┑(￣Д ￣)┍\n查询时间：{formatted_time}\n⚡ 当前电费：{surplus}元\n房间：{room_name}\n这是谁的寝室呢~"""
                )
            else:
                await self.send_group_help(message)
                
        # 订阅寝室Tracker
        elif content.startswith("/订阅"):
            if (bot_command.Content_split.subscrip(content)):
                room_name = bot_command.Content_split.subscrip(content)
                result = bot_command.Subscrip.add(room_name)
                await message._api.post_group_message(
                        group_openid=message.group_openid,
                        msg_type=0, 
                        msg_id=message.id,
                        content=f"""{result}"""
                    )
            else:
                await self.send_group_help(message)
        
        # 取消订阅寝室Tracker
        elif content.startswith("/取消订阅"):
            if (bot_command.Content_split.subscrip(content)):
                room_name = bot_command.Content_split.subscrip(content)
                result = bot_command.Subscrip.remove(room_name)
                await message._api.post_group_message(
                        group_openid=message.group_openid,
                        msg_type=0, 
                        msg_id=message.id,
                        content=f"""{result}"""
                    )
            else:
                await self.send_group_help(message)
            
        # 预测指定寝室电费
        elif content.startswith("/预测"):
            if (bot_command.Content_split.predict(content)):
                room_name,time_span = bot_command.Content_split.predict(content)
                result = bot_command.predict.predict_day(room_name,time_span)
                await message._api.post_group_message(
                        group_openid=message.group_openid,
                        msg_type=0, 
                        msg_id=message.id,
                        content=f"""{result}"""
                    )
            else:
                await self.send_group_help(message)
                
                
        # 电费图形化
        elif content.startswith("/图形化"):
            if (bot_command.Content_split.plot(content)):
                plot_params = bot_command.Content_split.plot(content)
                if plot_params:
                    result_dict = bot_command.plot.process(
                        plot_type=plot_params["type"],
                        room_name=plot_params["room_name"],
                        time_span=plot_params["time_span"]
                    )
                    
                    if result_dict.get("code") == 200:
                        try:
                            image_url = result_dict.get("url")
                            if not image_url:
                                raise ValueError("图床返回的URL为空")
    
                            _log.info(f"正在将图片URL上传到图床: {image_url}")
                            upload_media = await message._api.post_group_file(
                                group_openid=message.group_openid,
                                file_type=1,
                                url=image_url
                            )
                            _log.info("URL上传成功，获取到Media对象。")
    
                            await message._api.post_group_message(
                                group_openid=message.group_openid,
                                msg_type=7,
                                msg_id=message.id,
                                media=upload_media
                            )
                            _log.info("富媒体消息发送成功！")
    
                        except Exception as e:
                            _log.error(f"发送富媒体消息过程中出现异常: {e}")
                            await message._api.post_group_message(
                                group_openid=message.group_openid,
                                msg_type=0,
                                content=f"图片已生成，但在发送时遇到问题，请联系管理员。错误: {e}",
                                msg_id=message.id
                            )
                    else:
                        error_info = result_dict.get("info", "未知错误，请查看后台日志。")
                        await message._api.post_group_message(
                            group_openid=message.group_openid,
                            msg_type=0, 
                            content=f"❌ 操作失败: {error_info}",
                            msg_id=message.id
                        )
            else:
                await self.send_group_help(message)
        else:
            await self.send_group_help(message)
    
    async def send_group_help(self, message: GroupMessage):
        """发送帮助信息"""
        help_text = """
✡️ 电费机器人使用指南 ✡️
/查询指定电费 <楼栋> <房间号>
示例: /查询指定电费 10南 101
---
/订阅 <楼栋> <房间号>
示例: /订阅 D9东 101
---
/取消订阅 <楼栋> <房间号>
示例: /取消订阅 D9东 101
---
/预测 <楼栋> <房间号> [小时数]
小时数: 可选, 默认48
示例: /预测 10南 101 48
---
/图形化 <类型> <楼栋> <房间号> [小时数]
类型: 历史, 消耗
小时数: 可选, 默认48
示例: /图形化 历史 10南 101
示例: /图形化 消耗 D9东 101 72
        """
        await message._api.post_group_message(
                group_openid=message.group_openid,
                msg_type=0, 
                msg_id=message.id,
                content = help_text
                )

if __name__ == "__main__":
    
    # 配置机器人权限（启用私聊消息）
    intents = botpy.Intents(public_messages=True)
    
    # 启动机器人
    client = EnhancedQQBot(intents=intents)
    client.run(
        appid=config["qq"]["appid"],
        secret=config["qq"]["secret"]
    )


