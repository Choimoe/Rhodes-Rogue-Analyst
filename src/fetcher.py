# -*- coding: utf-8 -*-
import os
import requests
import json
import time
import hashlib
import hmac
from typing import Dict, Any, Optional, Tuple
from dotenv import load_dotenv
import logging
from pathlib import Path
from urllib.parse import urlparse, urlencode

# --- Configuration ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# --- Constants ---
GRANT_URL = "https://as.hypergryph.com/user/oauth2/v2/grant"
CRED_URL = "https://zonai.skland.com/api/v1/user/auth/generate_cred_by_code"
BINDING_URL = "https://zonai.skland.com/api/v1/game/player/binding"
PLAYER_INFO_URL = "https://zonai.skland.com/api/v1/game/player/info"
APP_CODE = "4ca99fa6b56cc2ba"
V_NAME = "1.21.0"  # App version from the shell script


def load_hypergryph_token() -> Optional[str]:
    """
    Loads the Hypergryph token from a .env file located in the project root.
    """
    project_root = Path(__file__).parent.parent
    dotenv_path = project_root / '.env'
    if dotenv_path.exists():
        load_dotenv(dotenv_path=dotenv_path)
    else:
        load_dotenv()
    token = os.getenv("HYPERGRYPH_TOKEN")
    if not token:
        logging.error("HYPERGRYPH_TOKEN not found in environment variables.")
        logging.info("Please ensure a .env file exists with your token.")
        logging.info('Example: HYPERGRYPH_TOKEN="your_token_here"')
        return None
    return token


