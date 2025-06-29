import logging
import json
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta

from .data_manager import DataManager
from ..utils import get_resource_path


class RogueService:
    def __init__(self, skland_client):
        self.client = skland_client
        self.db_manager = DataManager()
        self._load_theme_config()

    def _load_theme_config(self):
        config_path = get_resource_path("config/rogue_theme_config.json")
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                self.theme_config = json.load(f)
            logging.info("Rogue theme config loaded successfully.")
        except (FileNotFoundError, json.JSONDecodeError) as e:
            logging.error(f"Failed to load or parse rogue_theme_config.json: {e}")
            self.theme_config = {}

    def get_analysis_for_theme(self, theme_name: str) -> Optional[Dict[str, Any]]:
        raw_data = self.client.get_rogue_info()
        if not raw_data:
            return None

        target_topic = next((t for t in raw_data.get("topics", []) if t.get("name") == theme_name), None)
        if not target_topic:
            logging.warning(f"Theme '{theme_name}' not found in API response.")
            return None

        theme_config = self.theme_config.get(theme_name)
        if not theme_config:
            logging.error(f"No configuration found for theme: {theme_name}")
            return {"error": f"缺少对主题 {theme_name} 的配置"}

        if new_records := raw_data.get("history", {}).get("records"):
            self.db_manager.merge_and_save_runs(self.client.uid, theme_name, new_records)

        all_records = self.db_manager.get_all_runs(self.client.uid, theme_name)
        if not all_records:
            return None

        return self._analyze_records(raw_data, all_records, theme_name, theme_config)

    def _determine_ending(self, record: Dict[str, Any], theme_config: Dict[str, Any]) -> tuple[str, bool]:
        keys = theme_config["keys"]
        rules = theme_config["ending_rules"]

        relics = set(record.get(keys["relic_list"], []))
        is_rolling = rules["is_rolling_relic"] in relics
        is_success = record.get(keys["success_status"]) == 1

        if not is_success:
            last_stage = record.get(keys["last_stage"], "事件")
            template = rules["text_templates"]["failure_rolling" if is_rolling else "failure"]
            return template.format(last_stage=last_stage), is_rolling

        ending_2_rule = next((ending for ending in rules["endings"] if ending["name"] == "2"), None)

        final_endings = []
        if ending_2_rule and ending_2_rule["relic"] in relics:
            final_endings.append("2")
        else:
            final_endings.append(rules["default_win_ending"])

        other_ending_rules = [ending for ending in rules["endings"] if ending["name"] != "2"]
        achieved_other_endings = sorted([
            ending["name"] for ending in other_ending_rules if ending["relic"] in relics
        ])
        final_endings.extend(achieved_other_endings)

        ending_str = "".join(final_endings)

        if "5" in final_endings:
            for companion in rules.get("ending_5_companions", []):
                if companion["relic"] in relics:
                    ending_str += f" {companion['name']}"
                    break

        template_key = "success_rolling" if is_rolling else "success"
        template = rules["text_templates"][template_key]
        return template.format(endings=ending_str), is_rolling

    def _calculate_max_streak(self, records_bool_list: List[bool]) -> int:
        max_streak, current_streak = 0, 0
        for is_win in records_bool_list:
            if is_win:
                current_streak += 1
            else:
                max_streak = max(max_streak, current_streak)
                current_streak = 0
        return max(max_streak, current_streak)

    def _analyze_records(self, raw_data: Dict, all_records: List[Dict], theme_name: str, theme_config: Dict) -> Dict:
        keys = theme_config["keys"]
        analysis_rules = theme_config["analysis_rules"]
        stats_def = theme_config["stats_definitions"]["fifth_ending"]

        valid_records = [r for r in all_records if r.get(keys["score"], 0) > analysis_rules["min_score_for_valid"]]
        seven_days_ago = datetime.now() - timedelta(days=7)
        seven_day_records = [
            r for r in valid_records
            if datetime.fromtimestamp(int(r.get(keys["start_timestamp"], 0))) > seven_days_ago
        ]

        def get_stats(records: List[Dict]) -> Dict:
            total = len(records)
            if not total:
                return {"win_rate": "0.00%", "max_streak": 0, "fifth_rate": "0.00%", "max_fifth_streak": 0}

            win_bools = [r.get(keys["success_status"]) == 1 for r in records]
            win_rate = (sum(win_bools) / total) * 100
            max_streak = self._calculate_max_streak(win_bools)

            fifth_win_bools = []
            if stats_def["rule"]["type"] == "is_win_and_has_ending":
                ending_name_to_check = stats_def["rule"]["ending_name"]
                for r in records:
                    ending_str, _ = self._determine_ending(r, theme_config)
                    is_fifth_win = r.get(keys["success_status"]) == 1 and f" {ending_name_to_check}" in ending_str
                    fifth_win_bools.append(is_fifth_win)

            fifth_rate = (sum(fifth_win_bools) / total) * 100
            max_fifth_streak = self._calculate_max_streak(fifth_win_bools)

            return {
                "win_rate": f"{win_rate:.2f}%", "max_streak": max_streak,
                "fifth_rate": f"{fifth_rate:.2f}%", "max_fifth_streak": max_fifth_streak
            }

        total_stats = get_stats(valid_records)
        seven_day_stats = get_stats(seven_day_records)

        detailed_recent_runs = []
        count = self.client.config.getint("APP", "ROGUE_RECENT_RUNS_COUNT")
        for record in all_records[:count]:
            ending_str, is_rolling = self._determine_ending(record, theme_config)

            squad_name = record.get(keys["squad"][0], {}).get(keys["squad"][1], "N/A")

            start_ts = int(record.get(keys["start_timestamp"], 0))
            end_ts = int(record.get(keys["end_timestamp"], 0))

            totem_list = record.get(keys["totem_list"], [])
            totem_count = sum(
                item.get('count', 0) for item in totem_list
                if item.get('id') == analysis_rules["primary_totem_id"]
            )

            detailed_recent_runs.append({
                "difficulty": record.get(keys["difficulty"], "N/A"),
                "squad": squad_name,
                "score": record.get(keys["score"], "N/A"),
                "is_success": record.get(keys["success_status"]) == 1,
                "ending": ending_str,
                "is_rolling": is_rolling,
                "start_date": datetime.fromtimestamp(start_ts).strftime('%m-%d'),
                "duration_hours": f"{(end_ts - start_ts) / 3600:.1f}h" if start_ts and end_ts else "N/A",
                "totem_count": totem_count,
            })

        return {
            "player_info": raw_data.get("gameUserInfo", {}),
            "career_summary": raw_data.get("career", {}),
            "stats": {
                "total_runs": len(valid_records),
                "total_stats": total_stats,
                "seven_day_runs": len(seven_day_records),
                "seven_day_stats": seven_day_stats
            },
            "theme_summary": {
                "name": theme_name,
                "detailed_recent_runs": detailed_recent_runs
            }
        }
