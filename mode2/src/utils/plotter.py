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
from typing import List, Dict, Any, Tuple

import matplotlib
matplotlib.use('Agg') # 使用非交互式后端，适用于服务器环境
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import numpy as np
from scipy.interpolate import make_interp_spline, Akima1DInterpolator, PchipInterpolator
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
        
    
    # 画历史曲线
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

        # 【新增】异常值过滤
        original_count = len(room_data)
        room_data = self._filter_outliers_with_MAD(room_data, threshold=3.0, window_size=10)
        filtered_count = len(room_data)
        
        if len(room_data) < 2:
            return {"code": 102, "info": f"过滤异常值后数据点不足 (仅 {len(room_data)} 个)，无法绘制曲线"}

        # 准备绘图：原始时间与数值
        timestamps = [datetime.strptime(d["timestamp"], self.TIME_FORMAT) for d in room_data]
        values = [d["value"] for d in room_data]

        # 曲线1：通过所有点的平滑曲线（PCHIP + raw）
        x_smooth_raw, y_smooth_raw = self._generate_smooth_curve(
            room_data,
            method="pchip",
            points_count=300,
            trend_mode="raw",
        )

        # 曲线2：趋势线（PCHIP + MA，窗口=3）
        x_smooth_ma, y_smooth_ma = self._generate_smooth_curve(
            room_data,
            method="pchip",
            points_count=300,
            trend_mode="ma",
            ma_window=3,
        )

        # 4. 绘图
        font_path = os.path.join("assets", "fonts", "YaHei Ubuntu Mono.ttf")
        if not os.path.exists(font_path):
            pylog.error(f"字体文件 '{font_path}' 在项目目录中未找到！请确保已复制。")
            return {"code": 122, "info": f"字体文件 '{font_path}' 未找到"}
        my_font = FontProperties(fname=font_path)

        sns.set_theme(style="darkgrid")
        fig, ax = plt.subplots(figsize=(12, 7))

        # 0. 绘制原始数据点
        if len(timestamps) >=150:
            # 时间跨度较长，不画数据点
            pass
        else:
            # 动态计算点的大小：基础大小 40，随着点数增加而减小，最少不小于 10
            point_size = max(10, 40 - 0.1 * len(timestamps)) 
            ax.scatter(timestamps, values, label="实际数据点", color='red', s=point_size, zorder=5)
        # 曲线1：穿点平滑曲线（PCHIP + raw）
        ax.plot(
            x_smooth_raw,
            y_smooth_raw,
            label="电费变化曲线",
            color='royalblue',
            linewidth=2,
        )
        # 曲线2：趋势线（PCHIP + MA，细虚线）
        ax.plot(
            x_smooth_ma,
            y_smooth_ma,
            label="趋势线",
            color='royalblue',
            linewidth=1.2,
            linestyle="--",
            alpha=0.9,
        )
        
        # 格式化图表
        ax.set_title(f'房间「{room_name}」近 {time_span} 小时电费历史', fontproperties=my_font, fontsize=16, pad=20)
        ax.set_xlabel("时间", fontproperties=my_font, fontsize=12)
        ax.set_ylabel("剩余电费 (元)", fontproperties=my_font, fontsize=12)
        ax.legend(prop=my_font)
        removed_points = original_count - filtered_count
        if removed_points > 0:
            ax.text(
                0.99,
                0.02,
                f"有效数据点 {filtered_count}, 过滤 {removed_points} 个异常数据",
                transform=ax.transAxes,
                ha="right",
                va="bottom",
                fontsize=9,
                color="#888888",
                style="italic",
                fontdict={"fontproperties": my_font}
            )
        else:
            ax.text(
                0.99,
                0.02,
                f"有效数据点 {filtered_count}, 无异常数据",
                transform=ax.transAxes,
                ha="right",
                va="bottom",
                fontsize=9,
                color="#888888",
                style="italic",
                fontdict={"fontproperties": my_font}
            )
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
    
    # 异常值过滤 滑动窗口MAD+充值豁免
    def _filter_outliers_with_MAD(
        self,
        data: List[Dict],
        threshold: float = 3.0,
        window_size: int = 10,
        recharge_buffer: float = 500.0,
        recharge_points: int = 5
    ) -> List[Dict]:
        """
        使用滑动窗口MAD (Median Absolute Deviation) 算法过滤异常值。
        
        算法特点：
        1. 对每个数据点使用其周围窗口内的数据计算MAD
        2. 对突然上升的数据点给予豁免（更大的容忍度），并在随后若干点继续缓冲
        3. 过滤掉异常的低值或高值波动
        
        Args:
            data (List[Dict]): 原始历史数据，格式为 [{"timestamp": str, "value": float}, ...]
            threshold (float): MAD倍数阈值，默认3.0。越大越宽松
            window_size (int): 滑动窗口大小，默认10。必须>=3
            recharge_buffer (float): 允许突增点超出上界的缓冲值
            recharge_points (int): 突增后额外豁免的连续数据点数量
            
        Returns:
            List[Dict]: 过滤后的数据列表
        """
        if len(data) < 3:
            pylog.warning(f"数据点不足3个（当前{len(data)}个），跳过异常值过滤")
            return data
        
        values = [d["value"] for d in data]
        filtered_indices: List[int] = []
        
        half_window = max(1, window_size // 2)
        recharge_countdown = 0
        
        for i in range(len(values)):
            # 定义窗口范围
            start_idx = max(0, i - half_window)
            end_idx = min(len(values), i + half_window + 1)
            window_data = values[start_idx:end_idx]
            
            median_val = np.median(window_data)
            mad = np.median([abs(v - median_val) for v in window_data])
            if mad == 0:
                mad = 1e-6
            
            # 计算上下界
            upper_bound = median_val + threshold * mad
            lower_bound = median_val - threshold * mad
            
            # 判断是否为异常值
            current_value = values[i]
            prev_value = values[i - 1] if i > 0 else None
            
            # 低值直接视为异常
            if current_value < lower_bound:
                pylog.info(
                    f"过滤异常值: 时间={data[i]['timestamp']}, 值={current_value:.2f}, "
                    f"界限=[{lower_bound:.2f}, {upper_bound:.2f}]"
                )
                continue
            
            # 高值异常，判断是否属于充值突增
            if current_value > upper_bound:
                is_recharge = (
                    prev_value is not None
                    and current_value > prev_value
                    and (current_value - upper_bound) <= recharge_buffer
                )
                if is_recharge or recharge_countdown > 0:
                    recharge_countdown = recharge_points
                    filtered_indices.append(i)
                    continue
                
                pylog.info(
                    f"过滤异常值: 时间={data[i]['timestamp']}, 值={current_value:.2f}, "
                    f"界限=[{lower_bound:.2f}, {upper_bound:.2f}]"
                )
                continue
            
            # 正常判断：在界限内则保留
            if lower_bound <= current_value <= upper_bound:
                filtered_indices.append(i)
            else:
                pylog.info(f"过滤异常值: 时间={data[i]['timestamp']}, 值={current_value:.2f}, "
                           f"界限=[{lower_bound:.2f}, {upper_bound:.2f}]")
                continue
            
            if recharge_countdown > 0:
                recharge_countdown -= 1
        
        # 根据保留的索引构建过滤后的数据
        filtered_data = [data[i] for i in filtered_indices]
        
        if len(filtered_data) < len(data):
            pylog.info(f"异常值过滤完成: {len(data)} -> {len(filtered_data)} (过滤了 {len(data)-len(filtered_data)} 个异常点)")
        
        return filtered_data

    # 生成多种平滑曲线数据
    def _generate_smooth_curve(
        self,
        filtered_data: List[Dict],
        method: str = "pchip",
        points_count: int = 300,
        trend_mode: str = "raw",
        ma_window: int = 3,
        ema_alpha: float = 0.3,
    ) -> Tuple[List[datetime], np.ndarray]:
        """
        基于过滤后的数据生成平滑曲线坐标。
        
        Args:
            filtered_data: 已经过滤异常值后的数据
            method: 'akima' 或 'pchip'，用于插值
            points_count: 插值后的点数，越多越平滑
            trend_mode: 'raw' 原始值；'ma' 滑动平均；'ema' 指数平滑
            ma_window: 'ma' 模式下的窗口大小（以点为单位）
            ema_alpha: 'ema' 模式下的平滑系数 (0,1]
        
        Returns:
            (x_smooth_dates, y_smooth_values)
        """
        if not filtered_data or len(filtered_data) < 2:
            return [], np.array([])

        # 1. 提取时间与数值
        try:
            timestamps = [datetime.strptime(d["timestamp"], self.TIME_FORMAT) for d in filtered_data]
        except (TypeError, ValueError):
            timestamps = [d["timestamp"] for d in filtered_data]
        values = [float(d["value"]) for d in filtered_data]

        # 2. 根据 trend_mode 生成趋势点
        y_trend = np.array(values, dtype=float)

        if trend_mode == "ma":
            # 简单滑动平均（点窗口），两端用可用范围内的平均
            window = max(1, int(ma_window))
            half_w = window // 2
            smoothed = []
            for i in range(len(y_trend)):
                start = max(0, i - half_w)
                end = min(len(y_trend), i + half_w + 1)
                smoothed.append(float(np.mean(y_trend[start:end])))
            y_trend = np.array(smoothed, dtype=float)
        elif trend_mode == "ema":
            alpha = float(ema_alpha)
            alpha = min(max(alpha, 0.0), 1.0)
            if alpha <= 0.0:
                alpha = 0.3
            ema_vals = []
            prev = y_trend[0]
            ema_vals.append(prev)
            for v in y_trend[1:]:
                prev = alpha * v + (1.0 - alpha) * prev
                ema_vals.append(prev)
            y_trend = np.array(ema_vals, dtype=float)
        else:
            # raw: 不做额外平滑
            pass

        # 3. 对趋势点做插值
        x_numeric = mdates.date2num(timestamps)
        x_smooth_numeric = np.linspace(x_numeric.min(), x_numeric.max(), points_count)

        if method == "akima":
            interpolator = Akima1DInterpolator(x_numeric, y_trend)
        elif method == "pchip":
            interpolator = PchipInterpolator(x_numeric, y_trend)
        else:
            raise ValueError("method must be 'akima' or 'pchip'")

        y_smooth = interpolator(x_smooth_numeric)
        x_smooth_dates = mdates.num2date(x_smooth_numeric)
        return x_smooth_dates, y_smooth
    
    # 画消耗曲线
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
        from matplotlib.font_manager import FontProperties

        # --- 0. 基本的数据寻找、过滤和初步验证 ---
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

        # 余额级别的异常值过滤
        room_data = self._filter_outliers_with_MAD(room_data, threshold=3.0, window_size=10)
        if len(room_data) < 2:
            return {"code": 102, "info": f"过滤异常值后数据点不足 (少于2个)，无法计算消耗"}

        # --- 1. 计算每个有效时间段的消耗率和时间中点 ---
        segments = []
        for i in range(len(room_data) - 1):
            start_point = room_data[i]
            end_point = room_data[i + 1]

            # 过滤掉 value 上升的时间段 (充电)
            if start_point["value"] < end_point["value"]:
                continue

            # 计算消耗量
            consumption = start_point["value"] - end_point["value"]

            # 计算时间差 (小时)
            t_start = datetime.strptime(start_point["timestamp"], self.TIME_FORMAT)
            t_end = datetime.strptime(end_point["timestamp"], self.TIME_FORMAT)
            duration_hours = (t_end - t_start).total_seconds() / 3600

            if duration_hours <= 0:
                continue

            # 平均每小时消耗率
            rate = consumption / duration_hours

            # 时间段中点
            midpoint = t_start + (t_end - t_start) / 2

            segments.append(
                {
                    "timestamp": midpoint,
                    "rate": rate,
                    "duration_hours": duration_hours,
                }
            )

        if not segments:
            return {"code": 103, "info": f"房间「{room_name}」在近 {time_span} 小时内未找到有效的电费消耗记录 (可能充值)"
                    }

        original_count = len(segments)

        # --- 2. 对消耗率段做二次过滤（时长 & rate 异常） ---
        segments = self._filter_consumption_segments(segments)
        filtered_count = len(segments)

        if not segments:
            return {"code": 103, "info": f"过滤异常段后未找到有效的电费消耗记录"}

        # 把过滤后的段拆成绘图所需的几个数组
        consumption_rates = [seg["rate"] for seg in segments]
        midpoint_timestamps = [seg["timestamp"] for seg in segments]
        time_period_durations_day = [seg["duration_hours"] / 24.0 for seg in segments]

        # --- 3. 生成趋势线（与 plot_history 风格一致） ---
        # 构造兼容 _generate_smooth_curve 的数据结构
        trend_data = [
            {"timestamp": ts, "value": rate}
            for ts, rate in zip(midpoint_timestamps, consumption_rates)
        ]

        # 曲线1：穿点（PCHIP + raw）
        x_smooth_raw, y_smooth_raw = self._generate_smooth_curve(
            trend_data,
            method="pchip",
            points_count=300,
            trend_mode="raw",
        )

        # 曲线2：趋势线（PCHIP + MA）
        x_smooth_ma, y_smooth_ma = self._generate_smooth_curve(
            trend_data,
            method="pchip",
            points_count=300,
            trend_mode="ma",
            ma_window=max(3, moving_avg_window)+3, # 这里将ma_window调大，让趋势线更平滑
        )

        # --- 4. 绘图 ---
        font_path = os.path.join("assets", "fonts", "YaHei Ubuntu Mono.ttf")
        if not os.path.exists(font_path):
            pylog.error(f"字体文件 '{font_path}' 在项目目录中未找到！")
            return {"code": 122, "info": f"字体文件 '{font_path}' 未找到"}
        my_font = FontProperties(fname=font_path)

        sns.set_theme(style="whitegrid")
        fig, ax = plt.subplots(figsize=(12, 7))

        # 柱状图：每小时平均消耗率
        bars = ax.bar(
            midpoint_timestamps,
            consumption_rates,
            width=[w * 0.8 for w in time_period_durations_day],
            label="每小时平均消耗率",
            color="skyblue",
            edgecolor="none",
            zorder=1,
        )

        # 曲线1：穿点平滑曲线（PCHIP + raw）
        line_raw, = ax.plot(
            x_smooth_raw,
            y_smooth_raw,
            label="消耗变化曲线",
            color="royalblue",
            linewidth=2,
            zorder=3,
        )

        # 曲线2：趋势线（PCHIP + MA，细虚线）
        line_ma, = ax.plot(
            x_smooth_ma,
            y_smooth_ma,
            label="消耗趋势",
            color="lightcoral",
            linewidth=1.8,
            linestyle="--",
            alpha=0.9,
            zorder=2,
        )

        # 格式化图表
        ax.set_title(
            f'房间「{room_name}」近 {time_span} 小时电费消耗率',
            fontproperties=my_font,
            fontsize=16,
            pad=20,
        )
        ax.set_xlabel("时间段中点", fontproperties=my_font, fontsize=12)
        ax.set_ylabel("每小时电费消耗 (元/小时)", fontproperties=my_font, fontsize=12)
        ax.legend(
            [bars, line_raw, line_ma],
            labels=["每小时平均消耗率", "消耗变化曲线", "消耗趋势"],
            prop=my_font)
        ax.grid(True, which="both", linestyle="--", linewidth=0.5, axis="y")

        # 右下角标注过滤信息
        removed_segments = original_count - filtered_count
        if removed_segments > 0:
            ax.text(
                0.99,
                0.02,
                f"过滤 {removed_segments} 段异常消耗",
                transform=ax.transAxes,
                ha="right",
                va="bottom",
                fontsize=9,
                color="#888888",
                style="italic",
                fontdict={"fontproperties": my_font}
            )
        else:
            ax.text(
                0.99,
                0.02,
                "无异常消耗段",
                transform=ax.transAxes,
                ha="right",
                va="bottom",
                fontsize=9,
                color="#888888",
                style="italic",
                fontdict={"fontproperties": my_font}
            )

        # 格式化 X 轴时间显示
        ax.xaxis.set_major_formatter(mdates.DateFormatter("%m-%d %H:%M"))
        fig.autofmt_xdate()

        # --- 5. 保存图片 ---
        try:
            os.makedirs(self.PLOT_DIR, exist_ok=True)
        except OSError as e:
            pylog.error(f"创建目录 '{self.PLOT_DIR}' 失败: {e}")
            return {"code": 120, "info": "创建图片目录失败"}

        safe_room_name = room_name.replace(" ", "_")
        timestamp_str = now_time.strftime("%Y%m%d_%H%M%S")
        filepath = os.path.join(
            self.PLOT_DIR, f"{safe_room_name}_consumption_{timestamp_str}.png"
        )

        try:
            plt.savefig(filepath, dpi=200, bbox_inches="tight")
            pylog.info(f"成功绘制并保存电费消耗柱状图: {filepath}")
        except Exception as e:
            pylog.error(f"保存图片 '{filepath}' 失败: {e}")
            return {"code": 121, "info": "保存图片失败"}
        finally:
            plt.close(fig)

        return {"code": 100, "info": "绘图成功", "path": filepath}

    def _filter_consumption_segments(
        self,
        segments: List[Dict],
        min_duration_hours: float = 0.25,
        mad_threshold: float = 3.0,
    ) -> List[Dict]:
        """
        对分段消耗率进行二次过滤：
        - 过滤掉时间过短的段 (duration < min_duration_hours)
        - 使用 MAD 在 rate 空间过滤异常高/低的段
        """
        if not segments:
            return []

        # 先按时长过滤
        duration_filtered = [
            seg for seg in segments if seg["duration_hours"] >= min_duration_hours
        ]
        if len(duration_filtered) < 3:
            # 如果过滤后太少，就直接返回按时长过滤的结果（不做 MAD）
            return duration_filtered

        # 对 rate 使用 MAD 过滤
        rates = np.array([seg["rate"] for seg in duration_filtered], dtype=float)
        median_val = np.median(rates)
        mad = np.median(np.abs(rates - median_val))

        if mad == 0:
            # 所有段都几乎一样，直接返回
            return duration_filtered

        lower_bound = median_val - mad_threshold * mad
        upper_bound = median_val + mad_threshold * mad

        filtered = []
        for seg, rate in zip(duration_filtered, rates):
            if lower_bound <= rate <= upper_bound:
                filtered.append(seg)
            else:
                pylog.info(
                    f"过滤消耗异常段: 时间中心={seg['timestamp']}, rate={rate:.2f}, "
                    f"区间=[{lower_bound:.2f}, {upper_bound:.2f}]"
                )

        return filtered
    
