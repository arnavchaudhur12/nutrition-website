from __future__ import annotations

from pathlib import Path
import sys

import gspread
from google.oauth2.service_account import Credentials

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.core.config import get_settings
from app.db.session import SessionLocal
from app.repositories.order import OrderRepository

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
]


def is_successful_order(order) -> bool:
    return order.payment_status == "paid" and order.status != "cancelled"


def build_rows() -> list[list[str]]:
    with SessionLocal() as session:
        orders = OrderRepository(session).list_orders()

    rows: list[list[str]] = [HEADERS]
    serial = 1
    for order in reversed(orders):
        if not is_successful_order(order):
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
            ]
        )
        serial += 1
    return rows


def main() -> None:
    settings = get_settings()
    if not settings.google_sheet_id:
        raise RuntimeError("GOOGLE_SHEET_ID is not configured.")
    if not settings.google_service_account_file:
        raise RuntimeError("GOOGLE_SERVICE_ACCOUNT_FILE is not configured.")

    credentials = Credentials.from_service_account_file(
        settings.google_service_account_file,
        scopes=SCOPES,
    )
    client = gspread.authorize(credentials)
    workbook = client.open_by_key(settings.google_sheet_id)
    worksheet = (
        workbook.worksheet(settings.google_sheet_worksheet)
        if settings.google_sheet_worksheet
        else workbook.get_worksheet(0)
    )
    rows = build_rows()
    worksheet.clear()
    worksheet.update("A1", rows)


if __name__ == "__main__":
    main()
