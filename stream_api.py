from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple

import requests


class StreamApiClient:
    def __init__(self, base_url: str, endpoints: Dict[str, str], timeout: int = 30) -> None:
        self.base_url = base_url.rstrip("/")
        self.endpoints = endpoints
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

    def search_missions(self, headers: Dict[str, str], keyword: str) -> requests.Response:
        return self._request(
            "GET",
            self.endpoints["missions_search"],
            headers=headers,
            params={"keyword": keyword},
        )

    def list_devices(self, headers: Dict[str, str], site_id: str, company_id: str) -> requests.Response:
        return self._request(
            "GET",
            self.endpoints["devices_list"],
            headers=headers,
            params={"siteId": site_id, "companyId": company_id},
        )

    def start_stream(self, headers: Dict[str, str], payload: Dict[str, Any]) -> requests.Response:
        return self._request("POST", self.endpoints["stream_start"], headers=headers, json_body=payload)

    def stop_stream(self, headers: Dict[str, str], payload: Dict[str, Any]) -> requests.Response:
        return self._request("POST", self.endpoints["stream_stop"], headers=headers, json_body=payload)

    def get_streams(self, headers: Dict[str, str]) -> requests.Response:
        return self._request("GET", self.endpoints["stream_list"], headers=headers)

    @staticmethod
    def _ensure_list(data: Any) -> List[Dict[str, Any]]:
        if isinstance(data, list):
            return [item for item in data if isinstance(item, dict)]
        if isinstance(data, dict):
            if isinstance(data.get("data"), list):
                return [item for item in data["data"] if isinstance(item, dict)]
            if isinstance(data.get("items"), list):
                return [item for item in data["items"] if isinstance(item, dict)]
            return [data] if isinstance(data, dict) else []
        return []

    def resolve_mission_context(
        self,
        headers: Dict[str, str],
        mission_name: str,
        company_name: str | None = None,
        site_name: str | None = None,
    ) -> Dict[str, Any]:
        response = self.search_missions(headers, mission_name)
        response.raise_for_status()

        items = self._ensure_list(response.json())

        matched = [
            item
            for item in items
            if str(item.get("missionName", "")).strip().lower() == mission_name.strip().lower()
        ]

        if not matched:
            raise ValueError(f"Mission not found for name: {mission_name}")

        if company_name:
            matched = [
                item
                for item in matched
                if str(item.get("companyName", "")).strip().lower() == company_name.strip().lower()
            ]

        if site_name:
            matched = [
                item
                for item in matched
                if str(item.get("siteName", "")).strip().lower() == site_name.strip().lower()
            ]

        if not matched:
            raise ValueError(
                f"Mission found by name but not matching company/site. "
                f"mission={mission_name}, company={company_name}, site={site_name}"
            )

        if len(matched) > 1:
            raise ValueError(
                f"Multiple missions found even after filtering. "
                f"mission={mission_name}, company={company_name}, site={site_name}"
            )

        item = matched[0]

        return {
            "mission_id": item["missionId"],
            "site_id": item["siteId"],
            "company_id": item["companyId"],
            "mission_name": item["missionName"],
            "site_name": item.get("siteName", ""),
            "company_name": item.get("companyName", ""),
            "device_type": item.get("deviceType", ""),
        }

    def resolve_device_context(
        self,
        headers: Dict[str, str],
        site_id: str,
        company_id: str,
        device_name: str,
    ) -> Dict[str, Any]:
        response = self.list_devices(headers, site_id=site_id, company_id=company_id)
        response.raise_for_status()

        items = self._ensure_list(response.json())

        for item in items:
            if str(item.get("deviceName", "")).strip().lower() == device_name.strip().lower():
                sub_device = item.get("subDeviceInfo") or {}
                return {
                    "device_id": item["deviceId"],
                    "device_name": item["deviceName"],
                    "device_type": item.get("deviceType", ""),
                    "device_status": item.get("status", ""),
                    "device_sn": item.get("deviceSn", ""),
                    "sub_device_sn": sub_device.get("sn", ""),
                    "sub_device_id": sub_device.get("subDeviceId", ""),
                }

        available_names = [item.get("deviceName", "") for item in items]

        raise ValueError(
            f"Device not found for name: {device_name} "
            f"under site_id={site_id}, company_id={company_id}. "
            f"Available devices: {available_names}"
        )

    def is_device_stream_active(self, headers: Dict[str, str], device_id: str) -> Tuple[bool, str, Optional[int]]:
        response = self.get_streams(headers)
        status_code = response.status_code
        response.raise_for_status()

        items = self._ensure_list(response.json())

        for item in items:
            current_device_id = item.get("deviceId") or item.get("robotId") or item.get("id")
            status_value = str(
                item.get("status")
                or item.get("streamStatus")
                or item.get("state")
                or ""
            ).lower()

            if current_device_id == device_id:
                is_active = status_value in {"active", "started", "running", "live", "streaming"}
                return is_active, f"Matched device {device_id} with status={status_value}", status_code

        return False, f"No active stream found for device {device_id}", status_code