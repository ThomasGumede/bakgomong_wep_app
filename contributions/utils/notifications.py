import logging, requests, uuid
from django.core.mail import send_mail, EmailMessage
from django.conf import settings
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from twilio.rest import Client
from twilio.base.exceptions import TwilioRestException
from contributions.models import MemberContribution
from utilities.validators import validate_rsa_phone
from weasyprint import HTML
from io import BytesIO
from django.template.loader import render_to_string
from django.template.loader import get_template

logger = logging.getLogger("contributions")

import requests
from django.conf import settings
import base64



def send_sms_via_bulksms(to, message):
    """
    BulkSMS API (supports multiple countries including South Africa).
    Returns success bool and response.
    """
    if not to or not message:
        logger.warning("send_sms_via_bulksms: missing to or message")
        return False, {"error": "Missing phone or message"}

    try:
        # Validate phone format
        validate_rsa_phone(to)
    except Exception as e:
        logger.error("Invalid phone number for BulkSMS: %s", to)
        return False, {"error": f"Invalid phone: {str(e)}"}

    url = settings.BULKSMS_API_URL
    credentials = f"{settings.BULKSMS_USERNAME}:{settings.BULKSMS_PASSWORD}"
    encoded_credentials = base64.b64encode(credentials.encode('utf-8')).decode('utf-8')

    headers = {
        "Content-Type": "application/json",
        "Authorization": "Basic ODM5ODk4RTAzREVCNDNENkJFRDA4NUNGNDQ4MDdENzgtMDEtMDoxdkFsYU1vRjZ2VlNkb2tUYUYzRzJyVmF6dlhpIw==",
    }

    payload = {
        "to": to,
        "body": message,
        "from": settings.BULKSMS_SENDER,
    }

    try:
        response = requests.post(
            url,
            json=payload,
            headers=headers,
            timeout=15
        )
        response.raise_for_status()
        result = response.json()
        logger.info("SMS sent via BulkSMS to %s", to)
        return True, result
    except requests.exceptions.RequestException as e:
        logger.exception("Failed to send SMS via BulkSMS to %s", to)
        return False, {"error": str(e)}

def send_sms_via_smsportal(to, message):
    """
    SMSPortal API (South Africa). Returns success bool and response.
    """
    if not to or not message:
        logger.warning("sms_via_smsportal: missing to or message")
        return False, {"error": "Missing phone or message"}

    try:
        # Validate phone format
        validate_rsa_phone(to)
    except Exception as e:
        logger.error("Invalid phone number for SMS: %s", to)
        return False, {"error": f"Invalid phone: {str(e)}"}

    url = "https://rest.smsportal.com/v1/bulkmessages"
    payload = {
        "messages": [
            {
                "content": message,
                "destination": to
            }
        ]
    }
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Basic {settings.SMSPORTAL_AUTH}",
    }

    try:
        response = requests.post(url, json=payload, headers=headers, timeout=10)
        response.raise_for_status()
        result = response.json()
        logger.info("SMS sent via SMSPortal to %s", to)
        return True, result
    except requests.exceptions.RequestException as e:
        logger.exception("Failed to send SMS via SMSPortal to %s", to)
        return False, {"error": str(e)}


def send_sms_via_twilio(to, message):
    """
    Twilio WhatsApp OR SMS. Returns success bool and response.
    """
    if not to or not message:
        logger.warning("send_sms_via_twilio: missing to or message")
        return False, {"error": "Missing phone or message"}

    try:
        validate_rsa_phone(to)
    except Exception as e:
        logger.error("Invalid phone number for Twilio SMS: %s", to)
        return False, {"error": f"Invalid phone: {str(e)}"}

    try:
        client = Client(settings.TWILIO_SID, settings.TWILIO_AUTH_TOKEN)
        result = client.messages.create(
            from_=settings.TWILIO_FROM,
            to=to,
            body=message
        )
        logger.info("SMS sent via Twilio to %s (SID: %s)", to, result.sid)
        return True, {"sid": result.sid}
    except TwilioRestException as e:
        logger.exception("Failed to send SMS via Twilio to %s", to)
        return False, {"error": str(e)}


def send_email_notification(site_url, mc: MemberContribution):
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


def send_payment_details_email(mc: MemberContribution):
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


def generate_reference():
    """Generate a short human-friendly reference (e.g., #CLN-ABC123)."""
    while True:
        ref = f"#CLN-{uuid.uuid4().hex[:6].upper()}"
        if not MemberContribution.objects.filter(reference=ref).exists():
            return ref
