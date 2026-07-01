from __future__ import annotations

import argparse
import sqlite3
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Renumber stored orders sequentially and rename matching invoice PDFs."
    )
    parser.add_argument(
        "--db-path",
        default="lagads_nutrition.db",
        help="SQLite database path relative to the backend directory.",
    )
    parser.add_argument(
        "--pdf-dir",
        default="legacy_invoices",
        help="Directory containing invoice PDFs to rename when filenames match old order numbers.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview the renumbering plan without changing the database or files.",
    )
    return parser.parse_args()


def format_order_number(sequence: int) -> str:
    return f"LN-{sequence:02d}"


def format_non_final_order_number(order_id: int, payment_status: str, status: str) -> str:
    prefix = "FAILED" if payment_status == "failed" or status == "payment_failed" else "PENDING"
    return f"{prefix}-{order_id:06d}"


def main() -> None:
    args = parse_args()
    db_path = (ROOT / args.db_path).resolve()
    pdf_dir = (ROOT / args.pdf_dir).resolve()

    with sqlite3.connect(db_path) as connection:
        rows = connection.execute(
            """
            SELECT id, order_number, payment_status, status
            FROM orders
            ORDER BY datetime(created_at) ASC, id ASC
            """
        ).fetchall()

        if not rows:
            print("No orders found.")
            return

        renames: list[tuple[int, str, str]] = []
        successful_index = 0
        for order_id, order_number, payment_status, status in rows:
            is_successful = payment_status == "paid" and status != "cancelled"
            if is_successful:
                successful_index += 1
                new_order_number = format_order_number(successful_index)
            else:
                new_order_number = format_non_final_order_number(
                    int(order_id),
                    str(payment_status or ""),
                    str(status or ""),
                )
            if order_number != new_order_number:
                renames.append((int(order_id), str(order_number), new_order_number))

        if not renames:
            print("Order numbers are already sequential.")
            return

        for _, old_order_number, new_order_number in renames:
            print(f"{old_order_number} -> {new_order_number}")

        if args.dry_run:
            print("Dry run complete. No changes applied.")
            return

        for order_id, _, new_order_number in renames:
            connection.execute(
                "UPDATE orders SET order_number = ? WHERE id = ?",
                (f"TEMP-{new_order_number}", order_id),
            )
        connection.commit()

        old_to_new = {old: new for _, old, new in renames}
        for order_id, old_order_number, new_order_number in renames:
            connection.execute(
                "UPDATE orders SET order_number = ? WHERE id = ?",
                (new_order_number, order_id),
            )
            rename_invoice_pdfs(pdf_dir, old_order_number, new_order_number)
        connection.commit()

    print(f"Updated {len(old_to_new)} orders.")


def rename_invoice_pdfs(pdf_dir: Path, old_order_number: str, new_order_number: str) -> None:
    if not pdf_dir.exists():
        return

    candidate_names = [
        f"{old_order_number}.pdf",
        f"invoice-{old_order_number}.pdf",
    ]

    for candidate_name in candidate_names:
        source = pdf_dir / candidate_name
        if not source.exists():
            continue

        target = pdf_dir / f"{new_order_number}.pdf"
        source.rename(target)
        print(f"Renamed PDF {source.name} -> {target.name}")
        return


if __name__ == "__main__":
    main()
