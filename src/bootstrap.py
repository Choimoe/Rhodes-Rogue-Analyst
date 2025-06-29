import os
import sys
import tkinter as tk
from tkinter import messagebox
from dotenv import load_dotenv

from .utils import get_persistent_path


def ensure_token_configured() -> str:
    dotenv_path = get_persistent_path(".env")
    env_template = "HYPERGRYPH_TOKEN=\"\"\n"

    if not os.path.exists(dotenv_path):
        try:
            with open(dotenv_path, "w", encoding="utf-8") as f:
                f.write(env_template)

            root = tk.Tk()
            root.withdraw()
            messagebox.showinfo(
                "首次配置向导",
                "请在程序目录下的 .env 文件中填入您的 HYPERGRYPH_TOKEN 后，再重新启动程序。"
            )
        except Exception as e:
            root = tk.Tk()
            root.withdraw()
            messagebox.showerror("文件创建失败", f"尝试创建 .env 文件时出错: {e}")
        sys.exit(0)

    load_dotenv(dotenv_path=dotenv_path)
    token = os.getenv("HYPERGRYPH_TOKEN")

    if not token:
        root = tk.Tk()
        root.withdraw()
        messagebox.showwarning(
            "凭证未填写",
            "请在 .env 文件中填入您的 HYPERGRYPH_TOKEN 后，再重新启动程序。"
        )
        sys.exit(1)

    return token
