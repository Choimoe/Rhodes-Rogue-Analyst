# main.py

import json
from pathlib import Path
from datetime import datetime
import logging

try:
    from src.auth import SklandAuthenticator
    from src.player import PlayerClient
    from src.rogue import RogueClient
except ImportError:
    logging.error("无法导入模块。请确保 src 文件夹及内部文件存在，并且主程序从项目根目录运行。")
    exit()

DATA_DIR = Path(__file__).parent / "data"


def load_hypergryph_token():
    from dotenv import load_dotenv
    load_dotenv()
    token = os.getenv("HYPERGRYPH_TOKEN")
    if not token:
        logging.error("HYPERGRYPH_TOKEN not found in environment variables.")
        return None
    return token


def save_data_to_file(data: dict, file_prefix: str, uid: str):
    try:
        DATA_DIR.mkdir(exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        file_path = DATA_DIR / f"{file_prefix}_{uid}_{timestamp}.json"
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
        logging.info(f"✅ 数据已成功保存至: {file_path}")
    except Exception as e:
        logging.error(f"❌ 保存文件时出错: {e}")


def display_friendly_summary(player_data: dict, rogue_data: dict):
    print("\n" + "=" * 40)
    print("森空岛实时数据概览".center(36))
    print("=" * 40)

    # 基础信息
    status = player_data.get("status", {})
    ap = status.get("ap", {})
    recovery_ts = ap.get("completeRecoveryTime", -1)
    if recovery_ts and isinstance(recovery_ts, int) and recovery_ts > 0:
        recovery_time_str = datetime.fromtimestamp(recovery_ts).strftime('%Y-%m-%d %H:%M:%S')
    else:
        recovery_time_str = "已溢出或无需恢复"

    print(f"【博士】     : {status.get('name', 'N/A')} (Lv.{status.get('level', 'N/A')})")
    print(f"【理智】     : {ap.get('current', 'N/A')} / {ap.get('max', 'N/A')}")
    print(f"  └ 恢复时间 : {recovery_time_str}")

    # 任务与剿灭
    campaign = player_data.get("campaign", {})
    routine = player_data.get("routine", {})
    print(
        f"【周常】     : 剿灭 {campaign.get('reward', {}).get('current', 'N/A')}/{campaign.get('reward', {}).get('total', 'N/A')} | 任务 {routine.get('weekly', {}).get('current', 'N/A')}/{routine.get('weekly', {}).get('total', 'N/A')}")

    # 基建
    building = player_data.get("building", {})
    drones = building.get("labor", {})
    print(f"【基建】     : 无人机 {drones.get('value', 'N/A')} / {drones.get('maxValue', 'N/A')}")

    # 集成战略
    if rogue_data and rogue_data.get("themes"):
        print("=" * 40)
        print("集成战略 (Rogue-like)".center(34))
        print("-" * 40)
        for theme in rogue_data["themes"]:
            name = theme.get('name')
            relics = theme.get('relic_count', 'N/A')
            investment = theme.get('investment_system', {}).get('current', 'N/A')
            print(f"【{name}】")
            print(f"  ├─ 收藏品 : {relics} 件")
            print(f"  └─ 源石锭 : {investment}")
    print("=" * 40 + "\n")


def main():
    logging.info("▶️ 开始获取森空岛数据...")
    token = load_hypergryph_token()
    if not token:
        logging.error("⏹️ 未找到 HYPERGRYPH_TOKEN，获取流程终止。")
        return

    authenticator = SklandAuthenticator(hypergryph_token=token)
    cred, signing_token = authenticator.authenticate()

    if not (cred and signing_token):
        logging.error("❌ 客户端认证失败，请检查你的 HYPERGRYPH_TOKEN。")
        return

    player_client = PlayerClient(session=authenticator.session, cred=cred, token=signing_token)
    if not player_client.is_ready:
        logging.error("❌ 玩家客户端初始化失败，未能找到UID。")
        return

    # 获取并保存完整的玩家数据
    full_player_data = player_client.get_player_info()
    if full_player_data:
        save_data_to_file(full_player_data, "player_info", player_client.uid)

        # 初始化并使用Rogue客户端
        rogue_client = RogueClient(player_client)
        rogue_summary_data = rogue_client.get_rogue_summary()

        # 以友好格式显示关键信息
        display_friendly_summary(full_player_data, rogue_summary_data)
    else:
        logging.error("未能获取到有效的玩家数据。")

    logging.info("⏹️ 获取流程结束。")


if __name__ == "__main__":
    import os

    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    main()

