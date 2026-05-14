import hmac
from hashlib import sha256
from typing import Union
from uuid import uuid4

import razorpay
from fastapi import HTTPException, status
from razorpay.errors import BadRequestError, GatewayError, ServerError
from requests import RequestException

from app.core.config import get_settings


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
