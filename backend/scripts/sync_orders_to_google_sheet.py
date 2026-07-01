from __future__ import annotations

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.services.google_sheet_service import GoogleSheetService


def main() -> None:
    GoogleSheetService().sync_successful_orders_snapshot()


if __name__ == "__main__":
    main()
