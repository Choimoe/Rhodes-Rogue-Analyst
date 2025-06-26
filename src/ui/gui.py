import os
import logging
import tkinter as tk
from tkinter import ttk
from datetime import datetime
import threading

try:
    from src.auth import SklandAuthenticator
    from src.player import PlayerClient
    from src.rogue import RogueClient
    from src.config import ROGUE_RECENT_RUNS_COUNT
except ImportError:
    logging.error("无法导入模块。请确保 src 文件夹及内部文件存在。")
    exit()


class DataController:
    def __init__(self):
        self.token = self._load_hypergryph_token()

    def _load_hypergryph_token(self):
        from dotenv import load_dotenv
        load_dotenv()
        token = os.getenv("HYPERGRYPH_TOKEN")
        if not token:
            logging.error("HYPERGRYPH_TOKEN not found in .env file.")
        return token

    def fetch_and_analyze_data(self, theme_to_analyze):
        if not self.token:
            return {"error": "未找到Token"}

        authenticator = SklandAuthenticator(hypergryph_token=self.token)
        cred, signing_token = authenticator.authenticate()
        if not (cred and signing_token):
            return {"error": "客户端认证失败"}

        player_client = PlayerClient(session=authenticator.session, cred=cred, token=signing_token)
        if not player_client.is_ready:
            return {"error": "玩家客户端初始化失败"}

        rogue_client = RogueClient(player_client)
        full_rogue_data = rogue_client.get_rogue_info()
        if not full_rogue_data:
            return {"error": "未能获取到集成战略数据"}

        return rogue_client.get_theme_analysis(full_rogue_data, theme_to_analyze)


