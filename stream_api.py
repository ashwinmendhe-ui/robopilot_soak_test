from __future__ import annotations

from typing import Any, Dict, Optional, Tuple

import requests


class StreamApiClient:
    def __init__(self, base_url: str, timeout: int = 30) -> None:
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout

    def _request(
        self,
        method: str,
        endpoint: str,
        headers: Dict[str, str],
        json_body: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None,
    ) -> requests.Response:
        url = f"{self.base_url}{endpoint}"
        return requests.request(
            method=method,
            url=url,
            headers=headers,
            json=json_body,
            params=params,
            timeout=self.timeout,
        )

    def start_stream(self, headers: Dict[str, str], payload: Dict[str, Any]) -> requests.Response:
        return self._request("POST", "/v1/stream/start", headers=headers, json_body=payload)

    def stop_stream(self, headers: Dict[str, str], payload: Dict[str, Any]) -> requests.Response:
        return self._request("POST", "/v1/stream/stop", headers=headers, json_body=payload)

    def get_streams(self, headers: Dict[str, str]) -> requests.Response:
        return self._request("GET", "/v1/stream", headers=headers)

    def get_stream_metadata(self, headers: Dict[str, str], stream_id: str) -> requests.Response:
        return self._request("GET", f"/v1/stream/{stream_id}/metadata", headers=headers)

    def is_device_stream_active(self, headers: Dict[str, str], device_id: str) -> Tuple[bool, str, Optional[int]]:
        """
        Best-effort generic status checker.
        Assumption: GET /v1/stream returns one stream object or a list containing active streams.
        You may need to adjust this once you confirm the real response shape.
        """
        response = self.get_streams(headers)
        status_code = response.status_code
        response.raise_for_status()

        data = response.json()

        candidates = []
        if isinstance(data, list):
            candidates = data
        elif isinstance(data, dict):
            if isinstance(data.get("data"), list):
                candidates = data["data"]
            elif isinstance(data.get("items"), list):
                candidates = data["items"]

        for stream in candidates:
            if stream.get("device_id") == device_id:
                return True, f"Stream is active for device {device_id}", status_code

        return False, f"No active stream found for device {device_id}", status_code