import os
import logging
import configparser
import sys
import tkinter as tk
from tkinter import messagebox

try:
    from src.utils import get_resource_path, get_persistent_path
    from src.bootstrap import ensure_token_configured
    from src.api.skland_client import SklandClient
    from src.services.rogue_service import RogueService
    from src.ui.app_window import AppWindow
    from src.ui.controller import UIController
except ImportError as e:
    root = tk.Tk()
    root.withdraw()
    messagebox.showerror("启动失败", f"无法导入必要的模块，请检查项目结构。\n\n{e}")
    sys.exit(1)


def load_config():
    parser = configparser.ConfigParser()
    config_path = get_resource_path("config/app_config.ini")
    if not os.path.exists(config_path):
        root = tk.Tk()
        root.withdraw()
        messagebox.showerror("配置错误", "关键配置文件 app_config.ini 未找到。\n程序无法启动。")
        sys.exit(1)
    parser.read(config_path, encoding='utf-8')
    return parser


def setup_logging():
    log_dir = get_persistent_path("logs")
    os.makedirs(log_dir, exist_ok=True)
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(os.path.join(log_dir, "app.log"), encoding='utf-8'),
            logging.StreamHandler()
        ]
    )


def main():
    hypergryph_token = ensure_token_configured()

    setup_logging()
    logging.info("Token configured. Starting application.")

    config = load_config()

    skland_client = SklandClient(config)
    if not skland_client.authenticate(hypergryph_token):
        logging.critical("认证失败，请检查你的Token。")
        root = tk.Tk()
        root.withdraw()
        messagebox.showerror("认证失败", "无法通过您的Token进行认证。\n\n请检查.env文件中的HYPERGRYPH_TOKEN是否正确、有效。")
        return

    rogue_service = RogueService(skland_client)

    app = AppWindow(config)
    controller = UIController(app, rogue_service, "萨卡兹的无终奇语")

    controller.initial_load()
    app.mainloop()


if __name__ == "__main__":
    main()
