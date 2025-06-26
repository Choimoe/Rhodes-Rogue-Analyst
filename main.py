import os
import logging
import configparser
from pathlib import Path

try:
    from src.api.skland_client import SklandClient
    from src.services.rogue_service import RogueService
    from src.ui.app_window import AppWindow
    from src.ui.controller import UIController
except ImportError as e:
    logging.critical(f"启动失败: 无法导入必要的模块。请检查项目结构。 {e}")
    exit()


def load_config():
    parser = configparser.ConfigParser()
    config_path = Path(__file__).parent / "config" / "app_config.ini"
    if not config_path.exists():
        logging.critical(f"配置文件未找到: {config_path}")
        exit()
    parser.read(config_path, encoding='utf-8')
    return parser


def load_token():
    from dotenv import load_dotenv
    load_dotenv()
    token = os.getenv("HYPERGRYPH_TOKEN")
    if not token:
        logging.critical("HYPERGRYPH_TOKEN not found in .env file. Application cannot start.")
        exit()
    return token


def setup_logging():
    log_dir = Path(__file__).parent / "logs"
    log_dir.mkdir(exist_ok=True)
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_dir / "app.log", encoding='utf-8'),
            logging.StreamHandler()
        ]
    )


def main():
    setup_logging()
    config = load_config()
    hypergryph_token = load_token()

    skland_client = SklandClient(config)
    if not skland_client.authenticate(hypergryph_token):
        logging.critical("认证失败，程序退出。请检查你的Token。")
        return

    rogue_service = RogueService(skland_client)

    app = AppWindow(config)
    controller = UIController(app, rogue_service, "萨卡兹的无终奇语")

    controller.initial_load()
    app.mainloop()


if __name__ == "__main__":
    main()