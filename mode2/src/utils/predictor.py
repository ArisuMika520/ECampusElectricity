'''
负责qq机器人的有关预测的功能
- 用户查询电费使用情况、上次电费充值时间（区间）、预计剩余时间、预计停电时间

Build by Vanilla-chan (2025.7.18)

Refactor by ArisuMika (2025.7.25)
'''
import asyncio
import json
import os
import logging as pylog
# 该pylog在“仅调用本文件”时会输出到sub_log.log中，在“调用本文件的class”时可能会被bot的logging设置覆盖导致输出至botpy.log
pylog.basicConfig(
    level=pylog.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        pylog.FileHandler("sub_log.log", encoding='utf-8'), # 输出到文件
        pylog.StreamHandler()                               # 同时输出到控制台
    ]
)
from datetime import datetime, timedelta
import asyncio
from botpy.ext.cog_yaml import read
from typing import List, Dict, Any

config = read(os.path.join(os.path.dirname(__file__), '..', '..', 'config.yaml'))

class predictor:
    # 订阅列表文件路径
    SUBSCRIPTION_LIST_FILE = config['path']['SUBSCRIPTION_LIST_FILE'] # sub
    # 订阅历史文件路径
    SUBSCRIPTION_HISTORY_FILE = config['path']['SUBSCRIPTION_HISTORY_FILE'] # his
    # 时间字符串格式
    TIME_FORMAT = "%Y-%m-%d %H:%M:%S"
    # 绘图输出目录
    PLOT_DIR = config['path']['PLOT_DIR'] # plot
    def _load_json_file(self, filepath: str) -> Any:
        """安全地加载一个JSON文件，处理不存在或格式错误的情况。"""

        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return [] # 如果文件不存在或为空/损坏，返回一个空列表作为默认值

    def _save_json_file(self, filepath: str, data: Any) -> bool:
        """安全地保存数据到JSON文件。"""
        
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=4)
            return True
        except Exception as e:
            pylog.error(f"保存文件 '{filepath}' 时发生错误: {e}")
            return False
    # 预测
    def predict_day(self, room_name: str, time_span = 24) -> Dict:
        """
        查询某房间近24h的使用情况，并做出初步的预测
        返回类型：字典
        
        状态码：
        查询成功
            code: 100
            info: 
            avg_usage: 24h内平均使用电费（元）
            remaining_day: 预计还能用多久（天）
            outage_time: 预计什么时候停电（str）
            vaild_data_size: int, 有效数据量
            delta_timestamp: double, 时间跨度，表示有效的信息实际跨过了多少个小时

        没找到该房间
            code: 101
            info:

        存在该房间但是24h内数据过少
            code: 102
            info:
            vaild_data_size: int, 有效数据量

        存在该房间，数据量有，但是充值电费导致都是电费都是上升的，无法预测
            code: 103
            info: 
        
        存在该房间，数据量有，但是电费始终没有下降，可能是长期无人
            code: 104
            info
        """
        sub_his=self._load_json_file(self.SUBSCRIPTION_HISTORY_FILE)
        now_time=datetime.now()
        for item in sub_his:
            if room_name == item["name"]:
                vaild_data=[x for x in item["his"] if now_time - datetime.strptime(x["timestamp"], self.TIME_FORMAT) <= timedelta(hours=time_span)]
                # print(vaild_data)
                if len(vaild_data) <= 1:
                    return {
                        "code": 102,
                        "info": f"近 {time_span} 小时内数据太少了，多订阅一会儿吧！",
                        "vaild_data_size": len(vaild_data)
                    }
                # 计算近期数据的累计电费差
                delta_value=0
                # 计算近期数据的累计时间差
                delta_timestamp_seconds=0.0
                for idx,x in enumerate(vaild_data):
                    if idx+1==len(vaild_data):
                        continue
                    idy=idx+1
                    y=vaild_data[idy]

                    if(x["value"]<y["value"]):
                        continue
                    delta_value += x["value"]-y["value"]
                    delta_timestamp_seconds += (datetime.strptime(y["timestamp"], self.TIME_FORMAT)-datetime.strptime(x["timestamp"], self.TIME_FORMAT)).total_seconds()
                # 转换成小时
                delta_timestamp_hours=delta_timestamp_seconds/3600
                # 计算小时平均消耗
                avg_usage_hour = delta_value / delta_timestamp_hours
                # 计算24h内的平均电费使用量
                avg_usage=delta_value/(delta_timestamp_hours/24)
                # 计算从上一次数据开始，剩余电费还能用多少天
                # 特判：几乎无开销
                if avg_usage==0.0:
                    if delta_timestamp_seconds==0:
                        return {
                            "code": 103,
                            "info": f"最近 {time_span} 小时内，你都在充电费，让我算个🥚啊！过几个小时再来问我！笨蛋！"
                        }
                    else:
                        return {
                            "code": 104,
                            "info": f"最近 {time_span} 小时内，好像基本没用电呢，欸!(＃°Д°)不会似了吧！"
                        }
                remaining_day_from_lastest_requirement=vaild_data[-1]["value"]/avg_usage # 从上次查询开始计算，预计还能用多少天
                outage_time=datetime.strptime(vaild_data[-1]["timestamp"], self.TIME_FORMAT)+timedelta(days=remaining_day_from_lastest_requirement)
                now_time=datetime.now()
                remaining_day=outage_time-now_time
                # 转str/double
                outage_time_str=outage_time.strftime(self.TIME_FORMAT)
                remaining_day_double=remaining_day.total_seconds()/(24*3600)
                return {
                    "code": 100,
                    "info": f"⏱️近 {time_span} 小时\n🏠房间 {room_name}：\n⚡电费使用平均速率 {avg_usage_hour:.2f} 元/小时\n💤预计一天消耗{avg_usage:.2f} 元\n✨预计还能使用 {remaining_day_double:.2f} 天，将在 {outage_time_str} 停电。\n🧐{time_span}小时内有效数据 {len(vaild_data)} 条，有效时间跨度 {delta_timestamp_hours:.2f} 小时\n呜呜呜::>_<::我最讨厌数学啦！😭😭😭",
                    "avg_usage": avg_usage,
                    "remaining_day": remaining_day_double,
                    "outage_time": outage_time_str,
                    "vaild_data_size": len(vaild_data),
                    "delta_timestamp": delta_timestamp_hours
                }



        return {"code": "101", "info": f"嘿嘿嘿~❤️杂鱼~杂鱼~💞\n订阅历史中不存在房间「{room_name}」的历史数据哦！"}
