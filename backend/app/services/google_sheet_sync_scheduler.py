import asyncio
import logging
from contextlib import suppress
from typing import Optional

from app.core.config import get_settings
from app.services.google_sheet_service import GoogleSheetService

logger = logging.getLogger(__name__)


class GoogleSheetSyncScheduler:
    def __init__(self) -> None:
        self.settings = get_settings()
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
            try:
                await asyncio.to_thread(self._sync_once)
            except Exception:
                logger.exception("Scheduled Google Sheet order sync failed.")
            interval_seconds = max(self.settings.google_sheet_sync_interval_minutes * 60, 300)
            await asyncio.sleep(interval_seconds)

    def _sync_once(self) -> None:
        service = GoogleSheetService()
        if not service.is_configured():
            logger.warning("Scheduled Google Sheet order sync skipped because it is not configured.")
            return

        rows = service.build_successful_order_rows()
        service.sync_successful_orders_snapshot()
        logger.info(
            "Scheduled Google Sheet order sync completed. Synced %s successful order row(s).",
            len(rows) - 1,
        )
