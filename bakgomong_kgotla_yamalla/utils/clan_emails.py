from bakgomong_kgotla_yamalla.models import Meeting
import logging
import base64
import mimetypes
from django.utils.encoding import force_bytes
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from accounts.utils.tokens import account_activation_token, generate_activation_token
from django.utils.http import urlsafe_base64_encode
from django.core.mail import EmailMessage, EmailMultiAlternatives, get_connection
from django.contrib.sites.shortcuts import get_current_site
from django.contrib.auth.tokens import default_token_generator
from django.conf import settings

logger = logging.getLogger("emails")

def send_new_meeting_notification(meeting: Meeting, to: str, subject: str) -> bool:
    """Send new meeting notification email to all members."""
    if not meeting:
        logger.warning("send_new_meeting_notification: invalid meeting object")
        return False

    try:
        context = {
            "meeting": meeting,
            "site_url": settings.SITE_URL,
            "subject": subject,
        }

        html_message = render_to_string("emails/new_meeting_notification.html", context)
        text_message = strip_tags(html_message)

        from_email = getattr(settings, "DEFAULT_FROM_EMAIL", "noreply@bakgomong.co.za")
        email = EmailMultiAlternatives(subject, text_message, from_email, [to])
        email.attach_alternative(html_message, "text/html")
        email.send()

        logger.info("New meeting notification email sent to %s", to)
        return True
    except Exception:
        logger.exception("Failed to send new meeting notification email")
        return False
