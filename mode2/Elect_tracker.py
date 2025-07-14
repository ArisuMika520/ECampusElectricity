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
import json
import os
import buildingData
import asyncio
from Elect_bot import ElectricityMonitor
from botpy.ext.cog_yaml import read

# --- 配置 ---

# 订阅列表文件路径
SUBSCRIPTION_LIST_FILE = "sub.json"
# 订阅历史文件路径
SUBSCRIPTION_HISTORY_FILE = "his.json"
# 读取和机器人相同的配置文件
config = read(os.path.join(os.path.dirname(__file__), "config.yaml"))
# 每次轮询之间的等待时间（秒）
WAIT_TIME = config["tracker"]["check_interval"]
# 时间字符串格式
TIME_FORMAT = "%Y-%m-%d %H:%M:%S"

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
    # formatted_time = now.strftime(TIME_FORMAT)

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
        current_time_str = datetime.datetime.now().strftime(TIME_FORMAT)
        pylog.info(f"现在时间是 {current_time_str}，准备开始查询——")

        # 读取订阅列表
        try:
            with open(SUBSCRIPTION_LIST_FILE, 'r', encoding='utf-8') as f:
                sub_list = json.load(f)
            pylog.info(f"成功读取订阅文件，共找到 {len(sub_list)} 条订阅。")
        except FileNotFoundError:
            pylog.error(f"错误：订阅文件 '{SUBSCRIPTION_LIST_FILE}' 不存在。请先创建该文件。")
            pylog.info(f"将在 {WAIT_TIME} 秒后重试...")
            await asyncio.sleep(WAIT_TIME)
            continue  # 跳过本轮循环的剩余部分
        except json.JSONDecodeError:
            pylog.error(f"错误：订阅文件 '{SUBSCRIPTION_LIST_FILE}' 格式无效，无法解析。请手动调整his.json格式。")
            pylog.info(f"将在 {WAIT_TIME} 秒后重试...")
            await asyncio.sleep(WAIT_TIME)
            continue  # 跳过本轮循环的剩余部分
        

        # 存放新数据，格式为[{"name":"xx南 101","new_require":{"timestamp":"","value":0}}]
        new_data=[]
        # 对每个订阅的name进行查询并更新数据
        for name in sub_list:
            try:
                # 执行查询
                new_value = await elect_require(monitor, name)
                
                # 获取当前时间作为记录时间
                record_time = datetime.datetime.now().strftime(TIME_FORMAT)
                
                new_data.append(
                    {
                        "name": name,
                        "new_require":
                            {
                                "timestamp": record_time,
                                "value": new_value
                            }
                    }
                )
            except Exception as e:
                pylog.error(f"处理房间 '{name}' 时发生错误，已跳过。错误详情: {e}")
                continue
        pylog.debug(f"new_data\n{new_data}")
        pylog.info(f"所有订阅房间已查询完毕，准备合并入 {SUBSCRIPTION_HISTORY_FILE}")

        # 这个时候才开始读&写 SUBSCRIPTION_HISTORY_FILE，以确保最小化该json的修改耗时
        try:
            # 读取订阅历史
            with open(SUBSCRIPTION_HISTORY_FILE, 'r', encoding='utf-8') as f:
                sub_his = json.load(f)
                pylog.info(f"成功读取订阅历史，共找到 {len(sub_his)} 历史订阅房间，共计 {sum([len(_["his"]) for _ in sub_his])} 条历史数据")
        except FileNotFoundError:
            pylog.error(f"错误：订阅历史文件 '{SUBSCRIPTION_HISTORY_FILE}' 不存在。请先创建该文件。")
            pylog.info(f"将在 {WAIT_TIME} 秒后重试...")
            await asyncio.sleep(WAIT_TIME)
            continue  # 跳过本轮循环的剩余部分
        except json.JSONDecodeError:
            pylog.error(f"错误：订阅文件 '{SUBSCRIPTION_LIST_FILE}' 格式无效，无法解析。请手动调整his.json格式。")
            pylog.info(f"将在 {WAIT_TIME} 秒后重试...")
            await asyncio.sleep(WAIT_TIME)
            continue  # 跳过本轮循环的剩余部分

        # 合并数据
        pylog.debug(f"sub_his\n{sub_his}")

        # 将历史列表转换为字典，方便快速查找和更新
        sub_his_namemap = {item['name']: idx for idx,item in enumerate(sub_his)} # 构建name->idx的映射
        pylog.debug(f"sub_his_namemap\n{sub_his_namemap}")

        for new_item in new_data:
            name = new_item["name"]
            new_require = new_item["new_require"]
            
            if name not in sub_his_namemap or not isinstance(sub_his[sub_his_namemap[name]]["his"], list):
                # 如果是新房间，直接创建条目
                sub_his.append(
                    {
                        "name": name,
                        "his": [new_require]
                    }
                )
                pylog.info(f"房间 {name} 为首次记录，{new_require}")
            else:
                # 如果是已有房间，则判断数据是否变化
                last_time = ""
                last_value = -100
                # 在 sub_his 中找到数据
                old_data = sub_his[sub_his_namemap[name]]
                # 遍历 old_data 以得到最新的一次查询
                # 【可优化】直接取最后一个元素的值进行比较
                for old_item in old_data['his']:
                    if last_time == "" or datetime.datetime.strptime(last_time, TIME_FORMAT) < datetime.datetime.strptime(old_item["timestamp"], TIME_FORMAT):
                        last_time = old_item["timestamp"]
                        last_value = old_item["value"]

                if last_value == new_require["value"]:
                    pylog.info(f"房间 {name} 新查询与旧查询结果一致，不保存")
                else:
                    # 将新数据 {时间:"时间", 数值:数值} 追加到历史记录中
                    old_data['his'].append(
                        new_require
                    )
                    pylog.info(f"房间 {name} 得到新数据，{new_require}")
        
        
        # 写回 SUBSCRIPTION_HISTORY_FILE
        pylog.info(f"开始写回文件 '{SUBSCRIPTION_HISTORY_FILE}'")
        with open(SUBSCRIPTION_HISTORY_FILE, 'w', encoding='utf-8') as f:
            json.dump(sub_his, f, ensure_ascii=False, indent=4)

        pylog.info(f"所有订阅已更新，并成功写回文件 '{SUBSCRIPTION_HISTORY_FILE}'。")

        # 等待
        pylog.info(f"本轮查询结束，程序将休眠 {WAIT_TIME} 秒。")
        now = datetime.datetime.now()
        next_run_time = now + datetime.timedelta(seconds=WAIT_TIME)
        next_run_time_str = next_run_time.strftime(TIME_FORMAT) # 使用您已定义的 TIME_FORMAT 常量
        pylog.info(f"下一次查询预计将于 {next_run_time_str} 进行。\n"+30*"-")
        await asyncio.sleep(WAIT_TIME)



