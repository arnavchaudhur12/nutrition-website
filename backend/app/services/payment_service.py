import hmac
import logging
from hashlib import sha256
from typing import Any, Optional, Union
from uuid import uuid4

import razorpay
from fastapi import HTTPException, status
from razorpay.errors import BadRequestError, GatewayError, ServerError
from requests import RequestException

from app.core.config import get_settings

logger = logging.getLogger(__name__)


class PaymentService:
    def __init__(self) -> None:
        self.settings = get_settings()
        self.key_id = self.settings.razorpay_key_id or self.settings.payment_key_id
        self.key_secret = self.settings.razorpay_key_secret or self.settings.payment_key_secret

    def create_checkout_reference(
        self, amount: float, order_number: str
    ) -> dict[str, Union[str, float]]:
        return {
            "provider": self.settings.payment_provider,
            "order_number": order_number,
            "gateway_reference": f"{self.settings.payment_provider}_{uuid4().hex[:14]}",
            "amount": amount,
            "status": "created",
        }

    def create_razorpay_order(
        self, amount_paise: int, currency: str, receipt: str
    ) -> dict[str, Union[str, int]]:
        if amount_paise < 100:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Minimum payment amount is 100 paise.",
            )

        if not self.key_id or not self.key_secret:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Razorpay credentials are not configured.",
            )

        client = razorpay.Client(auth=(self.key_id, self.key_secret))

        try:
            order = client.order.create(
                {
                    "amount": amount_paise,
                    "currency": currency.upper(),
                    "receipt": receipt[:40],
                    "payment_capture": 1,
                }
            )
        except BadRequestError as error:
            error_message = str(error)
            if "authentication failed" in error_message.lower():
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Razorpay authentication failed. Check KEY_ID and KEY_SECRET on the server.",
                ) from error
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=error_message,
            ) from error
        except (GatewayError, ServerError) as error:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Unable to create Razorpay order.",
            ) from error
        except RequestException as error:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Unable to reach Razorpay.",
            ) from error
        except Exception as error:
            error_message = str(error)
            if "authentication failed" in error_message.lower():
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Razorpay authentication failed. Check KEY_ID and KEY_SECRET on the server.",
                ) from error
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Unexpected error while creating Razorpay order.",
            ) from error

        return {
            "order_id": str(order["id"]),
            "amount": int(order["amount"]),
            "currency": str(order["currency"]),
            "receipt": str(order.get("receipt") or receipt),
        }

    def verify_razorpay_signature(
        self, order_id: str, payment_id: str, signature: str
    ) -> bool:
        if not self.key_secret:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Razorpay credentials are not configured.",
            )

        message = f"{order_id}|{payment_id}".encode("utf-8")
        generated_signature = hmac.new(
            self.key_secret.encode("utf-8"),
            message,
            sha256,
        ).hexdigest()
        return hmac.compare_digest(generated_signature, signature)

    def verify_razorpay_webhook_signature(self, payload_body: bytes, signature: str) -> bool:
        webhook_secret = self.settings.payment_webhook_secret
        if not webhook_secret:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Razorpay webhook secret is not configured.",
            )

        generated_signature = hmac.new(
            webhook_secret.encode("utf-8"),
            payload_body,
            sha256,
        ).hexdigest()
        return hmac.compare_digest(generated_signature, signature)

    def get_captured_payment_id_for_order(self, razorpay_order_id: str) -> Optional[str]:
        if not self.key_id or not self.key_secret:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Razorpay credentials are not configured.",
            )

        client = razorpay.Client(auth=(self.key_id, self.key_secret))

        try:
            response: Any = client.order.payments(razorpay_order_id)
        except BadRequestError as error:
            logger.warning(
                "Razorpay reconciliation lookup failed for order_id=%s detail=%s",
                razorpay_order_id,
                str(error),
            )
            return None
        except (GatewayError, ServerError, RequestException):
            logger.exception(
                "Razorpay reconciliation lookup failed for order_id=%s",
                razorpay_order_id,
            )
            return None
        except Exception:
            logger.exception(
                "Unexpected Razorpay reconciliation error for order_id=%s",
                razorpay_order_id,
            )
            return None

        payments = self._extract_payment_items(response)
        for payment in payments:
            status_value = str(payment.get("status") or "").strip().lower()
            if status_value == "captured":
                payment_id = str(payment.get("id") or "").strip()
                if payment_id:
                    return payment_id
        return None

    @staticmethod
    def _extract_payment_items(response: Any) -> list[dict[str, Any]]:
        if isinstance(response, dict):
            items = response.get("items")
            if isinstance(items, list):
                return [item for item in items if isinstance(item, dict)]
        if isinstance(response, list):
            return [item for item in response if isinstance(item, dict)]
        return []
