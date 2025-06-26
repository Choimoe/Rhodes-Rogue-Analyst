import requests
import json
import time
import hmac
import hashlib
import logging
from typing import Optional, Tuple, Dict, Any
from urllib.parse import urlparse, urlencode


class SklandClient:
    def __init__(self, config):
        self.config = config
        self.session = requests.Session()
        self.session.headers.update({"User-Agent": self.config.get("APP", "USER_AGENT")})
        self.cred: Optional[str] = None
        self.token: Optional[str] = None
        self.uid: Optional[str] = None

    def authenticate(self, hypergryph_token: str) -> bool:
        logging.info("Starting authentication...")
        oauth_code = self._get_oauth_code(hypergryph_token)
        if not oauth_code: return False

        cred, token = self._get_cred_and_token(oauth_code)
        if not cred or not token: return False

        self.cred, self.token = cred, token

        uid = self._get_game_uid()
        if not uid: return False

        self.uid = uid
        logging.info("Authentication successful.")
        return True

    def _get_oauth_code(self, token: str) -> Optional[str]:
        payload = {"token": token, "appCode": self.config.get("APP", "APP_CODE"), "type": 0}
        try:
            response = self.session.post(self.config.get("API", "GRANT_URL"), json=payload, timeout=10)
            response.raise_for_status()
            data = response.json()
            if data.get("status") == 0: return data.get("data", {}).get("code")
        except requests.RequestException as e:
            logging.error(f"Error fetching OAuth code: {e}")
        return None

    def _get_cred_and_token(self, code: str) -> Tuple[Optional[str], Optional[str]]:
        payload = {"kind": 1, "code": code}
        try:
            response = self.session.post(self.config.get("API", "CRED_AUTH_URL"), json=payload, timeout=10)
            response.raise_for_status()
            data = response.json()
            if data.get("code") == 0:
                return data.get("data", {}).get("cred"), data.get("data", {}).get("token")
        except requests.RequestException as e:
            logging.error(f"Error fetching cred and token: {e}")
        return None, None

    def _get_game_uid(self) -> Optional[str]:
        headers = self._generate_signature_headers(self.config.get("API", "BINDING_URL"))
        try:
            response = self.session.get(self.config.get("API", "BINDING_URL"), headers=headers, timeout=10)
            response.raise_for_status()
            data = response.json()
            if data.get("code") == 0:
                for game in data.get("data", {}).get("list", []):
                    if game.get("appCode") == "arknights":
                        if binding_list := game.get("bindingList"):
                            return binding_list[0].get("uid")
        except requests.RequestException as e:
            logging.error(f"Error fetching UID: {e}")
        return None

    def _generate_signature_headers(self, url: str, body: Optional[Dict] = None) -> Dict[str, str]:
        parsed_url = urlparse(url)
        path = parsed_url.path
        query = parsed_url.query
        timestamp = str(int(time.time()))

        headers_for_sign = {
            "platform": "1",
            "timestamp": timestamp,
            "dId": "",
            "vName": self.config.get("APP", "V_NAME")
        }
        headers_for_sign_str = json.dumps(headers_for_sign, separators=(',', ':'))
        body_str = json.dumps(body, separators=(',', ':')) if body else ""

        str_to_sign = f"{path}{query}{body_str}{timestamp}{headers_for_sign_str}"

        hex_digest = hmac.new(self.token.encode('utf-8'), str_to_sign.encode('utf-8'), hashlib.sha256).hexdigest()
        sign = hashlib.md5(hex_digest.encode('utf-8')).hexdigest()

        return {"cred": self.cred, "sign": sign, **headers_for_sign}

    def get_rogue_info(self) -> Optional[Dict[str, Any]]:
        if not self.uid: return None
        url = f"{self.config.get('API', 'ROGUE_INFO_URL')}?uid={self.uid}"
        headers = self._generate_signature_headers(url)
        try:
            response = self.session.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            data = response.json()
            if data.get("code") == 0:
                return data.get("data")
        except requests.RequestException as e:
            logging.error(f"Error fetching rogue info: {e}")
        return None