class RogueApp(tk.Tk):
    def __init__(self, data_controller, theme):
        super().__init__()
        self.data_controller = data_controller
        self.theme_to_analyze = theme

        self.configure_styles()
        self.setup_window()
        self.create_widgets()

        self.after(100, self.initial_load)

    def configure_styles(self):
        self.BG_COLOR = "#2e2e2e"
        self.FG_COLOR = "#d0d0d0"
        self.ACCENT_COLOR = "#5f9ea0"
        self.SUCCESS_COLOR = "#81c784"
        self.FAIL_COLOR = "#e57373"
        self.ROLLING_COLOR = "#ff6961"
        self.SCROLLBAR_COLOR = "#4a4a4a"
        self.FONT_FAMILY = "Microsoft YaHei"
        self.FONT_NORMAL = (self.FONT_FAMILY, 12)
        self.FONT_BOLD = (self.FONT_FAMILY, 12, "bold")
        self.FONT_SCORE = (self.FONT_FAMILY, 14, "bold")
        self.FONT_LARGE_BOLD = (self.FONT_FAMILY, 16, "bold")
        self.FONT_SMALL = (self.FONT_FAMILY, 10)
        self.FONT_ENDING = (self.FONT_FAMILY, 10)

        style = ttk.Style(self)
        style.theme_use("clam")
        style.configure("TFrame", background=self.BG_COLOR)
        style.configure("TLabel", background=self.BG_COLOR, foreground=self.FG_COLOR, font=self.FONT_NORMAL)
        style.configure("Title.TLabel", font=self.FONT_LARGE_BOLD, foreground=self.ACCENT_COLOR)
        style.configure("Header.TLabel", font=self.FONT_BOLD)
        style.configure("Success.TLabel", foreground=self.SUCCESS_COLOR, font=self.FONT_SCORE)
        style.configure("Fail.TLabel", foreground=self.FAIL_COLOR, font=self.FONT_SCORE)
        style.configure("Ending.TLabel", foreground=self.FG_COLOR, font=self.FONT_ENDING)
        style.configure("Rolling.TLabel", foreground=self.ROLLING_COLOR, font=self.FONT_ENDING, weight="bold")
        style.configure("TButton", background=self.ACCENT_COLOR, foreground="white", font=self.FONT_BOLD, borderwidth=0)
        style.map("TButton", background=[("active", "#4a7c7d")])
        style.configure("Vertical.TScrollbar", gripcount=0, background=self.ACCENT_COLOR, troughcolor=self.BG_COLOR,
                        bordercolor=self.BG_COLOR, lightcolor=self.BG_COLOR, darkcolor=self.BG_COLOR)
        style.map("Vertical.TScrollbar", background=[("active", "#4a7c7d")])

    def setup_window(self):
        self.title("集成战略数据分析")
        self.geometry("520x820")
        self.minsize(480, 600)
        self.resizable(True, True)
        self.configure(bg=self.BG_COLOR)

    def create_widgets(self):
        self.main_frame = ttk.Frame(self, padding=20)
        self.main_frame.pack(fill=tk.BOTH, expand=True)
        self.main_frame.columnconfigure(0, weight=1)
        self.main_frame.rowconfigure(3, weight=1)

        self.header_frame = ttk.Frame(self.main_frame, style="TFrame")
        self.header_frame.grid(row=0, column=0, sticky="ew")

        self.stats_frame = ttk.Frame(self.main_frame, style="TFrame")
        self.stats_frame.grid(row=1, column=0, sticky="ew", pady=(10, 15))

        self.runs_header_label = ttk.Label(self.main_frame, text=f"最近{ROGUE_RECENT_RUNS_COUNT}场对局详情",
                                           style="Header.TLabel", padding=(0, 5))
        self.runs_header_label.grid(row=2, column=0, sticky="w")

        self.create_runs_list_widgets(self.main_frame)

        self.footer_frame = ttk.Frame(self.main_frame, style="TFrame", padding=(0, 10))
        self.footer_frame.grid(row=4, column=0, sticky="ew")

        self.refresh_button = ttk.Button(self.footer_frame, text="刷新", command=self.refresh_data, style="TButton")
        self.refresh_button.pack(pady=10)

        self.status_label = ttk.Label(self.footer_frame, text="准备就绪", anchor="center", font=self.FONT_SMALL)
        self.status_label.pack(fill=tk.X)

    def _on_mousewheel(self, event):
        if event.num == 5 or event.delta == -120:
            self.canvas.yview_scroll(1, "units")
        if event.num == 4 or event.delta == 120:
            self.canvas.yview_scroll(-1, "units")

    def create_runs_list_widgets(self, parent):
        container = ttk.Frame(parent)
        container.grid(row=3, column=0, sticky="nsew")
        container.columnconfigure(0, weight=1)
        container.rowconfigure(0, weight=1)

        self.canvas = tk.Canvas(container, bg=self.BG_COLOR, highlightthickness=0)
        scrollbar = ttk.Scrollbar(container, orient="vertical", command=self.canvas.yview, style="Vertical.TScrollbar")

        self.scrollable_frame = ttk.Frame(self.canvas, style="TFrame")

        self.scrollable_frame.bind("<Configure>", lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")))
        canvas_frame_id = self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        self.canvas.configure(yscrollcommand=scrollbar.set)

        self.canvas.bind_all("<MouseWheel>", self._on_mousewheel)
        self.canvas.bind_all("<Button-4>", self._on_mousewheel)
        self.canvas.bind_all("<Button-5>", self._on_mousewheel)

        self.canvas.bind("<Configure>", lambda e: self.canvas.itemconfig(canvas_frame_id, width=e.width))

        self.canvas.grid(row=0, column=0, sticky="nsew")
        scrollbar.grid(row=0, column=1, sticky="ns")

        self.scrollable_frame.columnconfigure(0, weight=1)

    def initial_load(self):
        self.refresh_data()

    def refresh_data(self):
        self.status_label.config(text="正在获取数据...")
        self.refresh_button.config(state=tk.DISABLED)

        thread = threading.Thread(target=self._fetch_data_thread, daemon=True)
        thread.start()

    def _fetch_data_thread(self):
        data = self.data_controller.fetch_and_analyze_data(self.theme_to_analyze)
        self.after(0, self.update_ui, data)

    def update_ui(self, data):
        self._clear_frame(self.header_frame)
        self._clear_frame(self.stats_frame)
        self._clear_frame(self.scrollable_frame)

        if data and "error" not in data:
            self._update_header(data.get("player_info", {}), data.get("theme_summary", {}).get("name"))
            self._update_career_summary(data.get("career_summary", {}))
            self._update_recent_stats(data.get("recent_stats", {}))
            self._update_runs_list(data.get("theme_summary", {}).get("detailed_recent_runs", []))
            self.status_label.config(text=f"数据于 {datetime.now().strftime('%H:%M:%S')} 更新")
        else:
            error_msg = data.get("error", "未知错误") if data else "未能获取数据"
            ttk.Label(self.header_frame, text=error_msg, style="Fail.TLabel", font=self.FONT_LARGE_BOLD).pack(pady=20)
            self.status_label.config(text="获取失败")

        self.refresh_button.config(state=tk.NORMAL)

    def _clear_frame(self, frame):
        for widget in frame.winfo_children():
            widget.destroy()

    def _update_header(self, player_info, theme_name):
        ttk.Label(self.header_frame, text=f"{player_info.get('name', 'N/A')} (Lv.{player_info.get('level', 'N/A')})",
                  style="Title.TLabel").pack()
        ttk.Label(self.header_frame, text=theme_name or "", style="Header.TLabel").pack()

    def _update_career_summary(self, career_summary):
        summary_text = f"累计投资: {career_summary.get('total_invested', 'N/A')} | 累计节点: {career_summary.get('total_nodes', 'N/A')} | 累计步数: {career_summary.get('total_steps', 'N/A')}"
        ttk.Label(self.header_frame, text=summary_text, font=self.FONT_SMALL, wraplength=520).pack(pady=(5, 0))

    def _update_recent_stats(self, recent_stats):
        frame = ttk.Frame(self.stats_frame, padding=(10, 5))
        frame.pack(fill=tk.X)

        ttk.Label(frame, text=f"20场战绩:", style="Header.TLabel").grid(row=0, column=0, sticky="w")
        ttk.Label(frame,
                  text=f"胜率 {recent_stats.get('win_rate', 'N/A')} | 当前连胜: {recent_stats.get('current_win_streak', 'N/A')}").grid(
            row=0, column=1, sticky="w", padx=10)

        ttk.Label(frame, text=f"五结局战绩:", style="Header.TLabel").grid(row=1, column=0, sticky="w")
        ttk.Label(frame,
                  text=f"胜率 {recent_stats.get('fifth_ending_overall_rate', 'N/A')} | 当前连胜: {recent_stats.get('current_fifth_ending_streak', 'N/A')}").grid(
            row=1, column=1, sticky="w", padx=10)

    def _update_runs_list(self, runs):
        if not runs: return

        for i, run in enumerate(runs):
            run_frame = ttk.Frame(self.scrollable_frame, style="TFrame")
            run_frame.grid(row=i, column=0, sticky="ew", pady=(0, 15))

            run_frame.columnconfigure(0, minsize=55)
            run_frame.columnconfigure(1, minsize=55)
            run_frame.columnconfigure(2, minsize=100)
            run_frame.columnconfigure(3, weight=1)

            time_frame = ttk.Frame(run_frame)
            time_frame.grid(row=0, column=0, sticky="ns", padx=(0, 10))
            ttk.Label(time_frame, text=run.get("start_date", "N/A"), font=self.FONT_NORMAL).pack(anchor="w")
            ttk.Label(time_frame, text=run.get("duration_hours", "N/A"), font=self.FONT_SMALL).pack(anchor="w")

            difficulty = f"N{run.get('difficulty', '')}"
            ttk.Label(run_frame, text=difficulty, style="Header.TLabel").grid(row=0, column=1, sticky="w")

            squad_name = run.get("squad", "")
            ttk.Label(run_frame, text=squad_name, font=self.FONT_NORMAL).grid(row=0, column=2, sticky="w")

            result_frame = ttk.Frame(run_frame, style="TFrame")
            result_frame.grid(row=0, column=3, sticky="e")

            score_text = f"{run.get('score', 'N/A')}({run.get('totem_count', 0)}构)"
            score_style = "Success.TLabel" if run.get("is_success") else "Fail.TLabel"
            ttk.Label(result_frame, text=score_text, style=score_style).pack(anchor="e")

            ending_text = run.get("ending", "N/A")
            ending_style = "Rolling.TLabel" if run.get("is_rolling") else "Ending.TLabel"
            ttk.Label(result_frame, text=ending_text, style=ending_style).pack(anchor="e")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format='%(name)s - %(levelname)s - %(message)s')

    controller = DataController()
    theme = "萨卡兹的无终奇语"

    app = RogueApp(controller, theme)
    app.mainloop()
