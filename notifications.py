"""
Best-effort email notification when a new lead comes in.

If SMTP settings aren't configured, this quietly no-ops (logged, not
raised) so the lead-capture flow still works without email set up. A
failed or skipped notification never fails the lead submission itself —
the lead is already safely stored in SQLite by the time this runs.
"""

import logging
import os
import smtplib
from email.message import EmailMessage

logger = logging.getLogger("northstar.notifications")


def send_lead_notification(lead: dict, lead_id: int) -> bool:
    host = os.getenv("SMTP_HOST")
    port = os.getenv("SMTP_PORT")
    username = os.getenv("SMTP_USERNAME")
    password = os.getenv("SMTP_PASSWORD")
    to_addr = os.getenv("NOTIFICATION_EMAIL")
    if not all([host, port, username, password, to_addr]):
        logger.info(
            "Skipping email notification for lead #%s: SMTP settings are not fully configured.",
            lead_id,
        )
        return False

    message = EmailMessage()
    message["Subject"] = f"New case evaluation request — {lead['first_name']} {lead['last_name']}"
    message["From"] = username
    message["To"] = to_addr
    message.set_content(
        "A new case evaluation request was submitted on the website.\n\n"
        f"Lead ID: {lead_id}\n"
        f"Name: {lead['first_name']} {lead['last_name']}\n"
        f"Phone: {lead['phone']}\n"
        f"Email: {lead['email']}\n"
        f"Preferred contact method: {lead.get('contact_method') or 'Not specified'}\n"
        f"Accident type: {lead['accident_type']}\n"
        f"Accident date: {lead.get('accident_date') or 'Not provided'}\n\n"
        "Description:\n"
        f"{lead['description']}\n"
    )

    try:
        with smtplib.SMTP(host, int(port), timeout=10) as server:
            server.starttls()
            server.login(username, password)
            server.send_message(message)
        logger.info("Sent lead notification email for lead #%s.", lead_id)
        return True
    except Exception:  # noqa: BLE001 - a failed email must never break lead capture
        logger.warning("Failed to send lead notification email for lead #%s.", lead_id, exc_info=True)
        return False
