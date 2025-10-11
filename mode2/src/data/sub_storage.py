'''
负责qq机器人的有关订阅/data存储读取的功能
- 用户添加订阅房间add_subscription
- 用户取消订阅房间remove_subscription
- 查询最近一次历史数据require_lastest_history
- 检查是否订阅is_sub
- 手动添加一条数据add_record（可以用于用户查询数据时发现数据存在更新时手动添加，这样就比tracker早一步了）

Build by Vanilla-chan (2025.7.18)

Refactor by ArisuMika (2025.7.25)
'''
import asyncio
import json
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
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
from core import Buildings
import asyncio
from botpy.ext.cog_yaml import read
from typing import List, Dict, Any

config = read(os.path.join(os.path.dirname(__file__), '..', '..', 'config.yaml'))

class Subscription:
    # 订阅列表文件路径
    SUBSCRIPTION_LIST_FILE = config['path']['SUBSCRIPTION_LIST_FILE'] # sub
    # 订阅历史文件路径
    SUBSCRIPTION_HISTORY_FILE = config['path']['SUBSCRIPTION_HISTORY_FILE'] # his
    # 时间字符串格式
    TIME_FORMAT = "%Y-%m-%d %H:%M:%S"
    # 绘图输出目录
    PLOT_DIR = config["path"]['PLOT_DIR'] # plot

    def __init__(self):
        pass
    
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
        
    # 订阅
    def add_subscription(self, room_name: str) -> Dict:
        '''
        用户添加订阅房间
        
        Args:
            room_name (str): 新订阅房间号

        Returns:
            dict: 
                返回一个包含状态信息的字典，结构如下：
                
                {
                    "code": str,       # 状态码
                    "codeinfo": str,   # 状态码含义
                    "info": str        # 订阅成功或订阅失败
                }

                状态码：
                100 成功
                101 重复订阅
                111 房间参数数量错误
                112 楼栋号错误
                113 房间号错误
                131 订阅文件保存失败
        '''

        # 检测是否存在该房间
        # 这里只能借助 buildingData 检测 东/西区 楼栋号 是否正确
        # 不能检测 楼层号 房间号 是否正确
        parts = room_name.strip().split(' ')
        if len(parts) != 2:
            return {
                "code":"111",
                "info":f"'{room_name}' 参数数量不正确，应为2个（楼栋 房间号）"
            }
        if len(parts[1]) != 3:
            return {
                "code":"112",
                "info":f"'{room_name}' 房间号（长度）不正确"
            }

        try:
            # build_part = parts[0]
            # area = 1 if build_part.startswith('D') else 0
            buildIndex = Buildings.get_buildingIndex(1 if parts[0].startswith('D') else 0, parts[0])
        except KeyError:
            return {
                "code":"113",
                "info":f"楼栋号 '{parts[0]}' 不存在或不正确，应为 'D9东'（东区） 或 '10南'（西区）"
            }

        # 读取订阅列表
        sub_list = self._load_json_file(self.SUBSCRIPTION_LIST_FILE)
        
        # 解析
        if room_name in sub_list:
            return {
                "code":"101",
                "info":f"你！已经订阅过房间 {room_name}了！baka！(╬▔皿▔)╯"
            }
        
        sub_list.append(room_name)

        # 写入
        if self._save_json_file(self.SUBSCRIPTION_LIST_FILE, sub_list):
            return {"code": "100", "info": f"成功订阅房间「{room_name}」┑(￣Д ￣)┍真麻烦呐~"}
        else:
            return {"code": "131", "info": "保存订阅文件失败，请检查日志！出错啦！笨蛋快来修bug！"}
        
    # 取消订阅
    def remove_subscription(self, room_name: str) -> Dict:
        """
            用户取消订阅房间。

            状态码：
                100 成功
                102 未订阅
                131 订阅文件保存失败
        """
        sub_list = self._load_json_file(self.SUBSCRIPTION_LIST_FILE)
        if room_name not in sub_list:
            return {"code": "102", "info": f"订阅列表中不存在房间「{room_name}」"}
            
        sub_list.remove(room_name)
        if self._save_json_file(self.SUBSCRIPTION_LIST_FILE, sub_list):
            return {"code": "100", "info": f"成功取消订阅房间「{room_name}」"}
        else:
            return {"code": "131", "info": "保存订阅文件失败，请检查日志！出错啦！笨蛋快来修bug！"}
        
    # check_sub 检查
    def is_sub(self, room_name: str) -> Dict:
        """
            查询某房间是否正在订阅
                
            状态码：
                100 订阅中
                101 未订阅
        """
        sub_list = self._load_json_file(self.SUBSCRIPTION_LIST_FILE)
        if room_name not in sub_list:
            return {"code": "101", "info": f"订阅列表中不存在房间「{room_name}」"}
        return {"code": "100", "info": f"正在订阅房间「{room_name}」"}

    def require_lastest_history(self, room_name: str) -> Dict:
        """
            查询某房间上一次的历史数据
            
            如果存在：
                code: 100
                timestamp: str, 上一次查询的时间戳
                value: double, 上次查询的剩余电费
            
            如果不存在：
                code: 101
        """
        sub_his = self._load_json_file(self.SUBSCRIPTION_HISTORY_FILE)
        
        for item in sub_his:
            if item["name"]==room_name and len(item["his"])!=0:
                return {
                    "code": "100",
                    "info": f"订阅列表中存在房间 {room_name}",
                    "timestamp": item["his"][-1]["timestamp"],
                    "value": item["his"][-1]["value"]
                }
        return {"code": "101", "info": f"订阅列表中不存在房间「{room_name}」"}
    
    # 手动add
    def add_record(self, room_name: str, value: float, force=False):
        """
        手动添加一条数据，时间戳自动采用当前的时间
        force: True or False, 是否强制添加（是否在未订阅该房间的情况下依然添加

        状态码：

        成功添加：
        100

        由于未订阅该房间，且force=Flase，故不添加：
        101

        由于与上一条记录的value相同且时间差小于2h，故不添加
        102

        添加失败（文件保存失败）
        110
        
        """
        sub_list=self._load_json_file(self.SUBSCRIPTION_LIST_FILE)
        if room_name not in sub_list and force == False:
            return {
                "code": 101,
                "info": "未订阅该房间，不进行添加"
            }
        sub_his=self._load_json_file(self.SUBSCRIPTION_HISTORY_FILE)
        for item in sub_his:
            if item["name"]==room_name:
                now_time=datetime.now()
                now_time_str=now_time.strftime(self.TIME_FORMAT)
                # 如果his是空的则直接加
                if len(item["his"])==0:
                    item["his"].append({
                        "timestamp": now_time_str,
                        "value": value
                    })
                    if self._save_json_file(self.SUBSCRIPTION_HISTORY_FILE, sub_his):
                        return {
                            "code": 100,
                            "info": "添加成功"
                        }
                    else:
                        return {
                            "code": 110,
                            "info": "添加失败，文件保存失败"
                        }
                # 相邻检测
                last_data=item["his"][-1]
                if last_data["value"]==value and now_time - datetime.strptime(last_data["timestamp"],self.TIME_FORMAT) <= timedelta(hours=2):
                    return {
                        "code": 102,
                        "info": "不添加，与上一条记录的剩余电费相同，且时间差不超过2h"
                    }
                item["his"].append({
                    "timestamp": now_time_str,
                    "value": value
                })
                if self._save_json_file(self.SUBSCRIPTION_HISTORY_FILE, sub_his):
                    return {
                        "code": 100,
                        "info": "添加成功"
                    }
                else:
                    return {
                        "code": 110,
                        "info": "添加失败，文件保存失败"
                    }
        # 添加新数据
        sub_his.append({
            "name": room_name,
            "his": [{
                    "timestamp": datetime.now().strftime(self.TIME_FORMAT),
                    "value": value
            }]
        })
        if self._save_json_file(self.SUBSCRIPTION_HISTORY_FILE, sub_his):
            return {
                "code": 100,
                "info": "添加成功"
            }
        else:
            return {
                "code": 110,
                "info": "添加失败，文件保存失败"
            }