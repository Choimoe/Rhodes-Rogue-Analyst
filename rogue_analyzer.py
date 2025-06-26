import os
import logging
from datetime import datetime

try:
    from src.auth import SklandAuthenticator
    from src.player import PlayerClient
    from src.rogue import RogueClient
    from src.config import ROGUE_RECENT_RUNS_COUNT
except ImportError:
    logging.error("无法导入模块。请确保 src 文件夹及内部文件存在，并且主程序从项目根目录运行。")
    exit()


def load_hypergryph_token():
    from dotenv import load_dotenv
    load_dotenv()
    token = os.getenv("HYPERGRYPH_TOKEN")
    if not token:
        logging.error("HYPERGRYPH_TOKEN not found in environment variables.")
        return None
    return token


def display_rogue_report(analysis: dict):
    """以友好的格式打印集成战略分析报告。"""
    if not analysis:
        print("未能生成分析报告。")
        return

    player_info = analysis.get("player_info", {})
    career_summary = analysis.get("career_summary", {})
    recent_stats = analysis.get("recent_stats", {})
    theme_summary = analysis.get("theme_summary", {})

    print("\n" + "=" * 80)
    print("集成战略生涯报告".center(78))
    print(f"玩家: {player_info.get('name', 'N/A')} (Lv.{player_info.get('level', 'N/A')})".center(80))
    print("=" * 80)

    # 生涯总览
    print("【生涯总览】")
    invested = career_summary.get('total_invested', 'N/A')
    nodes = career_summary.get('total_nodes', 'N/A')
    steps = career_summary.get('total_steps', 'N/A')
    print(f"  ├─ 累计投资资源: {invested}")
    print(f"  ├─ 累计通过节点: {nodes}")
    print(f"  └─ 累计探索步数: {steps}")

    print("-" * 80)

    # 近期战绩
    print("【近期战绩 (最近20场)】")
    win_rate_str = recent_stats.get('win_rate', 'N/A')
    win_streak = recent_stats.get('current_win_streak', 'N/A')
    fifth_rate_str = recent_stats.get('fifth_ending_overall_rate', 'N/A')
    fifth_streak = recent_stats.get('current_fifth_ending_streak', 'N/A')
    squad_freq = recent_stats.get('squad_frequency', 'N/A')
    print(f"  ├─ 总体战绩: 胜率 {win_rate_str} | 当前连胜: {win_streak}")
    print(f"  ├─ 五结局战绩: 胜率 {fifth_rate_str} | 当前连胜: {fifth_streak}")
    print(f"  └─ 分队统计: {squad_freq}")

    print("-" * 80)

    # 当前主题历史
    print(f"【当前主题: {theme_summary.get('name', '未知')} - 最近{ROGUE_RECENT_RUNS_COUNT}场对局详情】")
    detailed_runs = theme_summary.get('detailed_recent_runs', [])
    if detailed_runs:
        header = f"  {'日期':<5} | {'用时':<5} | {'难度':<4} | {'分队':<6} | {'得分':<7} | {'状态':<2} | 结局"
        print(header)
        print("  " + "-" * (len(header) - 2))  # Separator line
        for run in detailed_runs:
            date = run.get('start_date', 'N/A')
            duration = run.get('duration_hours', 'N/A')
            difficulty = f"难度{run.get('difficulty', ''):<2}"
            squad = run.get('squad', 'N/A')
            score = f"得分:{run.get('score', 0):<4}"
            status = f"{run.get('is_success', ''):<2}"
            ending = run.get('ending', 'N/A')
            print(f"  {date:<5} | {duration:<5} | {difficulty:<4} | {squad:<6} | {score:<7} | {status:<2} | {ending}")
    else:
        print("  └─ 未找到最近对局详情。")

    print("=" * 80 + "\n")
    print(f"报告生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}".rjust(80))


def main(theme_to_analyze: str):
    """
    主函数，负责执行完整的认证、数据获取和分析流程。
    """
    logging.info("▶️ 开始获取并分析集成战略数据...")
    token = load_hypergryph_token()
    if not token:
        logging.error("⏹️ 未找到 HYPERGRYPH_TOKEN，流程终止。")
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

    rogue_client = RogueClient(player_client)
    full_rogue_data = rogue_client.get_rogue_info()

    if full_rogue_data:
        # 对指定主题的数据进行分析
        analysis_result = rogue_client.get_theme_analysis(full_rogue_data, theme_to_analyze)

        if analysis_result:
            # 显示分析报告
            display_rogue_report(analysis_result)
        else:
            logging.error(f"未能分析主题 '{theme_to_analyze}' 的数据。")
    else:
        logging.error("未能获取到有效的集成战略数据。")

    logging.info("⏹️ 分析流程结束。")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format='%(name)s - %(levelname)s - %(message)s')

    # 指定你想要分析的肉鸽主题名称
    TARGET_THEME = "萨卡兹的无终奇语"

    main(theme_to_analyze=TARGET_THEME)