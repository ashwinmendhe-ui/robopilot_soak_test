from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, Optional

import requests

from utils import now_utc


@dataclass
class AuthSession:
    token: str
    token_created_at: datetime


class AuthClient:
    def __init__(self, base_url: str, email: str, password: str, timeout: int = 30) -> None:
        self.base_url = base_url.rstrip("/")
        self.email = email
        self.password = password
        self.timeout = timeout
        self.session: Optional[AuthSession] = None

    def login(self) -> AuthSession:
        url = f"{self.base_url}/v1/auth/login"
        payload = {
            "email": self.email,
            "password": self.password,
        }

        response = requests.post(url, json=payload, timeout=self.timeout)
        response.raise_for_status()

        data: Dict[str, Any] = response.json()

        token = (
            data.get("token")
            or data.get("accessToken")
            or data.get("access_token")
            or data.get("data", {}).get("token")
            or data.get("data", {}).get("accessToken")
            or data.get("data", {}).get("access_token")
        )

        if not token:
            raise ValueError(f"Login succeeded but token not found in response: {data}")

        self.session = AuthSession(token=token, token_created_at=now_utc())
        return self.session

    def get_auth_header(self) -> Dict[str, str]:
        if not self.session:
            raise RuntimeError("No active auth session. Call login() first.")
        return {"Authorization": f"Bearer {self.session.token}"}