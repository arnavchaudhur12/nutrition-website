from __future__ import annotations

import argparse
import csv
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.models.order import Order, OrderItem
from app.repositories.product import ProductRepository
from app.db.session import SessionLocal
from app.services.email_service import EmailService
from app.services.order_service import OrderService

DEFAULT_RECIPIENT = "workwitharnab24@gmail.com"
PRODUCT_PATTERN = re.compile(
    r"^(?P<name>.+?)\s*\((?P<flavour>.+?)\)\s*x\s*(?P<qty>\d+)$",
    re.IGNORECASE,
)
PINCODE_PATTERN = re.compile(r"(?<!\d)(\d{6})(?!\d)")


@dataclass
class LegacyOrderRow:
    serial_number: int
    purchased_at: datetime
    product_name: str
    product_count: int
    amount: Decimal
    customer_name: str
    customer_phone: str
    customer_address: str
    customer_email: str


@dataclass
class VariantPricing:
    weight_label: str
    mrp: float
    selling_price: float


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate and send separate legacy invoices for historical orders."
    )
    parser.add_argument("--csv", required=True, help="Path to CSV file with legacy order rows.")
    parser.add_argument(
        "--recipient",
        default=DEFAULT_RECIPIENT,
        help=f"Recipient email for separate legacy invoices. Default: {DEFAULT_RECIPIENT}",
    )
    parser.add_argument(
        "--invoice-start",
        type=int,
        default=1,
        help="Starting legacy invoice sequence number. Default: 1",
    )
    parser.add_argument(
        "--output-dir",
        default="legacy_invoices",
        help="Directory to write generated PDFs into. Default: legacy_invoices",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=13,
        help="Maximum number of rows to process from the CSV. Default: 13",
    )
    return parser.parse_args()


def parse_purchase_datetime(value: str) -> datetime:
    for pattern in ("%d-%m-%Y %H:%M", "%d-%m-%Y %H:%M:%S", "%d/%m/%Y", "%d-%m-%Y"):
        try:
            return datetime.strptime(value.strip(), pattern)
        except ValueError:
            continue
    raise ValueError(f"Unsupported date format: {value}")


def read_legacy_rows(csv_path: Path, limit: int) -> list[LegacyOrderRow]:
    with csv_path.open(newline="", encoding="utf-8-sig") as handle:
        reader = csv.DictReader(handle)
        rows: list[LegacyOrderRow] = []
        for raw_row in reader:
            rows.append(
                LegacyOrderRow(
                    serial_number=int((raw_row.get("Serial Number") or raw_row.get("serial_number") or "").strip()),
                    purchased_at=parse_purchase_datetime(
                        raw_row.get("Date of Purchase") or raw_row.get("date_of_purchase") or ""
                    ),
                    product_name=(raw_row.get("Product Name") or raw_row.get("product_name") or "").strip(),
                    product_count=int((raw_row.get("Product Count") or raw_row.get("product_count") or "1").strip()),
                    amount=Decimal((raw_row.get("Amount") or raw_row.get("amount") or "0").strip()),
                    customer_name=(raw_row.get("Customer Name") or raw_row.get("customer_name") or "").strip(),
                    customer_phone=(
                        raw_row.get("Customer Phone number")
                        or raw_row.get("customer_phone_number")
                        or ""
                    ).strip(),
                    customer_address=(
                        raw_row.get("Customer Adress")
                        or raw_row.get("Customer Address")
                        or raw_row.get("customer_address")
                        or ""
                    ).strip(),
                    customer_email=(
                        raw_row.get("Customer Email Id") or raw_row.get("customer_email_id") or ""
                    ).strip(),
                )
            )
            if len(rows) >= limit:
                break
    return rows


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


def load_variant_pricing() -> dict[str, list[VariantPricing]]:
    with SessionLocal() as session:
        products = ProductRepository(session).list_products()

    pricing: dict[str, list[VariantPricing]] = {}
    for product in products:
        pricing[product.flavour.strip().lower()] = [
            VariantPricing(
                weight_label=variant.weight_label,
                mrp=float(variant.mrp),
                selling_price=float(variant.selling_price),
            )
            for variant in product.variants
        ]
    return pricing


def resolve_variant(flavour: str, unit_price: float, pricing_map: dict[str, list[VariantPricing]]) -> VariantPricing:
    variants = pricing_map.get(flavour.strip().lower(), [])
    if not variants:
        return VariantPricing(weight_label="Legacy", mrp=unit_price, selling_price=unit_price)

    return min(
        variants,
        key=lambda variant: (
            abs(variant.selling_price - unit_price),
            abs(variant.mrp - unit_price),
        ),
    )


def build_order_item(
    product_blob: str,
    product_count: int,
    amount: Decimal,
    pricing_map: dict[str, list[VariantPricing]],
) -> OrderItem:
    match = PRODUCT_PATTERN.match(" ".join(product_blob.split()))
    if match:
        name = match.group("name").strip()
        flavour = match.group("flavour").strip()
        quantity = int(match.group("qty"))
    else:
        name = "Peanut Butter"
        flavour = product_blob.strip()
        quantity = product_count

    quantity = max(1, quantity)
    unit_price = float(amount / quantity)
    variant = resolve_variant(flavour, unit_price, pricing_map)
    return OrderItem(
        product_name=name,
        flavour=flavour,
        variant_label=variant.weight_label,
        mrp=variant.mrp,
        unit_price=unit_price,
        quantity=quantity,
        line_total=float(amount),
    )


def build_order(
    row: LegacyOrderRow,
    invoice_number: str,
    pricing_map: dict[str, list[VariantPricing]],
) -> Order:
    item = build_order_item(row.product_name, row.product_count, row.amount, pricing_map)
    pincode, delivery_address = extract_pincode_and_address(row.customer_address)
    return Order(
        order_number=invoice_number,
        status="confirmed",
        payment_status="paid",
        total_amount=float(row.amount),
        customer_name=row.customer_name,
        email=row.customer_email or DEFAULT_RECIPIENT,
        phone_number=row.customer_phone,
        delivery_address=delivery_address,
        pincode=pincode,
        comments=f"Legacy invoice generated from serial number {row.serial_number}",
        created_at=row.purchased_at,
        items=[item],
    )


def main() -> None:
    args = parse_args()
    csv_path = Path(args.csv).expanduser().resolve()
    output_dir = (ROOT / args.output_dir).resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    rows = read_legacy_rows(csv_path, args.limit)
    if not rows:
        raise RuntimeError("No legacy rows found in the CSV file.")

    email_service = EmailService()
    pricing_map = load_variant_pricing()
    for index, row in enumerate(rows, start=args.invoice_start):
        invoice_number = f"LN-{index:06d}"
        order = build_order(row, invoice_number, pricing_map)
        attachment = OrderService.build_invoice_attachment(order, invoice_number)
        pdf_path = output_dir / attachment[0]
        pdf_path.write_bytes(attachment[1])

        subject = f"Legacy invoice {invoice_number} for {row.customer_name}"
        body = OrderService.build_invoice_email_body(order, invoice_number)
        email_service.send_to_explicit_recipients(
            recipients=[args.recipient],
            subject=subject,
            html_body=body,
            attachments=[attachment],
        )
        print(f"Generated {invoice_number} -> {pdf_path}")


if __name__ == "__main__":
    main()
