import asyncio
import logging
from contextlib import suppress
from typing import Optional

from app.core.config import get_settings
from app.db.session import SessionLocal
from app.services.order_service import OrderService

logger = logging.getLogger(__name__)


class ShipmentSyncScheduler:
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
                logger.exception("Hourly GenZLogix shipment sync failed.")
            interval_seconds = max(self.settings.genzlogix_sync_interval_minutes * 60, 300)
            await asyncio.sleep(interval_seconds)

    def _sync_once(self) -> None:
        with SessionLocal() as db:
            synced_count = OrderService(db).sync_pending_shipments(limit=100)
        logger.info("Hourly GenZLogix shipment sync completed. Refreshed %s order(s).", synced_count)
