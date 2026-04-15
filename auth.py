from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Dict, Optional

import requests

from utils import now_utc


@dataclass
class AuthSession:
    token: str
    token_type: str
    expires_in: int
    username: str
    email: str
    user_id: str
    token_created_at: datetime


class AuthClient:
    def __init__(
        self,
        base_url: str,
        login_endpoint: str,
        email: str,
        password: str,
        timeout: int = 30,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.login_endpoint = login_endpoint
        self.email = email
        self.password = password
        self.timeout = timeout
        self.session: Optional[AuthSession] = None

    def login(self) -> AuthSession:
        url = f"{self.base_url}{self.login_endpoint}"
        payload = {
            "email": self.email,
            "password": self.password,
        }

        response = requests.post(url, json=payload, timeout=self.timeout)
        response.raise_for_status()

        data = response.json()

        token = data["token"]
        token_type = data.get("tokenType", "Bearer")
        expires_in = data.get("expiresIn", 0)
        username = data.get("username", "")
        email = data.get("email", "")
        user_id = data.get("userId", "")

        self.session = AuthSession(
            token=token,
            token_type=token_type,
            expires_in=expires_in,
            username=username,
            email=email,
            user_id=user_id,
            token_created_at=now_utc(),
        )
        return self.session

    def get_auth_header(self) -> Dict[str, str]:
        if not self.session:
            raise RuntimeError("No active auth session. Call login() first.")
        return {"Authorization": f"{self.session.token_type} {self.session.token}"}

    def get_user_id(self) -> str:
        if not self.session:
            raise RuntimeError("No active auth session. Call login() first.")
        return self.session.user_id