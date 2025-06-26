import requests
import json
import time
import hashlib
import hmac
import logging
from typing import Optional, Dict, Any
from urllib.parse import urlparse, urlencode

BINDING_URL = "https://zonai.skland.com/api/v1/game/player/binding"
PLAYER_INFO_URL = "https://zonai.skland.com/api/v1/game/player/info"
V_NAME = "1.21.0"

class PlayerClient:
    def __init__(self, session: requests.Session, cred: str, token: str):
        self.session = session
        self.cred = cred
        self.token = token # Signing key
        self.uid = self._get_game_uid()
        if self.uid:
            self.is_ready = True
        else:
            self.is_ready = False

    def _generate_signature_headers(self, url: str, body: Optional[Dict] = None) -> Dict[str, str]:
        parsed_url = urlparse(url)
        path = parsed_url.path
        query = urlencode(dict(item.split('=') for item in parsed_url.query.split('&'))) if parsed_url.query else ""
        timestamp = str(int(time.time()))
        header_for_sign = {"platform": "1", "timestamp": timestamp, "dId": "", "vName": V_NAME}
        header_for_sign_str = json.dumps(header_for_sign, separators=(',', ':'))
        body_str = json.dumps(body, separators=(',', ':')) if body else ""
        s = f"{path}{query}{body_str}{timestamp}{header_for_sign_str}"
        hex_s = hmac.new(self.token.encode('utf-8'), s.encode('utf-8'), hashlib.sha256).hexdigest()
        sign = hashlib.md5(hex_s.encode('utf-8')).hexdigest()
        return {"cred": self.cred, "sign": sign, "timestamp": timestamp, "platform": "1", "dId": "", "vName": V_NAME}

    def _get_game_uid(self) -> Optional[str]:
        logging.info("Step 3: Fetching game account UID...")
        try:
            headers = self._generate_signature_headers(url=BINDING_URL)
            response = self.session.get(BINDING_URL, headers=headers, timeout=10)
            response.raise_for_status()
            data = response.json()
            if data.get("code") == 0:
                for game in data.get("data", {}).get("list", []):
                    if game.get("appCode") == "arknights":
                        binding_list = game.get("bindingList", [])
                        if binding_list:
                            uid = binding_list[0].get("uid")
                            logging.info(f"Found Arknights UID: {uid}")
                            return uid
            logging.error(f"Failed to get binding list: {data.get('message', 'Unknown error')}")
            return None
        except requests.RequestException as e:
            logging.error(f"Error fetching binding list: {e}")
            return None

    def get_player_info(self) -> Optional[Dict[str, Any]]:
        if not self.is_ready:
            logging.error("PlayerClient is not ready. UID not found.")
            return None
        url = f"{PLAYER_INFO_URL}?uid={self.uid}"
        logging.info(f"Requesting player info for UID: {self.uid}")
        try:
            headers = self._generate_signature_headers(url=url)
            response = self.session.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            data = response.json()
            if data.get("code") == 0:
                logging.info("Successfully fetched player info.")
                return data.get("data")
            logging.error(f"API Error on get_player_info: {data.get('message', 'Unknown API error')}")
            return None
        except requests.RequestException as e:
            logging.error(f"An error occurred during get_player_info request: {e}")
        return None
