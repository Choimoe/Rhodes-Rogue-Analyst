# src/rogue.py

import logging
from typing import Optional, Dict, Any, List
from src.player import PlayerClient


class RogueClient:
    def __init__(self, player_client: PlayerClient):
        if not isinstance(player_client, PlayerClient) or not player_client.is_ready:
            raise ValueError("A ready PlayerClient instance is required.")
        self.player_client = player_client

    def get_rogue_summary(self) -> Optional[Dict[str, Any]]:
        player_info = self.player_client.get_player_info()
        if not player_info:
            logging.error("Failed to get player info, cannot extract rogue data.")
            return None

        rogue_data = player_info.get("rogue")
        if not rogue_data:
            logging.warning("No rogue-like data found in player info.")
            return None

        # Process and structure the rogue-like data
        summary = {"themes": []}
        records = rogue_data.get("records", [])
        info_map = player_info.get("rogueInfoMap", {})

        for record in records:
            theme_id = record.get("rogueId")
            theme_info = info_map.get(theme_id, {})
            theme_name = theme_info.get("name", f"未知主题 ({theme_id})")

            summary["themes"].append({
                "name": theme_name,
                "relic_count": record.get("relicCnt"),
                "investment_system": record.get("bank", {})
            })

        return summary
