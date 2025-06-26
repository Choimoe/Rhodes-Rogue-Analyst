import logging
from typing import Optional, Dict, Any
from collections import Counter
from datetime import datetime, timedelta
from .data_manager import DataManager

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


class RogueService:
    def __init__(self, skland_client):
        self.client = skland_client
        self.db_manager = DataManager()

    def get_analysis_for_theme(self, theme_name: str) -> Optional[Dict[str, Any]]:
        raw_data = self.client.get_rogue_info()
        if not raw_data: return None

        target_topic = next((t for t in raw_data.get("topics", []) if t.get("name") == theme_name), None)
        if not target_topic: return None

        if new_records := raw_data.get("history", {}).get("records"):
            self.db_manager.merge_and_save_runs(self.client.uid, theme_name, new_records)

        all_records = self.db_manager.get_all_runs(self.client.uid, theme_name)
        if not all_records: return None

        return self._analyze_records(raw_data, all_records, theme_name)

    def _determine_ending(self, record: Dict[str, Any]) -> tuple[str, bool]:
        relics = record.get("gainRelicList", [])
        is_rolling = RELIC_MAPPING["ROLLING"] in relics

        if record.get("success") != 1:
            last_stage = record.get("lastStage")
            ending_text = f"驻足于: {last_stage or '事件'}"
            if is_rolling:
                ending_text += " (滚动)"
            return ending_text, is_rolling

        ending_parts = ["滚动"] if is_rolling else []
        ending_numbers = sorted(
            [num for id, num in [("ENDING_2", "2"), ("ENDING_3", "3"), ("ENDING_4", "4"), ("ENDING_5", "5")] if
             RELIC_MAPPING[id] in relics])

        if "2" not in ending_numbers:
            ending_parts.insert(0 if not is_rolling else 1, "1")

        ending_parts.append("".join(ending_numbers))

        if "5" in ending_numbers:
            if RELIC_MAPPING["EGG_SUPER"] in relics:
                ending_parts.append("超大蛋")
            elif RELIC_MAPPING["EGG_BIG"] in relics:
                ending_parts.append("大蛋")
            elif RELIC_MAPPING["EGG_SMALL"] in relics:
                ending_parts.append("小蛋")

        return f"完成结局: {' '.join(ending_parts)}", is_rolling

    def _calculate_max_streak(self, records_bool_list):
        max_streak, current_streak = 0, 0
        for is_win in records_bool_list:
            if is_win:
                current_streak += 1
            else:
                max_streak = max(max_streak, current_streak)
                current_streak = 0
        return max(max_streak, current_streak)

    def _analyze_records(self, raw_data, all_records, theme_name):
        valid_records = [r for r in all_records if r.get("score", 0) > 100]
        seven_days_ago = datetime.now() - timedelta(days=7)
        seven_day_records = [r for r in valid_records if
                             datetime.fromtimestamp(int(r.get("startTs", 0))) > seven_days_ago]

        def get_stats(records):
            total = len(records)
            if not total: return {"win_rate": "0.00%", "max_streak": 0, "fifth_rate": "0.00%", "max_fifth_streak": 0}

            wins = [r for r in records if r.get("success") == 1]
            win_rate = (len(wins) / total) * 100
            max_streak = self._calculate_max_streak([r.get("success") == 1 for r in records])

            fifth_wins = [r for r in wins if self._determine_ending(r)[0].startswith("完成结局: 5") or "滚动 5" in
                          self._determine_ending(r)[0]]
            fifth_rate = (len(fifth_wins) / total) * 100
            max_fifth_streak = self._calculate_max_streak([(r.get("success") == 1 and (
                        self._determine_ending(r)[0].startswith("完成结局: 5") or "滚动 5" in self._determine_ending(r)[
                    0])) for r in records])

            return {"win_rate": f"{win_rate:.2f}%", "max_streak": max_streak, "fifth_rate": f"{fifth_rate:.2f}%",
                    "max_fifth_streak": max_fifth_streak}

        total_stats = get_stats(valid_records)
        seven_day_stats = get_stats(seven_day_records)

        detailed_recent_runs = []
        for record in all_records[:self.client.config.getint("APP", "ROGUE_RECENT_RUNS_COUNT")]:
            ending_str, is_rolling = self._determine_ending(record)
            detailed_recent_runs.append({
                "difficulty": record.get("modeGrade", "N/A"), "squad": record.get("band", {}).get("name", "N/A"),
                "score": record.get("score", "N/A"), "is_success": record.get("success") == 1, "ending": ending_str,
                "is_rolling": is_rolling,
                "start_date": datetime.fromtimestamp(int(record.get("startTs", 0))).strftime('%m-%d'),
                "duration_hours": f"{(int(record.get('endTs', 0)) - int(record.get('startTs', 0))) / 3600:.1f}h",
                "totem_count": sum(item.get('count', 0) for item in record.get("totemList", []) if
                                   item.get('id') == 'rogue_4_fragment_I_1'),
            })

        return {
            "player_info": raw_data.get("gameUserInfo", {}),
            "career_summary": raw_data.get("career", {}),
            "stats": {
                "total_runs": len(valid_records), "total_stats": total_stats,
                "seven_day_runs": len(seven_day_records), "seven_day_stats": seven_day_stats
            },
            "theme_summary": {"name": theme_name, "detailed_recent_runs": detailed_recent_runs}
        }
