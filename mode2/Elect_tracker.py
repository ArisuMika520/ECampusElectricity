import logging as pylog
# 配置日志记录器
pylog.basicConfig(
    level=pylog.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        pylog.FileHandler("tracker_log.log", encoding='utf-8'), # 输出到文件
        pylog.StreamHandler()                               # 同时输出到控制台
    ]
)
import datetime
import time
import json
import random
import os
import Electricity
import buildingData
import asyncio
from Elect_bot import ElectricityMonitor
from botpy.ext.cog_yaml import read

# --- 配置 ---

# 订阅文件路径
SUBSCRIPTION_FILE = "his.json"
# 读取和机器人相同的配置文件
config = read(os.path.join(os.path.dirname(__file__), "config.yaml"))
# 每次轮询之间的等待时间（秒）
WAIT_TIME = config["tracker"]["check_interval"]

# --- 查询函数 ---

async def elect_require(monitor: ElectricityMonitor, target_name: str) -> float:
    """
    执行实际的查询操作。

    Args:
        monitor (ElectricityMonitor): ElectricityMonitor 的实例。
        target_name (str): 需要查询的目标名称。

    Returns:
        float: 查询到的电费余额。
    """
    pylog.info(f"开始为 '{target_name}' 执行查询...")
    
    parts = target_name.strip().split(' ')
    if len(parts) != 2:
        raise ValueError(f"查询 '{target_name}' 时参数数量不正确，应为2个（楼栋 房间号）")

    build_part = parts[0]
    room_part = parts[1]
    area = 1 if build_part.startswith('D') else 0

    buildIndex = buildingData.get_buildingIndex(area, build_part)
    floor = int(room_part[0]) - 1
    roomNum = int(room_part[1:]) -1

    surplus, room_name = await monitor.query_electricity(area, buildIndex, floor, roomNum)

    return surplus

    # now = datetime.datetime.now()
    # formatted_time = now.strftime("%Y-%m-%d %H:%M:%S")

    # return (surplus,formatted_time)



async def main():
    """
    主函数，运行无限循环的定时查询任务。
    """

    # 创建 ElectricityMonitor 实例
    pylog.info("正在初始化电费查询模块...")
    monitor = ElectricityMonitor(config)
    pylog.info("模块初始化成功。")

    while True:
        # 输出信息
        current_time_str = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        pylog.info(f"现在时间是 {current_time_str}，准备开始新一轮查询。")

        # 读取订阅列表
        try:
            with open(SUBSCRIPTION_FILE, 'r', encoding='utf-8') as f:
                subscriptions = json.load(f)
            pylog.info(f"成功读取订阅文件，共找到 {len(subscriptions)} 条订阅。")
        except FileNotFoundError:
            pylog.error(f"错误：订阅文件 '{SUBSCRIPTION_FILE}' 不存在。请先创建该文件。")
            pylog.info(f"将在 {WAIT_TIME} 秒后重试...")
            time.sleep(WAIT_TIME)
            continue  # 跳过本轮循环的剩余部分
        except json.JSONDecodeError:
            pylog.error(f"错误：订阅文件 '{SUBSCRIPTION_FILE}' 格式无效，无法解析。请手动调整his.json格式。")
            pylog.info(f"将在 {WAIT_TIME} 秒后重试...")
            time.sleep(WAIT_TIME)
            continue  # 跳过本轮循环的剩余部分

        # 对每个订阅的name进行查询并更新数据
        for sub in subscriptions:
            name = sub.get("name")
            if not name:
                pylog.warning("发现一条没有 'name' 字段的订阅，已跳过。")
                continue

            # 执行查询
            new_value = await elect_require(monitor, name)
            
            # 获取当前时间作为记录时间
            record_time = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            
            # 确保 'his' 字段是列表
            if 'his' not in sub or not isinstance(sub['his'], list):
                sub['his'] = []
            
            # 将新数据 [时间, 数值] 追加到历史记录中
            sub['his'].append(
                {
                    "timestamp": record_time,
                    "value": new_value
                }
            )

        # 将更新后的内容写回文件
        try:
            with open(SUBSCRIPTION_FILE, 'w', encoding='utf-8') as f:
                # 使用 indent=4 使 JSON 文件格式化，更易读
                json.dump(subscriptions, f, ensure_ascii=False, indent=4)
            pylog.info(f"所有订阅已更新，并成功写回文件 '{SUBSCRIPTION_FILE}'。")
        except IOError as e:
            pylog.error(f"无法将更新写入文件 '{SUBSCRIPTION_FILE}': {e}")

        # 等待
        pylog.info(f"本轮查询结束，程序将休眠 {WAIT_TIME} 秒。")
        await asyncio.sleep(WAIT_TIME)



if __name__ == "__main__":
    
    # 检查订阅文件是否存在，如果不存在则创建一个示例文件
    try:
        with open(SUBSCRIPTION_FILE, 'r', encoding='utf-8'):
            pass
    except FileNotFoundError:
        print(f"订阅文件 '{SUBSCRIPTION_FILE}' 未找到，将为您创建一个示例文件。")
        initial_data = [
            {
                "name": "10南 606",
                "his": [
                    {
                        "timestamp": "2025-07-14 00:00:40",
                        "value":  120.05
                    }
                ]
            },
            {
                "name": "D9东 425",
                "his": [
                    {
                        "timestamp": "2025-07-14 00:00:41",
                        "value": 41.61
                    }
                ]
            }
        ]
        with open(SUBSCRIPTION_FILE, 'w', encoding='utf-8') as f:
            json.dump(initial_data, f, ensure_ascii=False, indent=4)
        print("示例文件创建成功。")

    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n程序被用户中断。")
