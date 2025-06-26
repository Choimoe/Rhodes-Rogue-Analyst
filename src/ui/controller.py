import threading
import logging
from datetime import datetime

class UIController:
    def __init__(self, app_window, rogue_service, theme):
        self.app = app_window
        self.service = rogue_service
        self.theme = theme
        self.app.set_refresh_command(self.refresh_data)

    def initial_load(self):
        self.app.after(100, self.refresh_data)

    def refresh_data(self):
        self.app.show_status("正在获取数据...", is_loading=True)
        threading.Thread(target=self._fetch_data_thread, daemon=True).start()

    def _fetch_data_thread(self):
        try:
            analysis_data = self.service.get_analysis_for_theme(self.theme)
            self.app.after(0, self.update_ui, analysis_data)
        except Exception as e:
            logging.error(f"Error in data fetch thread: {e}")
            self.app.after(0, self.update_ui, {"error": f"发生意外错误: {e}"})

    def update_ui(self, data):
        if data and "error" not in data:
            self.app.header.update_content(data["player_info"], data["theme_summary"]["name"], data["career_summary"])
            self.app.stats.update_content(data["stats"])
            self.app.runs_list.update_content(data["theme_summary"]["detailed_recent_runs"])
            self.app.show_status(f"数据于 {datetime.now().strftime('%H:%M:%S')} 更新")
        else:
            error_msg = data.get("error", "未知错误") if data else "未能获取数据"
            self.app.show_error(error_msg)
            self.app.show_status("获取失败")
