import tkinter as tk
from tkinter import ttk
from .styles import StyleManager
from .components import HeaderFrame, StatsFrame, RunsListFrame

class AppWindow(tk.Tk):
    def __init__(self, config):
        super().__init__()
        self.config = config
        self.style_manager = StyleManager(ttk.Style(self))
        self.setup_window()
        self.create_widgets()

    def setup_window(self):
        self.title("罗德岛集成战略分析仪")
        self.geometry("360x820")
        self.minsize(320, 350)
        self.configure(bg=self.style_manager.theme["colors"]["bg"])

    def create_widgets(self):
        main_frame = ttk.Frame(self, padding=20)
        main_frame.pack(fill=tk.BOTH, expand=True)
        main_frame.columnconfigure(0, weight=1)
        main_frame.rowconfigure(2, weight=1)

        self.header = HeaderFrame(main_frame, self.style_manager)
        self.header.grid(row=0, column=0, sticky="ew", pady=(0, 10))

        self.stats = StatsFrame(main_frame, self.style_manager)
        self.stats.grid(row=1, column=0, sticky="ew", pady=(0, 15))

        runs_area_frame = ttk.Frame(main_frame, style="TFrame")
        runs_area_frame.grid(row=2, column=0, sticky="nsew")
        runs_area_frame.columnconfigure(0, weight=1)
        runs_area_frame.rowconfigure(1, weight=1)

        self.runs_header_label = ttk.Label(runs_area_frame, text=f"最近{self.config.getint('APP', 'ROGUE_RECENT_RUNS_COUNT')}场对局详情", style="Header.TLabel")
        self.runs_header_label.grid(row=0, column=0, sticky="nw", pady=(0, 5))

        self.runs_list = RunsListFrame(runs_area_frame, self.style_manager)
        self.runs_list.grid(row=1, column=0, sticky="nsew")

        footer_frame = ttk.Frame(main_frame, style="TFrame")
        footer_frame.grid(row=3, column=0, sticky="ew", pady=(10, 0))
        self.refresh_button = ttk.Button(footer_frame, text="刷新")
        self.refresh_button.pack(pady=10)
        self.status_label = ttk.Label(footer_frame, text="准备就绪", font=self.style_manager.get_font("small"), anchor="center")
        self.status_label.pack(fill=tk.X)

    def set_refresh_command(self, command):
        self.refresh_button.config(command=command)

    def show_status(self, message, is_loading=False):
        self.status_label.config(text=message)
        self.refresh_button.config(state=tk.DISABLED if is_loading else tk.NORMAL)

    def show_error(self, message):
        for child in [self.header, self.stats, self.runs_list]:
            for widget in child.winfo_children():
                 widget.destroy()

        ttk.Label(self.header, text=message, style="Fail.TLabel", font=self.style_manager.get_font("large_bold")).pack(pady=20)
