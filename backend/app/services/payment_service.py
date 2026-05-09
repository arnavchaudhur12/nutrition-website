from typing import Union
from uuid import uuid4

from app.core.config import get_settings


class PaymentService:
    def __init__(self) -> None:
        self.settings = get_settings()

    def create_checkout_reference(
        self, amount: float, order_number: str
    ) -> dict[str, Union[str, float]]:
        # This method is intentionally provider-agnostic until live gateway credentials are supplied.
        return {
            "provider": self.settings.payment_provider,
            "order_number": order_number,
            "gateway_reference": f"{self.settings.payment_provider}_{uuid4().hex[:14]}",
            "amount": amount,
            "status": "created",
        }
