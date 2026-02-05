import logging
import requests
import uuid
import base64

from django.core.mail import EmailMessage
from django.conf import settings
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from twilio.rest import Client
from twilio.base.exceptions import TwilioRestException
from requests.auth import HTTPBasicAuth

from contributions.models import MemberContribution
from utilities.validators import validate_rsa_phone

logger = logging.getLogger("contributions")

# API timeout constants (in seconds)
SMS_API_TIMEOUT = 10
BULKSMS_TIMEOUT = 15


def send_smsportal_sms(msisdn: str, message: str) -> tuple[bool, dict]:
    """
    Send a single SMS using SMSPortal
    """
    basic = HTTPBasicAuth(settings.SMSPORTAL_CLIENT_ID, settings.SMSPORTAL_API_SECRET)

    payload = {
        "messages": [
            {
                "content": message,
                "destination": msisdn,
            }
        ]
    }
    try:
        response = requests.post(
            settings.SMSPORTAL_URL,
            auth=basic,
            json=payload,
            timeout=SMS_API_TIMEOUT
        )
        response.raise_for_status()
        result = response.json()
        if response.status_code in (200, 201):
            logger.info("SMSPortal response: %s", result)
            return True, result
        else:
            logger.error("SMSPortal error response: %s", result)
            return False, result
    except requests.RequestException as e:
        logger.exception("SMSPortal request failed: %s", e)
        return False, {"error": str(e)}


def send_email_notification(site_url: str, mc: MemberContribution) -> bool:
    """
    Sends an HTML email when a new MemberContribution is created.
    """
    if not mc or not mc.account or not mc.account.email:
        logger.warning("send_email_notification: invalid member contribution or user email")
        return False

    try:
        context = {
            "user": mc.account.get_full_name() or mc.account.username,
            "contribution_type": mc.contribution_type.name,
            "amount_due": mc.amount_due,
            "due_date": mc.due_date,
            "site_url": site_url,
        }
        html_content = render_to_string("emails/contribution-notification.html", context)
        text_content = strip_tags(html_content)
        
        from_email = getattr(settings, "DEFAULT_FROM_EMAIL", "noreply@bakgomong.co.za")
        msg = EmailMessage(
            subject=f"New Contribution: {mc.contribution_type.name}",
            body=text_content,
            from_email=from_email,
            to=[mc.account.email],
        )
        msg.attach_alternative(html_content, "text/html")
        msg.send()
        logger.info("Contribution notification email sent to %s", mc.account.email)
        return True
    except Exception as e:
        logger.exception("Failed to send contribution notification email to %s", mc.account.email if mc.account else "<unknown>")
        return False


def send_payment_details_email(mc: MemberContribution) -> bool:
    """Send payment details email for a member contribution."""
    if not mc or not mc.account or not mc.account.email:
        logger.warning("send_payment_details_email: invalid member contribution or user email")
        return False

    template_name = "emails/payment-information.html"
 
    try:
        context = {
            "user": mc.account.get_full_name() or mc.account.username,
            "contribution_type": mc.contribution_type.name,
            "amount_due": mc.amount_due,
            "due_date": mc.due_date,
            "reference": mc.reference,
        }
        html_content = render_to_string(template_name, context)
        text_content = strip_tags(html_content)

        from_email = getattr(settings, "DEFAULT_FROM_EMAIL", "noreply@bakgomong.co.za")
        msg = EmailMessage(
            subject=f"Payment Details: {mc.contribution_type.name}",
            body=text_content,
            from_email=from_email,
            to=[mc.account.email],
        )
        msg.attach_alternative(html_content, "text/html")
        msg.send()
        logger.info("Payment details email sent to %s", mc.account.email)
        return True
    except Exception as e:
        logger.exception("Failed to send payment details email to %s", mc.account.email if mc.account else "<unknown>")
        return False


def generate_reference() -> str:
    """Generate a short human-friendly reference (e.g., #CLN-ABC123)."""
    while True:
        ref = f"#CLN-{uuid.uuid4().hex[:6].upper()}"
        if not MemberContribution.objects.filter(reference=ref).exists():
            return ref
