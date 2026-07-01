from __future__ import annotations

import csv
from datetime import datetime
from decimal import Decimal
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.db.session import SessionLocal
from app.models.order import Order, OrderItem
from app.services.order_service import OrderService

CSV_PATH = ROOT / "scripts" / "legacy_orders_template.csv"
PINCODE_PATTERN = re.compile(r"(?<!\d)(\d{6})(?!\d)")


def parse_purchase_datetime(value: str) -> datetime:
    return datetime.strptime(value.strip(), "%d-%m-%Y %H:%M")


def parse_product_blob(product_blob: str, amount: Decimal, count: int) -> OrderItem:
    normalized = " ".join(product_blob.split())
    prefix, quantity_blob = normalized.rsplit(" x ", 1)
    quantity = int(quantity_blob)
    name, flavour = prefix.split("(", 1)
    flavour = flavour.rstrip(")").strip()
    unit_price = float(amount / max(1, quantity))
    return OrderItem(
        product_name=name.strip(),
        flavour=flavour,
        variant_label="Legacy",
        mrp=unit_price,
        unit_price=unit_price,
        quantity=max(quantity, count, 1),
        line_total=float(amount),
    )


def extract_pincode_and_address(address: str) -> tuple[str, str]:
    normalized = " ".join(address.split())
    matches = PINCODE_PATTERN.findall(normalized)
    pincode = matches[-1] if matches else ""
    if not pincode:
        return "", normalized

    cleaned = normalized
    cleaned = cleaned.replace(f"- {pincode}", "").replace(f"{pincode} -", "")
    cleaned = re.sub(rf"(?<!\d){re.escape(pincode)}(?!\d)", "", cleaned)
    cleaned = re.sub(r"\s*-\s*$", "", cleaned)
    cleaned = re.sub(r"\s{2,}", " ", cleaned).strip(" ,.-")
    return pincode, cleaned


def main() -> None:
    with CSV_PATH.open(newline="", encoding="utf-8-sig") as handle:
        reader = csv.DictReader(handle)
        rows = list(reader)

    with SessionLocal() as session:
        session.query(OrderItem).delete()
        session.query(Order).delete()
        session.commit()

        for index, row in enumerate(rows, start=1):
            amount = Decimal(row["Amount"].strip())
            count = int(row["Product Count"].strip())
            pincode, delivery_address = extract_pincode_and_address(row["Customer Adress"])
            order = Order(
                order_number=OrderService.format_order_number(index),
                status="confirmed",
                payment_status="paid",
                total_amount=float(amount),
                customer_name=row["Customer Name"].strip(),
                email=row["Customer Email Id"].strip(),
                phone_number=row["Customer Phone number"].strip(),
                delivery_address=delivery_address,
                pincode=pincode,
                comments=f"Imported legacy order from serial {row['Serial Number'].strip()}",
                created_at=parse_purchase_datetime(row["Date of Purchase"]),
                items=[
                    parse_product_blob(
                        row["Product Name"].strip(),
                        amount,
                        count,
                    )
                ],
            )
            session.add(order)

        session.commit()


if __name__ == "__main__":
    main()
