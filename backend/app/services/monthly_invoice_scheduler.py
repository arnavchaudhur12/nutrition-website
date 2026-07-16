import asyncio
import json
import logging
from contextlib import suppress
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from typing import Optional
from zoneinfo import ZoneInfo

from app.core.config import BACKEND_ROOT
from app.db.session import SessionLocal
from app.services.email_service import EmailService
from app.services.order_service import OrderService

logger = logging.getLogger(__name__)

MONTHLY_STATEMENT_RECIPIENTS = [
    "jai.lagad@lagadsnutrition.in",
    "workwitharnab24@gmail.com",
]
SCHEDULER_TIMEZONE = ZoneInfo("Asia/Kolkata")
STATE_FILE = BACKEND_ROOT / "monthly_invoice_scheduler_state.json"


@dataclass(frozen=True)
class MonthlyInvoiceWindow:
    run_month: str
    start_date: date
    end_date: date


class MonthlyInvoiceScheduler:
    def __init__(self) -> None:
        self._task: Optional[asyncio.Task[None]] = None

    def start(self) -> None:
        if self._task and not self._task.done():
            return
        self._task = asyncio.create_task(self._run_forever())

    async def stop(self) -> None:
        if not self._task:
            return
        self._task.cancel()
        with suppress(asyncio.CancelledError):
            await self._task
        self._task = None

    async def _run_forever(self) -> None:
        while True:
            await self._run_if_due()
            next_run = self._next_run_time(datetime.now(SCHEDULER_TIMEZONE))
            sleep_seconds = max((next_run - datetime.now(SCHEDULER_TIMEZONE)).total_seconds(), 60.0)
            await asyncio.sleep(sleep_seconds)

    async def _run_if_due(self) -> None:
        now = datetime.now(SCHEDULER_TIMEZONE)
        if now.day != 1:
            return

        target = self._build_window(now.date())
        if self._load_last_sent_month() == target.run_month:
            return

        try:
            await asyncio.to_thread(self._send_monthly_statement, target)
        except Exception:
            logger.exception("Monthly invoice scheduler failed for %s", target.run_month)

    def _send_monthly_statement(self, target: MonthlyInvoiceWindow) -> None:
        with SessionLocal() as db:
            order_service = OrderService(db)
            orders = order_service.list_paid_orders_for_date_range(
                target.start_date,
                target.end_date,
            )
            email_service = EmailService()
            subject = (
                "Monthly invoice statement "
                f"({target.start_date.isoformat()} to {target.end_date.isoformat()})"
            )

            if orders:
                attachment = order_service.build_invoice_statement_attachment(
                    orders,
                    target.start_date,
                    target.end_date,
                )
                body = (
                    "<p>Please find attached the consolidated invoice statement for the last 30 days.</p>"
                    f"<p>Coverage: <strong>{target.start_date.isoformat()}</strong> to "
                    f"<strong>{target.end_date.isoformat()}</strong>.</p>"
                )
                email_service.send_to_explicit_recipients(
                    MONTHLY_STATEMENT_RECIPIENTS,
                    subject,
                    body,
                    attachments=[attachment],
                )
            else:
                body = (
                    "<p>No paid invoices were recorded in the last 30 days.</p>"
                    f"<p>Coverage: <strong>{target.start_date.isoformat()}</strong> to "
                    f"<strong>{target.end_date.isoformat()}</strong>.</p>"
                )
                email_service.send_to_explicit_recipients(
                    MONTHLY_STATEMENT_RECIPIENTS,
                    subject,
                    body,
                )

        self._save_last_sent_month(target.run_month)

    @staticmethod
    def _build_window(run_date: date) -> MonthlyInvoiceWindow:
        end_date = run_date - timedelta(days=1)
        start_date = run_date - timedelta(days=30)
        return MonthlyInvoiceWindow(
            run_month=run_date.strftime("%Y-%m"),
            start_date=start_date,
            end_date=end_date,
        )

    @staticmethod
    def _next_run_time(now: datetime) -> datetime:
        if now.month == 12:
            next_month = datetime(now.year + 1, 1, 1, 0, 5, tzinfo=SCHEDULER_TIMEZONE)
        else:
            next_month = datetime(now.year, now.month + 1, 1, 0, 5, tzinfo=SCHEDULER_TIMEZONE)

        current_month_target = datetime(now.year, now.month, 1, 0, 5, tzinfo=SCHEDULER_TIMEZONE)
        if now < current_month_target:
            return current_month_target
        return next_month

    @staticmethod
    def _load_last_sent_month() -> Optional[str]:
        if not STATE_FILE.exists():
            return None
        try:
            payload = json.loads(STATE_FILE.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            logger.warning("Unable to read monthly invoice scheduler state file.")
            return None
        value = payload.get("last_sent_month")
        return value if isinstance(value, str) else None

    @staticmethod
    def _save_last_sent_month(run_month: str) -> None:
        STATE_FILE.write_text(
            json.dumps({"last_sent_month": run_month}, indent=2),
            encoding="utf-8",
        )
