import logging
import smtplib
from email.message import EmailMessage
from typing import Iterable

from app.core.config import get_settings

logger = logging.getLogger(__name__)

EmailAttachment = tuple[str, bytes, str, str]


class EmailService:
    def __init__(self) -> None:
        self.settings = get_settings()

    def send_order_confirmation(
        self,
        buyer_email: str,
        subject: str,
        html_body: str,
        attachments: Iterable[EmailAttachment] = (),
    ) -> None:
        self._send_to_buyer_and_admin(buyer_email, subject, html_body, attachments)

    def send_payment_failure(
        self,
        buyer_email: str,
        subject: str,
        html_body: str,
        attachments: Iterable[EmailAttachment] = (),
    ) -> None:
        self._send_to_buyer_and_admin(buyer_email, subject, html_body, attachments)

    def _send_to_buyer_and_admin(
        self,
        buyer_email: str,
        subject: str,
        html_body: str,
        attachments: Iterable[EmailAttachment] = (),
    ) -> None:
        recipients = list(
            dict.fromkeys(
                [buyer_email, self.settings.notification_email, self.settings.smtp_user]
            )
        )
        local_smtp_hosts = {"localhost", "127.0.0.1", "0.0.0.0"}
        can_send_without_password = self.settings.smtp_host in local_smtp_hosts
        if not self.settings.smtp_password and not can_send_without_password:
            logger.info(
                "Email queued for buyer=%s admin=%s subject=%s",
                buyer_email,
                self.settings.notification_email,
                subject,
            )
            logger.debug("Email body preview: %s", html_body[:500])
            return

        attachment_list = list(attachments)

        for recipient in recipients:
            message = EmailMessage()
            message["Subject"] = subject
            message["From"] = f"{self.settings.smtp_sender_name} <{self.settings.smtp_user}>"
            message["To"] = recipient
            message.set_content(self._html_to_text(html_body))
            message.add_alternative(html_body, subtype="html")

            for filename, content, maintype, subtype in attachment_list:
                message.add_attachment(
                    content,
                    maintype=maintype,
                    subtype=subtype,
                    filename=filename,
                )

            try:
                self._deliver(message)
            except (OSError, smtplib.SMTPException):
                logger.exception("Failed to send email subject=%s recipient=%s", subject, recipient)
                continue

            logger.info("Email sent to recipient=%s subject=%s", recipient, subject)

    def _deliver(self, message: EmailMessage) -> None:
        with smtplib.SMTP(self.settings.smtp_host, self.settings.smtp_port) as smtp:
            if self.settings.smtp_use_tls:
                smtp.starttls()
            if self.settings.smtp_password:
                smtp.login(self.settings.smtp_user, self.settings.smtp_password)
            smtp.send_message(message)

    @staticmethod
    def _html_to_text(html_body: str) -> str:
        return (
            html_body.replace("<br/>", "\n")
            .replace("</p>", "\n\n")
            .replace("</tr>", "\n")
            .replace("</td>", " ")
            .replace("</th>", " ")
            .replace("<strong>", "")
            .replace("</strong>", "")
        )
