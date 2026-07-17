import json
from datetime import date
from typing import Any, Optional

import httpx
from fastapi import HTTPException, status

from app.core.config import get_settings


class ShippingService:
    def __init__(self) -> None:
        self.settings = get_settings()
        self.base_url = self.settings.genzlogix_base_url.rstrip("/")
        self.api_key = self.settings.genzlogix_api_key.strip()

    def is_configured(self) -> bool:
        return bool(self.api_key and self.base_url and self.settings.genzlogix_pickup_pincode.strip())

    def create_order(self, payload: dict[str, Any]) -> dict[str, Any]:
        return self._request("POST", "/orders", json_payload=payload)

    def track_shipment(self, awb_number: str) -> dict[str, Any]:
        return self._request("GET", f"/shipments/{awb_number}/track")

    def check_serviceability(self, delivery_pincode: str) -> dict[str, Any]:
        pickup_pincode = self.settings.genzlogix_pickup_pincode.strip()
        if not pickup_pincode:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="GenZLogix pickup pincode is not configured.",
            )
        path = (
            f"/serviceability?pickup_pincode={pickup_pincode}"
            f"&delivery_pincode={delivery_pincode.strip()}"
        )
        return self._request("GET", path)

    def _request(
        self,
        method: str,
        path: str,
        json_payload: Optional[dict[str, Any]] = None,
    ) -> dict[str, Any]:
        if not self.api_key:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="GenZLogix credentials are not configured.",
            )

        headers = {
            "X-API-Key": self.api_key,
            "Content-Type": "application/json",
        }

        try:
            with httpx.Client(timeout=20.0) as client:
                response = client.request(
                    method=method,
                    url=f"{self.base_url}{path}",
                    headers=headers,
                    json=json_payload,
                )
        except httpx.RequestError as error:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail="Unable to reach GenZLogix.",
            ) from error

        body = self._decode_body(response)
        if response.status_code >= 400:
            detail = self._extract_error_message(body) or "GenZLogix request failed."
            raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=detail)

        data = body.get("data")
        if not body.get("success") or not isinstance(data, dict):
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail="Invalid GenZLogix response.",
            )
        return data

    @staticmethod
    def _decode_body(response: httpx.Response) -> dict[str, Any]:
        try:
            body = response.json()
        except ValueError:
            body = {}
        return body if isinstance(body, dict) else {}

    @staticmethod
    def _extract_error_message(body: dict[str, Any]) -> str:
        message = body.get("message")
        if isinstance(message, str) and message.strip():
            return message.strip()
        detail = body.get("detail")
        if isinstance(detail, str) and detail.strip():
            return detail.strip()
        return ""

    @staticmethod
    def serialize_history(history: list[dict[str, Any]]) -> str:
        return json.dumps(history, separators=(",", ":"), ensure_ascii=True)

    @staticmethod
    def deserialize_history(history: Optional[str]) -> list[dict[str, Any]]:
        if not history:
            return []
        try:
            decoded = json.loads(history)
        except json.JSONDecodeError:
            return []
        if not isinstance(decoded, list):
            return []
        return [item for item in decoded if isinstance(item, dict)]

    @staticmethod
    def parse_date(value: Optional[str]) -> Optional[date]:
        if not value:
            return None
        try:
            return date.fromisoformat(value)
        except ValueError:
            return None
