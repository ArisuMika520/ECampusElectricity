'''
存放Bot具体的命令方法

Build by ArisuMika
'''
import asyncio
import sys
import os
import re
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from typing import Dict
from botpy import logging
from core import Electricity
from core import Buildings
from utils import plotter
from utils import predictor
from utils import image_uploader
from data import sub_storage
from botpy.ext.cog_yaml import read

_log = logging.get_logger()
config = read(os.path.join(os.path.dirname(__file__), '..', '..', 'config.yaml'))

Electricity.configure_offset_file(
    config.get('path', {}).get('FLOOR_OFFSET_FILE', 'data_files/floor_offset.json')
)

# 指令切分
class Content_split:
    """
    负责解析用户发送的原始消息字符串。
    """
    def query_electricity(content):
        """
        查询指定电费指令
        格式: /查询指定电费 <楼栋> <房间号>
        """
        parts = content.strip().split(' ')
        # 参数检查
        if len(parts) < 3:
            return 0
        # 东校区
        if parts[1][0] == 'D':
            area = 1
            buildNum = parts[1]
            buildIndex = Buildings.get_buildingIndex(area,buildNum)
            floor = int(parts[2][0])-1
            roomNum = int(parts[2][1:])-1
            return (area,buildIndex,floor,roomNum)
        # 西校区
        else:
            area = 0
            buildNum = parts[1]
            buildIndex = Buildings.get_buildingIndex(area,buildNum)
            floor = int(parts[2][0])-1
            roomNum = int(parts[2][1:])-1
            return (area,buildIndex,floor,roomNum)
        
    def subscrip(content):
        """
        添加订阅处理指令
        格式: /订阅 <楼栋> <房间号>
        """
        parts = content.strip().split(' ')
        if len(parts) < 3:
            return 0
        return parts[1] + ' ' + parts[2]
    
    def plot_history(content):
        """
        解析历史图形指令
        支持格式:
            /图形化-历史 <楼栋> <房间号> [小时数]
            /图形化历史 <楼栋> <房间号> [小时数]
        """
        parts = content.strip().split()
        args = parts[1:]

        if len(args) >= 3 and args[2].isdigit():
            building, room_token = args[0], args[1]
            time_span = int(args[2])
        elif len(args) >= 2:
            building, room_token = args[0], args[1]
            time_span = 48
        elif len(args) == 1:
            match = re.match(r"^(.+?)(\d{3,4})$", args[0])
            if not match:
                return None
            building, room_token = match.group(1), match.group(2)
            time_span = 48
        else:
            return None

        room_name = f"{building} {room_token}"
        return {"room_name": room_name, "time_span": time_span}

    def plot_consumption(content):
        """
        解析消耗图形指令
        支持格式:
            /图形化-消耗 <楼栋> <房间号> [小时数]
            /图形化消耗 <楼栋> <房间号> [小时数]
            /图形化-消耗 <楼栋房间号> [小时数]
        """
        parts = content.strip().split()
        args = parts[1:]
        if not args:
            return None

        time_span = 48
        if len(args) >= 3 and args[2].isdigit():
            building, room_token = args[0], args[1]
            time_span = int(args[2])
        elif len(args) >= 2:
            building, room_token = args[0], args[1]
            time_span = 48
        else:
            token = args[0]
            match = re.match(r"^(.+?)(\d{3,4})$", token)
            if not match:
                return None
            building, room_token = match.group(1), match.group(2)

        room_name = f"{building} {room_token}"
        return {"room_name": room_name, "time_span": time_span}
    def predict(content):
        """
        预测指令请求
        格式: /预测 <楼栋> <房间号> [小时数]
        """
        parts = content.strip().split(' ')
        if len(parts) < 3:
            return 0
        room_name = parts[1] + ' ' + parts[2]
        time_span = 48  # 默认48小时
        if len(parts) > 3 and parts[3].isdigit():
            time_span = int(parts[3])
        return (room_name,time_span)
        
# 调用电费查询
class ElectricityMonitor:
    """
    封装所有与直接查询电费相关的命令。
    """
    @staticmethod
    def query_electricity(area,buildIndex,floor,roomNum):
        """查询电费"""
        ece = Electricity.ECampusElectricity(config["electricity"])
        surplus, room_name = Electricity.ECampusElectricity.get_myRoom(area,buildIndex,floor,roomNum,ece)
        return (surplus,room_name)
    
# 订阅/data存储读取
class Subscrip:
    """
    封装所有与订阅和数据存储相关的命令。
    """
    def add(room_name):
        """添加订阅"""
        sub_manager = sub_storage.Subscription()
        
        result = sub_manager.add_subscription(room_name)
        return result["info"]
    
    def remove(room_name):
        """取消订阅"""
        sub_manager = sub_storage.Subscription()
        
        result = sub_manager.remove_subscription(room_name)
        return result["info"]
        
# 图形化
class plot:
    """
    封装绘图和上传功能的命令。
    """
    @staticmethod
    def process(plot_type: str, room_name: str, time_span: int) -> dict:
        plot_instance = plotter.Elect_plot(monitor=None)

        _log.info(f"开始为寝室「{room_name}」生成「{plot_type}」图...")
        if plot_type == "历史":
            plot_result = plot_instance.plot_history(room_name, time_span)
        elif plot_type == "消耗":
            plot_result = plot_instance.plot_consumption_histogram(room_name, time_span)
        else:
            return {"code": 500, "info": f"内部错误：未知的图形类型 '{plot_type}'"}

        if plot_result["code"] != 100:
            _log.warning(f"绘图失败: {plot_result['info']}")
            return {"code": plot_result["code"], "info": plot_result["info"]}

        image_path = plot_result["path"]
        _log.info(f"图片生成成功，路径: {image_path}")

        try:
            uploader_cfg = config["uploader"]
            record_file = config["path"]["UPLOAD_RECORD_FILE"]
            uploader = image_uploader.ImageUploader(
                token=uploader_cfg["token"], 
                album_id=uploader_cfg["album_id"],
                record_file_path=record_file
            )
        except (KeyError, ValueError) as e:
            _log.error(f"初始化图床上传器失败: {e}。请检查 config.yaml 配置。")
            return {"code": 500, "info": "机器人图床配置错误，请联系管理员。"}
            
        upload_result = uploader.manage_upload(room_name, image_path)
        return upload_result
# 预测
class predict:
    """
    封装所有与电费预测相关的命令。
    """
    def predict_day(room_name,time_span):
        pred_instance = predictor.predictor()
        
        result = pred_instance.predict_day(room_name,time_span)
        return result["info"]
        
    
    
