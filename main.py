# -*- coding: utf-8 -*-
import json
from pathlib import Path
from datetime import datetime
import logging

try:
    from src.fetcher import SklandAPIClient, load_hypergryph_token
except ImportError:
    logging.error("无法导入 src/fetch.py。请确保你的文件结构正确，并且主程序是从项目根目录运行的。")
    exit()

# --- 全局配置 ---
# 将数据保存在项目根目录下的 'data' 文件夹中
# 如果该文件夹不存在，程序会自动创建
DATA_DIR = Path(__file__).parent / "data"


def save_data_to_file(data: dict, uid: str):
    """
    将获取到的数据保存为带时间戳的 JSON 文件。

    Args:
        data (dict): 从 API 获取到的数据字典。
        uid (str): 玩家的 UID，用于文件名区分。
    """
    try:
        # 确保数据存储目录存在
        DATA_DIR.mkdir(exist_ok=True)

        # 使用 UID 和当前时间创建文件名，避免覆盖
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        file_path = DATA_DIR / f"skland_data_{uid}_{timestamp}.json"

        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=4)

        logging.info(f"✅ 数据已成功保存至: {file_path}")

    except IOError as e:
        logging.error(f"❌ 保存文件时出错: {e}")
    except Exception as e:
        logging.error(f"❌ 发生未知错误导致保存失败: {e}")


def display_friendly_data(data: dict):
    """
    以对用户友好的格式，在控制台打印关键信息。

    Args:
        data (dict): 包含实时数据的字典。
    """
    if not data:
        logging.warning("无可用数据，无法打印概览。")
        return

    print("\n" + "=" * 40)
    print("森空岛实时数据概览".center(36))
    print("=" * 40)

    ap = data.get("理智", {})
    current_ap = ap.get("当前值", "N/A")
    max_ap = ap.get("最大值", "N/A")
    recovery_ts = ap.get("完全恢复时间戳", -1)

    if recovery_ts and isinstance(recovery_ts, int) and recovery_ts > 0:
        try:
            recovery_time_str = datetime.fromtimestamp(recovery_ts).strftime('%Y-%m-%d %H:%M:%S')
        except (TypeError, ValueError):
            recovery_time_str = "时间戳格式无效"
    else:
        recovery_time_str = "已溢出或无需恢复"

    print(f"【理智】     : {current_ap} / {max_ap}")
    print(f"  └ 恢复时间 : {recovery_time_str}")

    # 剿灭作战
    campaign = data.get("剿灭作战", {})
    current_cp = campaign.get("本周已获取", "N/A")
    total_cp = campaign.get("本周总计", "N/A")
    print(f"【剿灭】     : {current_cp} / {total_cp} 玉")

    # 任务
    daily = data.get("每日任务", {})
    weekly = data.get("每周任务", {})
    print(
        f"【任务】     : 每日 {daily.get('已完成', 'N/A')}/{daily.get('总计', 'N/A')} | 每周 {weekly.get('已完成', 'N/A')}/{weekly.get('总计', 'N/A')}")

    print("=" * 40 + "\n")


def main():
    logging.info("▶️ 开始获取森空岛数据...")
    token = load_hypergryph_token()

    if not token:
        logging.error("⏹️ 未找到 HYPERGRYPH_TOKEN，获取流程终止。")
        return

    client = SklandAPIClient(hypergryph_token=token)

    if client.is_authenticated:
        realtime_data = client.get_realtime_data()

        if realtime_data:
            save_data_to_file(realtime_data, client.uid)

            display_friendly_data(realtime_data)
        else:
            logging.error("未能获取到有效的实时数据。")
    else:
        logging.error("❌ 客户端认证失败，请检查你的 HYPERGRYPH_TOKEN 是否有效或已过期。")

    logging.info("⏹️ 获取流程结束。")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    main()

