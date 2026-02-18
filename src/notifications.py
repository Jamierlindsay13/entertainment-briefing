"""Email notification module using SMTP."""

import logging
import os
import smtplib
from email.message import EmailMessage

logger = logging.getLogger(__name__)

SMTP_SERVERS = {
    "gmail.com": "smtp.gmail.com",
    "yahoo.com": "smtp.mail.yahoo.com",
    "rocketmail.com": "smtp.mail.yahoo.com",
    "outlook.com": "smtp-mail.outlook.com",
    "hotmail.com": "smtp-mail.outlook.com",
}


def _get_smtp_server(email: str) -> str:
    """Detect SMTP server from email domain."""
    domain = email.split("@")[-1].lower()
    return SMTP_SERVERS.get(domain, f"smtp.{domain}")


def send_email(to_email: str, subject: str, html_content: str) -> bool:
    """Send an HTML email via SMTP. Returns True on success."""
    email_address = os.environ.get("SMTP_EMAIL")
    email_password = os.environ.get("SMTP_PASSWORD")

    if not email_address or not email_password:
        logger.info(f"[DRY RUN] Would send email to {to_email}: {subject}")
        return False

    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = email_address
    msg["To"] = to_email
    msg.set_content(html_content, subtype="html")

    smtp_server = _get_smtp_server(email_address)

    try:
        server = smtplib.SMTP(smtp_server, 587)
        server.starttls()
        server.login(email_address, email_password)
        server.send_message(msg)
        try:
            server.quit()
        except smtplib.SMTPServerDisconnected:
            pass
        logger.info(f"Email sent to {to_email} via {smtp_server}: {subject}")
        return True
    except smtplib.SMTPResponseException as e:
        if e.smtp_code == 250:
            logger.info(f"Email sent to {to_email} via {smtp_server}: {subject}")
            return True
        logger.error(f"Failed to send email via {smtp_server}: {e}")
        return False
    except Exception as e:
        logger.error(f"Failed to send email via {smtp_server}: {e}")
        return False
