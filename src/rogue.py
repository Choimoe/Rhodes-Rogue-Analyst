import logging
from typing import Optional, Dict, Any
from src.player import PlayerClient
from src.config import ENDPOINTS, ROGUE_RECENT_RUNS_COUNT
from collections import Counter
from datetime import datetime


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

    def get_theme_analysis(self, full_rogue_data: Dict[str, Any], theme_name: str) -> Optional[Dict[str, Any]]:
        if not full_rogue_data:
            return None

        target_topic = next((t for t in full_rogue_data.get("topics", []) if t.get("name") == theme_name), None)
        if not target_topic:
            logging.warning(f"Could not find a rogue-like theme named '{theme_name}'.")
            return None

        history = full_rogue_data.get("history", {})
        career = full_rogue_data.get("career", {})
        game_user_info = full_rogue_data.get("gameUserInfo", {})

        if not history or not (records := history.get("records")):
            logging.warning("No historical records found for the current theme.")
            return None

        # --- Statistics Calculation ---
        total_runs = len(records)
        successful_runs = [r for r in records if r.get("success") == 1]
        win_rate = (len(successful_runs) / total_runs * 100) if total_runs > 0 else 0

        fifth_ending_wins = [r for r in successful_runs if r.get("lastStage") == "不容拒绝"]
        fifth_ending_overall_rate = (len(fifth_ending_wins) / total_runs * 100) if total_runs > 0 else 0

        current_win_streak = 0
        for record in reversed(records):
            if record.get("success") == 1:
                current_win_streak += 1
            else:
                break

        current_fifth_ending_streak = 0
        for record in reversed(records):
            if record.get("success") == 1 and record.get("lastStage") == "不容拒绝":
                current_fifth_ending_streak += 1
            else:
                break

        squad_counts = Counter(r.get("band", {}).get("name") for r in records if r.get("band", {}).get("name"))
        squad_frequency = " | ".join([f"{name}({count})" for name, count in squad_counts.most_common()])

        # --- Detailed Recent Runs (Last N) ---
        detailed_recent_runs = []
        for record in records[:ROGUE_RECENT_RUNS_COUNT]:
            start_ts = int(record.get("startTs", 0))
            end_ts = int(record.get("endTs", 0))

            start_date = datetime.fromtimestamp(start_ts).strftime('%m-%d') if start_ts > 0 else "N/A"
            duration_hours = (end_ts - start_ts) / 3600 if start_ts > 0 and end_ts > 0 else 0.0

            detailed_recent_runs.append({
                "difficulty": record.get("modeGrade", "N/A"),
                "squad": record.get("band", {}).get("name", "N/A"),
                "score": record.get("score", "N/A"),
                "is_success": "通关" if record.get("success") == 1 else "失败",
                "ending": record.get("lastStage", "N/A"),
                "start_date": start_date,
                "duration_hours": f"{duration_hours:.1f}h"
            })

        analysis = {
            "player_info": {
                "name": game_user_info.get("name"),
                "level": game_user_info.get("level")
            },
            "career_summary": {
                "total_invested": career.get("invest"),
                "total_nodes": career.get("node"),
                "total_steps": career.get("step")
            },
            "recent_stats": {
                "win_rate": f"{win_rate:.2f}%",
                "current_win_streak": current_win_streak,
                "fifth_ending_overall_rate": f"{fifth_ending_overall_rate:.2f}%",
                "current_fifth_ending_streak": current_fifth_ending_streak,
                "squad_frequency": squad_frequency,
            },
            "theme_summary": {
                "name": theme_name,
                "detailed_recent_runs": detailed_recent_runs,
            }
        }
        return analysis
