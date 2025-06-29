import json
import logging
from ..utils import get_resource_path

class AliasService:
    _aliases = {}

    def __init__(self):
        self._load_aliases()

    def _load_aliases(self):
        config_path = get_resource_path("config/aliases.json")
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                self._aliases = json.load(f)
            logging.info("Alias configuration loaded successfully.")
        except (FileNotFoundError, json.JSONDecodeError) as e:
            logging.warning(f"Could not load or parse aliases.json: {e}. Alias service will be disabled.")
            self._aliases = {}

    def get_squad_alias(self, squad_name: str) -> str:
        return self._aliases.get(squad_name, squad_name)
