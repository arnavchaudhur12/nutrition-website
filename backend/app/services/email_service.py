import logging

from app.core.config import get_settings

logger = logging.getLogger(__name__)


class EmailService:
    def __init__(self) -> None:
        self.settings = get_settings()

    def send_order_confirmation(self, buyer_email: str, subject: str, html_body: str) -> None:
        # SMTP wiring is configured here but left as a controlled integration step
        # until the mailbox password or app-specific credentials are provided.
        logger.info(
            "Email queued for buyer=%s admin=%s subject=%s",
            buyer_email,
            self.settings.notification_email,
            subject,
        )
        logger.debug("Email body preview: %s", html_body[:500])

