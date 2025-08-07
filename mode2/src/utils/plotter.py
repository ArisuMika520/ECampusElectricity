'''
负责qq机器人的有关图形化的功能
- 绘制房间最近电费历史折线图

Build by Vanilla-chan (2025.7.18)

Refactor by ArisuMika (2025.8.7)

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

import matplotlib
matplotlib.use('Agg') # 使用非交互式后端，适用于服务器环境
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import numpy as np
from scipy.interpolate import make_interp_spline
import seaborn as sns
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
config = read(os.path.join(os.path.dirname(__file__), '..', '..', 'config.yaml'))

class Elect_plot:
    # 订阅列表文件路径
    SUBSCRIPTION_LIST_FILE = config['path']['SUBSCRIPTION_LIST_FILE'] # sub
    # 订阅历史文件路径
    SUBSCRIPTION_HISTORY_FILE = config['path']['SUBSCRIPTION_HISTORY_FILE'] # his
    # 时间字符串格式
    TIME_FORMAT = "%Y-%m-%d %H:%M:%S"
    # 绘图输出目录
    PLOT_DIR = config["path"]['PLOT_DIR'] # plot
    
    def __init__(self, monitor):
        self.monitor = monitor
        self._setup_matplotlib_font()
    # setupfont
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
        
    
    # plot
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
        font_path = os.path.join("assets", "fonts", "YaHei Ubuntu Mono.ttf")
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
    # 柱状
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
        font_path = os.path.join("assets", "fonts", "YaHei Ubuntu Mono.ttf")
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