class SklandAPIClient:
    """
    A client for the Skland API, handling the full authentication flow including
    request signing.
    """

    def __init__(self, hypergryph_token: str):
        if not hypergryph_token or not isinstance(hypergryph_token, str):
            raise ValueError("Invalid 'hypergryph_token' provided.")
        self.hypergryph_token = hypergryph_token
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": f"Skland/{V_NAME} (com.hypergryph.skland; build:102100065; Android 34; ) Okhttp/4.11.0",
            "Accept-Encoding": "gzip",
            "Connection": "close",
        })
        self.cred = None
        self.token = None  # This will be the signing key
        self.uid = None
        self.is_authenticated = False
        self.authenticate()

    def _generate_signature_headers(self, url: str, body: Optional[Dict] = None) -> Dict[str, str]:
        """
        Generates the required signature headers for authenticated requests.
        This logic is ported from the provided attendance.sh script.
        """
        parsed_url = urlparse(url)
        path = parsed_url.path
        query = urlencode(dict(item.split('=') for item in parsed_url.query.split('&'))) if parsed_url.query else ""

        timestamp = str(int(time.time()))

        # Prepare header object for signing payload
        header_for_sign = {
            "platform": "1",
            "timestamp": timestamp,
            "dId": "",
            "vName": V_NAME
        }
        header_for_sign_str = json.dumps(header_for_sign, separators=(',', ':'))

        body_str = json.dumps(body, separators=(',', ':')) if body else ""

        # String to sign
        s = f"{path}{query}{body_str}{timestamp}{header_for_sign_str}"

        # Signing process
        hex_s = hmac.new(self.token.encode('utf-8'), s.encode('utf-8'), hashlib.sha256).hexdigest()
        sign = hashlib.md5(hex_s.encode('utf-8')).hexdigest()

        headers = {
            "cred": self.cred,
            "sign": sign,
            "timestamp": timestamp,
            "platform": "1",
            "dId": "",
            "vName": V_NAME
        }
        return headers

    def authenticate(self):
        """Performs the full authentication flow to get cred, signing token, and game UID."""
        logging.info("Starting authentication process...")
        oauth_code = self._get_oauth_code()
        if not oauth_code: return

        cred, token = self._get_cred_and_token(oauth_code)
        if not cred or not token: return
        self.cred = cred
        self.token = token

        uid = self._get_game_uid()
        if not uid: return
        self.uid = uid

        self.is_authenticated = True
        logging.info("Authentication successful.")

    def _get_oauth_code(self) -> Optional[str]:
        """Step 1: Get OAuth2 grant code."""
        logging.info("Step 1: Fetching OAuth2 code...")
        payload = {"token": self.hypergryph_token, "appCode": APP_CODE, "type": 0}
        try:
            response = self.session.post(GRANT_URL, json=payload, timeout=10)
            response.raise_for_status()
            data = response.json()
            if data.get("status") == 0 and data.get("data", {}).get("code"):
                logging.info("Successfully fetched OAuth2 code.")
                return data["data"]["code"]
            logging.error(f"Failed to get OAuth2 code: {data.get('msg', 'Unknown error')}")
            return None
        except requests.RequestException as e:
            logging.error(f"Error fetching OAuth2 code: {e}")
            return None

    def _get_cred_and_token(self, code: str) -> Tuple[Optional[str], Optional[str]]:
        """Step 2: Use OAuth2 code to generate 'cred' and the signing 'token'."""
        logging.info("Step 2: Fetching Skland cred and token...")
        payload = {"kind": 1, "code": code}
        try:
            response = self.session.post(CRED_URL, json=payload, timeout=10)
            response.raise_for_status()
            data = response.json()
            if data.get("code") == 0:
                cred = data.get("data", {}).get("cred")
                token = data.get("data", {}).get("token")
                if cred and token:
                    logging.info("Successfully fetched Skland cred and token.")
                    return cred, token
            logging.error(f"Failed to get cred/token: {data.get('message', 'Unknown error')}")
            return None, None
        except requests.RequestException as e:
            logging.error(f"Error fetching cred/token: {e}")
            return None, None

    def _get_game_uid(self) -> Optional[str]:
        """Step 3: Use the 'cred' and signature to find the bound Arknights UID."""
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
                logging.error("No Arknights account binding found in the response.")
                return None
            logging.error(f"Failed to get binding list: {data.get('message', 'Unknown error')}")
            return None
        except requests.RequestException as e:
            logging.error(f"Error fetching binding list: {e}")
            return None

    def get_player_info(self) -> Optional[Dict[str, Any]]:
        """Fetches the complete player information after successful authentication."""
        if not self.is_authenticated:
            logging.error("Authentication failed. Cannot fetch player info.")
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

    def get_realtime_data(self) -> Optional[Dict[str, Any]]:
        """Fetches and extracts key real-time data points for easy access."""
        player_data = self.get_player_info()
        if not player_data:
            return None
        try:
            status = player_data.get("status", {})
            building = player_data.get("building", {})
            campaign = player_data.get("campaign", {})
            routine = player_data.get("routine", {})
            realtime_info = {
                "理智": {"当前值": status.get("ap", {}).get("current"), "最大值": status.get("ap", {}).get("max"),
                         "完全恢复时间戳": status.get("ap", {}).get("completeRecoveryTime")},
                "剿灭作战": {"本周已获取": campaign.get("reward", {}).get("current"),
                             "本周总计": campaign.get("reward", {}).get("total")},
                "每日任务": {"已完成": routine.get("daily", {}).get("current"),
                             "总计": routine.get("daily", {}).get("total")},
                "每周任务": {"已完成": routine.get("weekly", {}).get("current"),
                             "总计": routine.get("weekly", {}).get("total")},
                "基建": {"无人机": {"当前值": building.get("labor", {}).get("value"),
                                    "最大值": building.get("labor", {}).get("maxValue")},
                         "贸易站": building.get("tradings", []), "制造站": building.get("manufactures", [])}
            }
            return realtime_info
        except Exception as e:
            logging.error(f"Failed to parse real-time data from API response: {e}")
            return None


def main():
    """Main function to demonstrate the usage of the SklandAPIClient."""
    hypergryph_token = load_hypergryph_token()
    if not hypergryph_token:
        return
    try:
        client = SklandAPIClient(hypergryph_token=hypergryph_token)
        if client.is_authenticated:
            realtime_data = client.get_realtime_data()
            if realtime_data:
                logging.info("获取到的实时数据:")
                print(json.dumps(realtime_data, indent=4, ensure_ascii=False))
            else:
                logging.error("无法获取实时数据，请检查日志中的错误信息。")
        else:
            logging.error("客户端认证失败，无法继续。请检查你的 HYPERGRYPH_TOKEN 是否有效。")
    except ValueError as e:
        logging.error(f"Initialization Error: {e}")


if __name__ == "__main__":
    main()
