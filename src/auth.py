import requests
import logging
from typing import Optional, Tuple
from src.config import ENDPOINTS, APP_CODE, USER_AGENT


class SklandAuthenticator:
    def __init__(self, hypergryph_token: str):
        if not hypergryph_token:
            raise ValueError("Hypergryph token is required.")
        self.hypergryph_token = hypergryph_token
        self.session = requests.Session()
        self.session.headers.update({"User-Agent": USER_AGENT})

    def authenticate(self) -> Tuple[Optional[str], Optional[str]]:
        logging.info("Starting authentication process...")
        oauth_code = self._get_oauth_code()
        if not oauth_code:
            return None, None

        cred, token = self._get_cred_and_token(oauth_code)
        if not cred or not token:
            return None, None

        logging.info("Authentication successful.")
        return cred, token

    def _get_oauth_code(self) -> Optional[str]:
        logging.info("Step 1: Fetching OAuth2 code...")
        payload = {"token": self.hypergryph_token, "appCode": APP_CODE, "type": 0}
        try:
            response = self.session.post(ENDPOINTS["GRANT"], json=payload, timeout=10)
            response.raise_for_status()
            data = response.json()
            if data.get("status") == 0 and data.get("data", {}).get("code"):
                return data["data"]["code"]
            logging.error(f"Failed to get OAuth2 code: {data.get('msg', 'Unknown error')}")
            return None
        except requests.RequestException as e:
            logging.error(f"Error fetching OAuth2 code: {e}")
            return None

    def _get_cred_and_token(self, code: str) -> Tuple[Optional[str], Optional[str]]:
        logging.info("Step 2: Fetching Skland cred and token...")
        payload = {"kind": 1, "code": code}
        try:
            response = self.session.post(ENDPOINTS["CRED_AUTH"], json=payload, timeout=10)
            response.raise_for_status()
            data = response.json()
            if data.get("code") == 0:
                cred = data.get("data", {}).get("cred")
                token = data.get("data", {}).get("token")
                if cred and token:
                    return cred, token
            logging.error(f"Failed to get cred/token: {data.get('message', 'Unknown error')}")
            return None, None
        except requests.RequestException as e:
            logging.error(f"Error fetching cred/token: {e}")
            return None, None
