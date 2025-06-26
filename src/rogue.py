import logging
from typing import Optional, Dict, Any, List
from src.player import PlayerClient
from src.config import ENDPOINTS, ROGUE_RECENT_RUNS_COUNT
from collections import Counter
from datetime import datetime

RELIC_MAPPING = {
    "ENDING_2": "rogue_4_relic_final_1",
    "ENDING_3": "rogue_4_relic_final_4",
    "ENDING_4": "rogue_4_relic_final_6",
    "ENDING_5": "rogue_4_relic_final_11",
    "EGG_SMALL": "rogue_4_relic_final_8",
    "EGG_BIG": "rogue_4_relic_final_9",
    "EGG_SUPER": "rogue_4_relic_final_10",
    "ROLLING": "rogue_4_relic_explore_7",
}


class RogueClient:
    def __init__(self, player_client: PlayerClient):
        if not isinstance(player_client, PlayerClient) or not player_client.is_ready:
            raise ValueError("A ready PlayerClient instance is required.")
        self.player_client = player_client

    def get_rogue_info(self) -> Optional[Dict[str, Any]]:
        logging.info("Fetching detailed rogue-like data from dedicated endpoint...")
        params = {"uid": self.player_client.uid}
        full_url_for_signing = f"{ENDPOINTS['ROGUE_INFO']}?uid={params['uid']}"

        try:
            headers = self.player_client._generate_signature_headers(url=full_url_for_signing)
            response = self.player_client.session.get(ENDPOINTS["ROGUE_INFO"], params=params, headers=headers,
                                                      timeout=10)
            response.raise_for_status()
            data = response.json()

            if data.get("code") == 0:
                logging.info("Successfully fetched rogue-like data.")
                return data.get("data")
            else:
                logging.error(f"API Error fetching rogue data: {data.get('message', 'Unknown error')}")
                return None
        except Exception as e:
            logging.error(f"An unexpected error occurred while fetching rogue data: {e}")
            return None

    def _determine_ending(self, record: Dict[str, Any]) -> tuple[str, bool]:
        relics = record.get("gainRelicList", [])
        is_rolling = RELIC_MAPPING["ROLLING"] in relics

        ending_parts = []
        if is_rolling:
            ending_parts.append("滚动")

        ending_numbers = []
        if RELIC_MAPPING["ENDING_2"] in relics:
            ending_numbers.append("2")
        else:
            ending_numbers.append("1")
        if RELIC_MAPPING["ENDING_3"] in relics: ending_numbers.append("3")
        if RELIC_MAPPING["ENDING_4"] in relics: ending_numbers.append("4")
        if RELIC_MAPPING["ENDING_5"] in relics: ending_numbers.append("5")

        ending_parts.append("".join(sorted(ending_numbers)))
        if "5" in ending_numbers:
            if RELIC_MAPPING["EGG_SUPER"] in relics:
                ending_parts.append("超大蛋")
            elif RELIC_MAPPING["EGG_BIG"] in relics:
                ending_parts.append("大蛋")
            elif RELIC_MAPPING["EGG_SMALL"] in relics:
                ending_parts.append("小蛋")

        return " ".join(ending_parts), is_rolling

    def get_theme_analysis(self, full_rogue_data: Dict[str, Any], theme_name: str) -> Optional[Dict[str, Any]]:
        if not full_rogue_data: return None
        target_topic = next((t for t in full_rogue_data.get("topics", []) if t.get("name") == theme_name), None)
        if not target_topic: return None

        history = full_rogue_data.get("history", {})
        career = full_rogue_data.get("career", {})
        game_user_info = full_rogue_data.get("gameUserInfo", {})
        if not history or not (records := history.get("records")): return None

        total_runs = len(records)
        successful_runs = [r for r in records if r.get("success") == 1]
        win_rate = (len(successful_runs) / total_runs * 100) if total_runs > 0 else 0

        fifth_ending_wins = [r for r in successful_runs if self._determine_ending(r)[0].startswith(("5", "滚动 5"))]
        fifth_ending_overall_rate = (len(fifth_ending_wins) / total_runs * 100) if total_runs > 0 else 0

        current_win_streak = sum(1 for r in reversed(records) if r.get("success") == 1) if records and records[0].get(
            "success") == 1 else 0
        current_fifth_ending_streak = sum(
            1 for r in reversed(records) if self._determine_ending(r)[0].startswith(("5", "滚动 5"))) if records and \
                                                                                                         self._determine_ending(
                                                                                                             records[
                                                                                                                 0])[
                                                                                                             0].startswith(
                                                                                                             ("5",
                                                                                                              "滚动 5")) else 0

        squad_counts = Counter(r.get("band", {}).get("name") for r in records if r.get("band", {}).get("name"))
        squad_frequency = " | ".join([f"{name}({count})" for name, count in squad_counts.most_common()])

        detailed_recent_runs = []
        for record in records[:ROGUE_RECENT_RUNS_COUNT]:
            start_ts = int(record.get("startTs", 0))
            end_ts = int(record.get("endTs", 0))
            is_success = record.get("success") == 1

            if is_success:
                ending_str, is_rolling = self._determine_ending(record)
                ending_text = f"完成: {ending_str}"
            else:
                last_stage = record.get("lastStage")
                ending_text = f"驻足在 {last_stage or '事件'}"
                is_rolling = False

            detailed_recent_runs.append({
                "difficulty": record.get("modeGrade", "N/A"),
                "squad": record.get("band", {}).get("name", "N/A"),
                "score": record.get("score", "N/A"),
                "is_success": is_success,
                "ending": ending_text,
                "is_rolling": is_rolling,
                "start_date": datetime.fromtimestamp(start_ts).strftime('%m-%d') if start_ts > 0 else "N/A",
                "duration_hours": f"{(end_ts - start_ts) / 3600:.1f}h" if start_ts > 0 and end_ts > 0 else "N/A",
                "totem_count": sum(item.get('count', 0) for item in record.get("totemList", []) if
                                   item.get('id') == 'rogue_4_fragment_I_1'),
            })

        return {
            "player_info": {"name": game_user_info.get("name"), "level": game_user_info.get("level")},
            "career_summary": {"total_invested": career.get("invest"), "total_nodes": career.get("node"),
                               "total_steps": career.get("step")},
            "recent_stats": {
                "win_rate": f"{win_rate:.2f}%", "current_win_streak": current_win_streak,
                "fifth_ending_overall_rate": f"{fifth_ending_overall_rate:.2f}%",
                "current_fifth_ending_streak": current_fifth_ending_streak,
                "squad_frequency": squad_frequency,
            },
            "theme_summary": {"name": theme_name, "detailed_recent_runs": detailed_recent_runs}
        }
