from __future__ import annotations

import logging
from typing import Any

import gspread
from google.oauth2.service_account import Credentials

from app.core.config import get_settings
from app.db.session import SessionLocal
from app.repositories.order import OrderRepository

logger = logging.getLogger(__name__)

SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]
HEADERS = [
    "Serial Number",
    "Date of Purchase",
    "Product Name",
    "Product Count",
    "Amount",
    "Customer Name",
    "Customer Phone number",
    "Customer Adress",
    "Customer Email Id",
    "Order ID",
]


class GoogleSheetService:
    def __init__(self) -> None:
        self.settings = get_settings()

    @staticmethod
    def is_successful_order(order: Any) -> bool:
        return order.payment_status == "paid" and order.status != "cancelled"

    def is_configured(self) -> bool:
        return bool(self.settings.google_sheet_id and self.settings.google_service_account_file)

    def build_successful_order_rows(self) -> list[list[str]]:
        with SessionLocal() as session:
            orders = OrderRepository(session).list_orders()

        rows: list[list[str]] = [HEADERS]
        serial = 1
        for order in reversed(orders):
            if not self.is_successful_order(order):
                continue

            product_names = ", ".join(
                f"{item.product_name} ({item.flavour}) x {item.quantity}" for item in order.items
            )
            product_count = str(sum(item.quantity for item in order.items))
            address = order.delivery_address
            if getattr(order, "pincode", ""):
                address = f"{address} - {order.pincode}"

            rows.append(
                [
                    str(serial),
                    order.created_at.strftime("%d-%m-%Y %H:%M"),
                    product_names,
                    product_count,
                    f"{float(order.total_amount):.2f}",
                    order.customer_name,
                    order.phone_number,
                    address,
                    order.email,
                    order.order_number,
                ]
            )
            serial += 1

        return rows

    def sync_successful_orders_snapshot(self) -> None:
        if not self.settings.google_sheet_id:
            raise RuntimeError("GOOGLE_SHEET_ID is not configured.")
        if not self.settings.google_service_account_file:
            raise RuntimeError("GOOGLE_SERVICE_ACCOUNT_FILE is not configured.")

        credentials = Credentials.from_service_account_file(
            self.settings.google_service_account_file,
            scopes=SCOPES,
        )
        client = gspread.authorize(credentials)
        workbook = client.open_by_key(self.settings.google_sheet_id)
        worksheet = (
            workbook.worksheet(self.settings.google_sheet_worksheet)
            if self.settings.google_sheet_worksheet
            else workbook.get_worksheet(0)
        )
        rows = self.build_successful_order_rows()
        worksheet.clear()
        worksheet.update("A1", rows)

    def sync_successful_orders_snapshot_best_effort(self) -> None:
        if not self.is_configured():
            logger.warning(
                "Google Sheet sync skipped because GOOGLE_SHEET_ID or "
                "GOOGLE_SERVICE_ACCOUNT_FILE is not configured."
            )
            return

        try:
            self.sync_successful_orders_snapshot()
        except Exception:
            logger.exception("Failed to sync successful orders to Google Sheet.")