if __name__ == "__main__":
    pylog.info("查找订阅文件...")
    # 检查订阅列表文件是否存在，如果不存在则创建一个示例文件
    try:
        with open(SUBSCRIPTION_LIST_FILE, 'r', encoding='utf-8'):
            pylog.info(f"找到订阅列表 {SUBSCRIPTION_LIST_FILE}")
    except FileNotFoundError:
        print(f"订阅文件 '{SUBSCRIPTION_LIST_FILE}' 未找到，将为您创建一个示例文件。")
        # initial_data = []  # 如果不需要完整格式的示例文件，则创建一个空list[]即可       
        initial_data = [
            "10南 606",
            "D9东 425"
        ]
        with open(SUBSCRIPTION_LIST_FILE, 'w', encoding='utf-8') as f:
            json.dump(initial_data, f, ensure_ascii=False, indent=4)
        print("示例文件创建成功。")


    # 检查订阅历史文件是否存在，如果不存在则创建一个示例文件
    try:
        with open(SUBSCRIPTION_HISTORY_FILE, 'r', encoding='utf-8'):
            pylog.info(f"找到订阅历史 {SUBSCRIPTION_HISTORY_FILE}")
    except FileNotFoundError:
        pylog.info(f"订阅文件 '{SUBSCRIPTION_HISTORY_FILE}' 未找到，将为您创建一个示例文件。")
        # initial_data = []  # 如果不需要完整格式的示例文件，则创建一个空list[]即可       
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
        with open(SUBSCRIPTION_HISTORY_FILE, 'w', encoding='utf-8') as f:
            json.dump(initial_data, f, ensure_ascii=False, indent=4)
        print("示例文件创建成功。")
    
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n程序被用户中断。")
