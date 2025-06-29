import os
import sqlite3
import json
import logging
from typing import List, Dict, Any

from src.utils import get_persistent_path

DB_PATH = get_persistent_path("data/rogue_data.db")


class DataManager:
    def __init__(self):
        db_dir = os.path.dirname(DB_PATH)
        os.makedirs(db_dir, exist_ok=True)
        self.conn = sqlite3.connect(DB_PATH, check_same_thread=False)
        self._create_table()

    def _create_table(self):
        with self.conn:
            self.conn.execute("""
                CREATE TABLE IF NOT EXISTS rogue_runs (
                    id TEXT PRIMARY KEY,
                    uid TEXT NOT NULL,
                    theme TEXT NOT NULL,
                    start_ts INTEGER,
                    record_data TEXT
                )
            """)

    def merge_and_save_runs(self, uid: str, theme: str, new_runs: List[Dict[str, Any]]):
        if not new_runs: return

        runs_to_insert = []
        for run in new_runs:
            run_id = run.get("id")
            if not run_id: continue
            runs_to_insert.append((
                run_id, uid, theme, run.get("startTs"), json.dumps(run)
            ))

        with self.conn:
            self.conn.executemany(
                "INSERT OR REPLACE INTO rogue_runs (id, uid, theme, start_ts, record_data) VALUES (?, ?, ?, ?, ?)",
                runs_to_insert
            )
        logging.info(f"Merged and saved {len(runs_to_insert)} runs to the database.")

    def get_all_runs(self, uid: str, theme: str) -> List[Dict[str, Any]]:
        with self.conn:
            cursor = self.conn.execute(
                "SELECT record_data FROM rogue_runs WHERE uid = ? AND theme = ? ORDER BY start_ts DESC",
                (uid, theme)
            )
            return [json.loads(row[0]) for row in cursor.fetchall()]

    def close(self):
        self.conn.close()

