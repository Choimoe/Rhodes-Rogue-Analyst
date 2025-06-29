from tkinter import ttk
import json

from ..utils import get_resource_path


class StyleManager:
    def __init__(self, style: ttk.Style):
        self.style = style
        self.theme = self._load_theme()
        self._configure_styles()

    def _load_theme(self):
        theme_path = get_resource_path("config/ui_theme.json")
        with open(theme_path, 'r', encoding='utf-8') as f:
            return json.load(f)

    def _configure_styles(self):
        colors = self.theme["colors"]
        fonts = self.theme["fonts"]
        family = fonts["family"]

        self.style.theme_use("clam")

        self.style.configure("TFrame", background=colors["bg"])

        self.style.configure("TLabel", background=colors["bg"], foreground=colors["fg"], font=(family, fonts["normal"]))
        self.style.configure("Title.TLabel", font=(family, fonts["large_bold"]), foreground=colors["accent"])
        self.style.configure("Header.TLabel", font=(family, fonts["bold"]))
        self.style.configure("Success.TLabel", foreground=colors["success"], font=(family, fonts["score"], "bold"))
        self.style.configure("Fail.TLabel", foreground=colors["fail"], font=(family, fonts["score"], "bold"))
        self.style.configure("Ending.TLabel", foreground=colors["fg"], font=(family, fonts["ending"]))
        self.style.configure("Rolling.TLabel", foreground=colors["rolling"], font=(family, fonts["ending"], "bold"))

        self.style.configure("Collapsible.TFrame", background=colors["collapsible_bg"], borderwidth=1, relief="solid")
        self.style.configure("Collapsible.Hover.TFrame", background=colors["collapsible_hover_bg"], borderwidth=1,
                             relief="solid")
        self.style.configure("Collapsible.TLabel", background=colors["collapsible_bg"], foreground=colors["fg"],
                             font=(family, fonts["bold"]))
        self.style.map("Collapsible.TLabel", background=[
            ("active", colors["collapsible_hover_bg"]),
            ("!active", colors["collapsible_bg"])
        ])

        self.style.configure("TButton", background=colors["accent"], foreground="white", font=(family, fonts["bold"]),
                             borderwidth=0)
        self.style.map("TButton", background=[("active", "#4a7c7d")])

        self.style.configure("Vertical.TScrollbar", gripcount=0, background=colors["accent"], troughcolor=colors["bg"],
                             bordercolor=colors["bg"], lightcolor=colors["bg"], darkcolor=colors["bg"])
        self.style.map("Vertical.TScrollbar", background=[("active", "#4a7c7d")])

    def get_font(self, name):
        fonts = self.theme["fonts"]
        return fonts["family"], fonts[name]
