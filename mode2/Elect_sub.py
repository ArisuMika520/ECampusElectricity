'''
负责qq机器人的有关订阅的功能
- 用户添加订阅房间
- 用户取消订阅房间
- 用户查询电费使用情况、上次电费充值时间（区间）、预计剩余时间、预计停电时间
- 绘制房间最近电费历史折线图
同时支持与数据更新有关的功能
- 查询最近一次历史数据
- 手动添加一条数据（可以用于用户查询数据时发现数据存在更新时手动添加，这样就比tracker早一步了）
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
import buildingData
import asyncio
from Elect_bot import ElectricityMonitor
from botpy.ext.cog_yaml import read
from typing import List, Dict, Any

# 绘图库
import matplotlib
matplotlib.use('Agg') # 使用非交互式后端，适用于服务器环境
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import numpy as np
from scipy.interpolate import make_interp_spline
import seaborn as sns


class Subscription_model:
    # 订阅列表文件路径
    SUBSCRIPTION_LIST_FILE = "sub.json"
    # 订阅历史文件路径
    SUBSCRIPTION_HISTORY_FILE = "his.json"
    # 时间字符串格式
    TIME_FORMAT = "%Y-%m-%d %H:%M:%S"
    # 绘图输出目录
    PLOT_DIR = "plot"

    def __init__(self, monitor):
        self.monitor = monitor
        self._setup_matplotlib_font()

    def _setup_matplotlib_font(self):
        """配置Matplotlib以支持中文显示。"""
        try:
            # 优先使用黑体，如果找不到则尝试其他常见中文字体
            plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'WenQuanYi Micro Hei']
            plt.rcParams['axes.unicode_minus'] = False
            print("配置中文字体成功")
        except Exception as e:
            pylog.warning(f"配置中文字体失败，绘图中的中文可能显示为方块: {e}")
    
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
            buildIndex = buildingData.get_buildingIndex(1 if parts[0].startswith('D') else 0, parts[0])
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
                "info":f"已经订阅了房间 {room_name}"
            }
        
        sub_list.append(room_name)

        # 写入
        if self._save_json_file(self.SUBSCRIPTION_LIST_FILE, sub_list):
            return {"code": "100", "info": f"成功添加订阅房间「{room_name}」"}
        else:
            return {"code": "131", "info": "保存订阅文件失败，请检查日志"}
    
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
            return {"code": "131", "info": "保存订阅文件失败，请检查日志"}
        
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
        
    def day_status(self, room_name: str, time_span=24) -> Dict:
        """
        查询某房间近24h的使用情况，并做出初步的预测
        
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
                # 计算24h内的平均电费使用量
                avg_usage=delta_value/(delta_timestamp_hours/24)
                # 计算从上一次数据开始，剩余电费还能用多少天
                # 特判：几乎无开销
                if avg_usage==0.0:
                    if delta_timestamp_seconds==0:
                        return {
                            "code": 103,
                            "info": f"最近 {time_span} 小时内，都是你在充电费，让我预测不了啦！过几个小时再来问我吧！"
                        }
                    else:
                        return {
                            "code": 104,
                            "info": f"最近 {time_span} 小时内，好像基本没用电呢"
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
                    "info": f"近 {time_span} 小时，房间 {room_name} 平均使用电费 {avg_usage:.2f} 元，预计还能使用 {remaining_day_double:.2f} 天，将在 {outage_time_str} 停电。\n24小时内有效数据 {len(vaild_data)} 条，有效时间跨度 {delta_timestamp_hours:.2f} 小时",
                    "avg_usage": avg_usage,
                    "remaining_day": remaining_day_double,
                    "outage_time": outage_time_str,
                    "vaild_data_size": len(vaild_data),
                    "delta_timestamp": delta_timestamp_hours
                }


        return {"code": "101", "info": f"订阅列表中不存在房间「{room_name}」"}

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
    

    def plot_history(self, room_name: str, time_span: int = 48) -> Dict:
        """
        绘制近time_span小时内的数据点的曲线图

        Args:
            room_name (str): 要查询的房间名。
            time_span (int, optional): 查询的小时数范围，默认为 24 小时。

        Returns:
            Dict: 包含操作结果和图片路径
                - code: 100, info: "绘图成功", path: "图片路径.png"
                - code: 101, info: "未找到该房间的历史数据"
                - code: 102, info: "近期数据点不足 (少于2个)，无法绘图"
                - code: 120, info: "创建图片目录失败"
                - code: 121, info: "保存图片失败"
                - code: 122, info: "字体文件找不到"
        """
        # 导入 FontProperties 用于加载字体文件
        from matplotlib.font_manager import FontProperties

        sub_his = self._load_json_file(self.SUBSCRIPTION_HISTORY_FILE)
        now_time = datetime.now()
        room_data = None
        for item in sub_his:
            if item["name"] == room_name:
                room_data = [
                    d for d in item["his"] 
                    if now_time - datetime.strptime(d["timestamp"], self.TIME_FORMAT) <= timedelta(hours=time_span)
                ]
                break

        if not room_data:
            return {"code": 101, "info": f"未找到房间「{room_name}」在近 {time_span} 小时内的历史数据"}

        if len(room_data) < 2:
            return {"code": 102, "info": f"房间「{room_name}」在近 {time_span} 小时内数据点不足 (仅 {len(room_data)} 个)，无法绘制曲线"}

        # 准备绘图
        timestamps = [datetime.strptime(d["timestamp"], self.TIME_FORMAT) for d in room_data]
        values = [d["value"] for d in room_data]

        # 创建平滑曲线 (样条插值)
        # datetime转为matplotlib能理解的数值格式
        x_numeric = mdates.date2num(timestamps)
        
        # 让曲线更平滑
        x_smooth_numeric = np.linspace(x_numeric.min(), x_numeric.max(), 300)
        
        # 创建样条函数
        # k=min(3, len(x_numeric) - 1) 确保样条阶数不大于数据点数-1
        spl = make_interp_spline(x_numeric, values, k=min(3, len(x_numeric) - 1))
        y_smooth = spl(x_smooth_numeric)

        # 将平滑的x轴数值转回datetime对象用于绘图
        x_smooth = mdates.num2date(x_smooth_numeric)

        # 4. 绘图
        font_path = os.path.join("font","YaHei Ubuntu Mono.ttf")
        if not os.path.exists(font_path):
            pylog.error(f"字体文件 '{font_path}' 在项目目录中未找到！请确保已复制。")
            return {"code": 122, "info": f"字体文件 '{font_path}' 未找到"}
        my_font = FontProperties(fname=font_path)

        sns.set_theme(style="darkgrid")
        fig, ax = plt.subplots(figsize=(12, 7))

        # 绘制原始数据点
        ax.scatter(timestamps, values, label="实际数据点", color='red', zorder=5)
        # 绘制平滑曲线
        ax.plot(x_smooth, y_smooth, label="电费变化趋势", color='royalblue', linewidth=2)
        
        # 格式化图表
        ax.set_title(f'房间「{room_name}」近 {time_span} 小时电费历史', fontproperties=my_font, fontsize=16, pad=20)
        ax.set_xlabel("时间", fontproperties=my_font, fontsize=12)
        ax.set_ylabel("剩余电费 (元)", fontproperties=my_font, fontsize=12)
        ax.legend(prop=my_font)
        ax.grid(True, which='both', linestyle='--', linewidth=0.5)

        # 格式化X轴的时间显示
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%m-%d %H:%M'))
        fig.autofmt_xdate() # 自动旋转日期标签以防重叠

        # 5. 保存图片
        try:
            os.makedirs(self.PLOT_DIR, exist_ok=True)
        except OSError as e:
            pylog.error(f"创建目录 '{self.PLOT_DIR}' 失败: {e}")
            return {"code": 120, "info": f"创建图片目录失败"}
        
        safe_room_name = room_name.replace(" ", "_")
        timestamp_str = now_time.strftime('%Y%m%d_%H%M%S')
        filepath = os.path.join(self.PLOT_DIR, f"{safe_room_name}_{timestamp_str}.png")

        try:
            plt.savefig(filepath, dpi=200, bbox_inches='tight')
            pylog.info(f"成功绘制并保存电费历史图: {filepath}")
        except Exception as e:
            pylog.error(f"保存图片 '{filepath}' 失败: {e}")
            return {"code": 121, "info": "保存图片失败"}
        finally:
            plt.close(fig)

        return {"code": 100, "info": "绘图成功", "path": filepath}

    def plot_consumption_histogram(self, room_name: str, time_span: int = 48, moving_avg_window: int = 5) -> Dict:
        """
        绘制房间在近 time_span 小时内，每个有效时间段的平均电费消耗率柱状图。

        Args:
            room_name (str): 要查询的房间名。
            time_span (int, optional): 查询的小时数范围，默认为 48 小时。
            moving_avg_window (int, optional): 滑动平均的窗口大小，影响趋势线平滑度。必须为奇数。默认为 5。

        Returns:
            Dict: 包含操作结果和图片路径的字典。
                - code: 100, info: "绘图成功", path: "图片路径.png"
                - code: 101, info: "未找到该房间的历史数据"
                - code: 102, info: "近期数据点不足 (少于2个)，无法计算消耗"
                - code: 103, info: "在指定时间段内未找到有效的电费消耗记录 (可能都在充电)"
                - code: 120, info: "创建图片目录失败"
                - code: 121, info: "保存图片失败"
                - code: 122, info: "字体文件找不到"
        """
        # --- 0. 基本的数据寻找、过滤和初步验证 ---
        from matplotlib.font_manager import FontProperties
        import pandas as pd

        sub_his = self._load_json_file(self.SUBSCRIPTION_HISTORY_FILE)
        now_time = datetime.now()
        room_data = None
        for item in sub_his:
            if item["name"] == room_name:
                room_data = [
                    d for d in item["his"] 
                    if now_time - datetime.strptime(d["timestamp"], self.TIME_FORMAT) <= timedelta(hours=time_span)
                ]
                break

        if not room_data:
            return {"code": 101, "info": f"未找到房间「{room_name}」在近 {time_span} 小时内的历史数据"}

        if len(room_data) < 2:
            return {"code": 102, "info": f"房间「{room_name}」在近 {time_span} 小时内数据点不足 (少于2个)，无法计算消耗"}

        # --- 1. 计算每个有效时间段的消耗率和时间中点 ---
        consumption_rates = []
        midpoint_timestamps = []
        time_period_durations_day = [] # 用于设置柱状图宽度

        for i in range(len(room_data) - 1):
            start_point = room_data[i]
            end_point = room_data[i+1]

            # 过滤掉value上升的时间段 (充电)
            if start_point["value"] < end_point["value"]:
                continue

            # 计算消耗量
            consumption = start_point["value"] - end_point["value"]

            # 计算时间差 (小时)
            t_start = datetime.strptime(start_point["timestamp"], self.TIME_FORMAT)
            t_end = datetime.strptime(end_point["timestamp"], self.TIME_FORMAT)
            duration_hours = (t_end - t_start).total_seconds() / 3600
            
            # 避免除以零
            if duration_hours <= 0:
                continue

            # 计算平均每小时消耗率
            rate = consumption / duration_hours
            consumption_rates.append(rate)

            # 每个时间段，取中间的时间点作为该数据的时间点
            midpoint = t_start + (t_end - t_start) / 2
            midpoint_timestamps.append(midpoint)
            
            # 记录以“天”为单位的时间段长度，用于柱状图宽度
            time_period_durations_day.append(duration_hours / 24.0)

        if not consumption_rates:
            return {"code": 103, "info": f"房间「{room_name}」在近 {time_span} 小时内未找到有效的电费消耗记录 (可能充值)"}

        # 加一个滑动平均曲线
        consumption_series = pd.Series(consumption_rates, index=midpoint_timestamps).sort_index()
        # 确保窗口大小是奇数，并且不超过数据点总数
        if moving_avg_window % 2 == 0:
            moving_avg_window += 1 # 保证为奇数以使中心对齐
        window_size = min(moving_avg_window, len(consumption_series))
        if window_size < 3: window_size = 3 # 最小窗口为3
        # 计算滑动平均。center=True使窗口中心对齐当前点
        # min_periods=1允许在数据点不足窗口大小时也计算
        trend_series = consumption_series.rolling(window=window_size, center=True, min_periods=1).mean()
        

        # --- 3. 绘图 ---
        font_path = os.path.join("font", "YaHei Ubuntu Mono.ttf")
        if not os.path.exists(font_path):
            pylog.error(f"字体文件 '{font_path}' 在项目目录中未找到！")
            return {"code": 122, "info": f"字体文件 '{font_path}' 未找到"}
        my_font = FontProperties(fname=font_path)

        sns.set_theme(style="whitegrid")
        fig, ax = plt.subplots(figsize=(12, 7))

        # 绘制柱状图
        # print(consumption_rates)
        # print(midpoint_timestamps)
        ax.bar(midpoint_timestamps, consumption_rates, width=[w * 0.8 for w in time_period_durations_day], 
               label="每小时平均消耗率", color='skyblue', edgecolor='none')
        # 绘制滑动平均趋势线
        ax.plot(trend_series.index, trend_series.values, color='lightcoral', linestyle='--', 
                linewidth=2.5, marker='o', markersize=4, label=f"消耗趋势")
        
        
        # 格式化图表
        ax.set_title(f'房间「{room_name}」近 {time_span} 小时电费消耗率', fontproperties=my_font, fontsize=16, pad=20)
        ax.set_xlabel("时间段中点", fontproperties=my_font, fontsize=12)
        ax.set_ylabel("每小时电费消耗 (元/小时)", fontproperties=my_font, fontsize=12)
        ax.legend(prop=my_font)
        ax.grid(True, which='both', linestyle='--', linewidth=0.5, axis='y') # 只在y轴显示网格

        # 格式化X轴的时间显示
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%m-%d %H:%M'))
        fig.autofmt_xdate()

        # --- 4. 保存图片 ---
        try:
            os.makedirs(self.PLOT_DIR, exist_ok=True)
        except OSError as e:
            pylog.error(f"创建目录 '{self.PLOT_DIR}' 失败: {e}")
            return {"code": 120, "info": f"创建图片目录失败"}
        
        safe_room_name = room_name.replace(" ", "_")
        timestamp_str = now_time.strftime('%Y%m%d_%H%M%S')
        # 文件名添加 _consumption 后缀以作区分
        filepath = os.path.join(self.PLOT_DIR, f"{safe_room_name}_consumption_{timestamp_str}.png")

        try:
            plt.savefig(filepath, dpi=200, bbox_inches='tight')
            pylog.info(f"成功绘制并保存电费消耗柱状图: {filepath}")
        except Exception as e:
            pylog.error(f"保存图片 '{filepath}' 失败: {e}")
            return {"code": 121, "info": "保存图片失败"}
        finally:
            plt.close(fig)

        return {"code": 100, "info": "绘图成功", "path": filepath}


# --- 使用示例 ---
async def demo():
    """演示如何使用 Sub_model 类"""
    print("--- 演示开始 ---")
    print("实例化")
    config = read(os.path.join(os.path.dirname(__file__), "config.yaml"))
    monitor = ElectricityMonitor(config)
    sub_model=Subscription_model(monitor)
    print("添加订阅")
    print(sub_model.add_subscription("123"))
    print(sub_model.add_subscription("F10nan 123"))
    print(sub_model.add_subscription("10南 606"))
    print(sub_model.add_subscription("9南 505"))

    print("查询是否订阅")
    print(sub_model.is_sub("9南 505"))
    print(sub_model.is_sub("9北 505"))

    print("删除订阅")
    print(sub_model.remove_subscription("9南 505"))
    print(sub_model.remove_subscription("9南505"))
    print(sub_model.remove_subscription("9南 505"))

    print("查询最近一次历史数据")
    print(sub_model.require_lastest_history("10南 606"))
    print(sub_model.require_lastest_history("9南 505"))
    print(sub_model.require_lastest_history("9南 504"))

    print("查询电费使用情况")
    print(sub_model.day_status("10南 606",time_span=48))
    print(sub_model.day_status("D9东 425"))
    print(sub_model.day_status("10南 604"))
    print(sub_model.day_status("10南 602"))
    print(sub_model.day_status("10南 601"))

    print("手动添加一条电费数据")
    print(sub_model.add_record("10南 101",43)) # 添加未订阅的房间数据
    print(sub_model.add_subscription("10南 102"))
    print(sub_model.add_record("10南 102",43)) # 添加已订阅的房间数据
    print(sub_model.add_record("10南 102",43)) # 测试重复添加
    print(sub_model.add_record("10南 103",43,force=True)) # 强制添加未订阅的房间数据

    print("查询电费使用情况、预计剩余")
    # print(sub_model.query_status("10南 606"))
    print("已弃用，请使用day_status(房间名称,time_span=24)")

    print("绘制房间近期电费历史折线图")
    print(sub_model.plot_history("10南 606"))
    print(sub_model.plot_history("D9东 425"))
    print(sub_model.plot_history("10南 605",time_span=36))

    print("绘制房间近期电费消耗折线图")
    print(sub_model.plot_consumption_histogram("10南 606",time_span=3600))
    print(sub_model.plot_consumption_histogram("D9东 425",time_span=48))
    print(sub_model.plot_consumption_histogram("10南 605"))
    print(sub_model.plot_consumption_histogram("10南 604"))
    print(sub_model.plot_consumption_histogram("10南 602"))

    

    
if __name__ == "__main__":
    asyncio.run(demo())
