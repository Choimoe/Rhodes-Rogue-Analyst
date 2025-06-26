import tkinter as tk
from tkinter import ttk


class HeaderFrame(ttk.Frame):
    def __init__(self, parent, style_manager, **kwargs):
        super().__init__(parent, style="TFrame", **kwargs)
        self.style_manager = style_manager
        self._create_widgets()

    def _create_widgets(self):
        self.player_label = ttk.Label(self, style="Title.TLabel")
        self.player_label.pack()
        self.theme_label = ttk.Label(self, style="Header.TLabel")
        self.theme_label.pack()
        self.career_label = ttk.Label(self, font=self.style_manager.get_font("small"))
        self.career_label.pack(pady=(5, 0))

    def update_content(self, player_info, theme_name, career_summary):
        self.player_label.config(text=f"{player_info.get('name', 'N/A')} (Lv.{player_info.get('level', 'N/A')})")
        self.theme_label.config(text=theme_name or "")
        summary_text = f"累计投资: {career_summary.get('invest', 'N/A')} | 累计节点: {career_summary.get('node', 'N/A')} | 累计步数: {career_summary.get('step', 'N/A')}"
        self.career_label.config(text=summary_text)


class StatsFrame(ttk.Frame):
    def __init__(self, parent, style_manager, **kwargs):
        super().__init__(parent, style="TFrame", **kwargs)
        self.style_manager = style_manager
        self.frame = ttk.Frame(self, padding=(10, 5))
        self.frame.pack(fill=tk.X)
        self.frame.columnconfigure(1, weight=1)

    def update_content(self, stats_data):
        for widget in self.frame.winfo_children():
            widget.destroy()

        title_label = ttk.Label(self.frame, text=f"战绩统计 (基于 {stats_data.get('total_runs', 0)} 场有效对局)",
                                style="Header.TLabel")
        title_label.grid(row=0, column=0, columnspan=2, sticky="w", pady=(0, 5))

        total_stats = stats_data.get("total_stats", {})
        seven_day_stats = stats_data.get("seven_day_stats", {})

        ttk.Label(self.frame, text=f"总胜率({stats_data.get('total_runs', 0)}场):").grid(row=1, column=0, sticky="w")
        ttk.Label(self.frame,
                  text=f"{total_stats.get('win_rate', 'N/A')} (最高{total_stats.get('max_streak', 0)}连胜)").grid(row=1,
                                                                                                                  column=1,
                                                                                                                  sticky="w",
                                                                                                                  padx=10)

        ttk.Label(self.frame, text="总五结局:").grid(row=2, column=0, sticky="w")
        ttk.Label(self.frame,
                  text=f"{total_stats.get('fifth_rate', 'N/A')} (最高{total_stats.get('max_fifth_streak', 0)}连胜)").grid(
            row=2, column=1, sticky="w", padx=10)

        ttk.Label(self.frame, text=f"近7日({stats_data.get('seven_day_runs', 0)}场):").grid(row=3, column=0, sticky="w",
                                                                                            pady=(5, 0))
        ttk.Label(self.frame,
                  text=f"{seven_day_stats.get('win_rate', 'N/A')} (最高{seven_day_stats.get('max_streak', 0)}连胜)").grid(
            row=3, column=1, sticky="w", padx=10, pady=(5, 0))

        ttk.Label(self.frame, text="近7日五结局:").grid(row=4, column=0, sticky="w")
        ttk.Label(self.frame,
                  text=f"{seven_day_stats.get('fifth_rate', 'N/A')} (最高{seven_day_stats.get('max_fifth_streak', 0)}连胜)").grid(
            row=4, column=1, sticky="w", padx=10)


class RunsListFrame(ttk.Frame):
    def __init__(self, parent, style_manager, **kwargs):
        super().__init__(parent, style="TFrame", **kwargs)
        self.style_manager = style_manager
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)

        canvas = tk.Canvas(self, bg=self.style_manager.theme["colors"]["bg"], highlightthickness=0)
        scrollbar = ttk.Scrollbar(self, orient="vertical", command=canvas.yview, style="Vertical.TScrollbar")
        self.scrollable_frame = ttk.Frame(canvas, style="TFrame")

        self.scrollable_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas_frame_id = canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.bind("<Configure>", lambda e: canvas.itemconfig(canvas_frame_id, width=e.width))
        canvas.bind_all("<MouseWheel>", lambda e: canvas.yview_scroll(int(-1 * (e.delta / 120)), "units"))

        canvas.grid(row=0, column=0, sticky="nsew")
        scrollbar.grid(row=0, column=1, sticky="ns")
        self.scrollable_frame.columnconfigure(0, weight=1)

    def update_content(self, runs):
        for widget in self.scrollable_frame.winfo_children():
            widget.destroy()

        if not runs: return

        for i, run in enumerate(runs):
            run_frame = ttk.Frame(self.scrollable_frame, style="TFrame")
            run_frame.grid(row=i, column=0, sticky="ew", pady=(0, 15))

            run_frame.columnconfigure(3, weight=1)

            time_frame = ttk.Frame(run_frame)
            time_frame.grid(row=0, column=0, sticky="ns", padx=(0, 10))
            ttk.Label(time_frame, text=run.get("start_date", "N/A"), font=self.style_manager.get_font("normal")).pack(
                anchor="w")
            ttk.Label(time_frame, text=run.get("duration_hours", "N/A"),
                      font=self.style_manager.get_font("small")).pack(anchor="w")

            ttk.Label(run_frame, text=f"N{run.get('difficulty', '')}", style="Header.TLabel").grid(row=0, column=1,
                                                                                                   sticky="w",
                                                                                                   padx=(0, 10))
            ttk.Label(run_frame, text=run.get("squad", ""), font=self.style_manager.get_font("normal")).grid(row=0,
                                                                                                             column=2,
                                                                                                             sticky="w",
                                                                                                             padx=(
                                                                                                             0, 10))

            result_frame = ttk.Frame(run_frame, style="TFrame")
            result_frame.grid(row=0, column=3, sticky="e")
            score_style = "Success.TLabel" if run.get("is_success") else "Fail.TLabel"
            ttk.Label(result_frame, text=f"{run.get('score', 'N/A')}({run.get('totem_count', 0)}构)",
                      style=score_style).pack(anchor="e")

            ending_text = run.get("ending", "N/A")

            if run.get("is_rolling") and not run.get("is_success"):
                parts = ending_text.split(" (滚动)")
                ending_label_frame = ttk.Frame(result_frame, style="TFrame")
                ending_label_frame.pack(anchor="e")
                ttk.Label(ending_label_frame, text=parts[0], style="Ending.TLabel").pack(side=tk.LEFT)
                ttk.Label(ending_label_frame, text=" (滚动)", style="Rolling.TLabel").pack(side=tk.LEFT)
            else:
                ending_style = "Rolling.TLabel" if "滚动" in ending_text else "Ending.TLabel"
                ttk.Label(result_frame, text=ending_text, style=ending_style).pack(anchor="e")
