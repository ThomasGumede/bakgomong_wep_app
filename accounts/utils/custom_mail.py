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
from accounts.models import Meeting
from django.conf import settings

from contributions.models import MemberContribution

logger = logging.getLogger("emails")

def send_html_email(subject, to_email, template_name, context):
    try:
        html_content = render_to_string(template_name, context)
        text_content = strip_tags(html_content)

        from_email = getattr(settings, "DEFAULT_FROM_EMAIL", "noreply@bakgomong.co.za")
        msg = EmailMultiAlternatives(subject=subject, body=text_content, from_email=from_email, to=[to_email])
        msg.attach_alternative(html_content, "text/html")
        msg.send()
        logger.info("Email sent to %s (html)", to_email)
        return True
    except Exception as e:
        logger.exception("Failed to send email to %s", to_email)
        return False


def send_email_confirmation_email(user, new_email, request):
    try:
        mail_subject = "BAKGOMONG | New Email Confirmation"
        message = render_to_string("emails/account/email_activation.html",
                {
                    "user": user.get_full_name(),
                    "email": new_email,
                    "uid": generate_activation_token(user),
                    "token": account_activation_token.make_token(user),
                    "website_url": settings.SITE_URL
                }, request
            )

        recipient = (new_email or "").strip() or user.email
        from_email = getattr(settings, "DEFAULT_FROM_EMAIL", "noreply@bakgomong.co.za")
        text_content = strip_tags(message)
        msg = EmailMultiAlternatives(subject=mail_subject, body=text_content, from_email=from_email, to=[recipient])
        msg.attach_alternative(message, "text/html")
        msg.send()
        logger.info("Confirmation email sent to %s", recipient)
        return True
    
    except Exception as err:
        logger.exception("Failed to send send_email_confirmation_email to %s", getattr(user, "email", "<unknown>"))
        return False

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

def send_verification_email(user, request):
    try:
        mail_subject = "BAKGOMONG | Activate Account"
        message = render_to_string("emails/account/account_activate_email.html",
            {
                "user": user.get_full_name(),
                "uid": generate_activation_token(user),
                "token": account_activation_token.make_token(user),
                "website_url": settings.SITE_URL
            }, request
        )

        from_email = getattr(settings, "DEFAULT_FROM_EMAIL", "noreply@bakgomong.co.za")
        text_content = strip_tags(message)
        msg = EmailMultiAlternatives(subject=mail_subject, body=text_content, from_email=from_email, to=[user.email])
        msg.attach_alternative(message, "text/html")
        msg.send()
        logger.info("Verification email sent to %s", user.email)
        return True
    except Exception as err:
        logger.exception("Failed to send send_verification_email to %s", getattr(user, "email", "<unknown>"))
        return False

def send_password_reset_email(user, request):
    try:
        mail_subject = "BAKGOMONG | Password Reset Request"
        
        
        context = {
            'first_name': user.first_name or user.get_full_name(),
            'uid': urlsafe_base64_encode(force_bytes(user.pk)),
            'token': default_token_generator.make_token(user),
            "website_url": settings.SITE_URL,
        }

        html_message = render_to_string("emails/password/reset_password_email.html", context)
        text_message = strip_tags(html_message)

        from_email = getattr(settings, "DEFAULT_FROM_EMAIL", "noreply@bakgomong.co.za")
        email = EmailMultiAlternatives(mail_subject, text_message, from_email, [user.email])
        email.attach_alternative(html_message, "text/html")
        email.send()

        logger.info("Password reset email sent to %s", user.email)
        return True
    
    except Exception:
        logger.exception("Failed to send password reset email to %s", user.email)
        return False

def send_html_email_with_attachments(to_email: str, subject: str, html_content: str, from_email: str, attachments: list = None) -> bool:
    try:
        msg = EmailMultiAlternatives(subject=subject, body=strip_tags(html_content), from_email=from_email, to=[to_email])
        msg.attach_alternative(html_content, "text/html")

        # Attach files if provided
        if attachments:
            for attachment in attachments:
                try:
                    filename = attachment.get("filename")
                    content = attachment.get("file_content")
                    if isinstance(content, str):
                        binary = base64.b64decode(content)
                    else:
                        binary = content.read() if hasattr(content, "read") else bytes(content)
                    ctype, _ = mimetypes.guess_type(filename or "")
                    msg.attach(filename, binary, ctype or "application/octet-stream")
                except Exception:
                    logger.exception("Failed to attach file %s for email to %s", attachment.get("filename"), to_email)

        msg.send()
        logger.info("Email with attachments sent to %s", to_email)
        return True
    except Exception:
        logger.exception("Failed to send email with attachments to %s", to_email)
        return False


    """Send new contribution notification email to member."""
    if not mc or not mc.account or not mc.account.email:
        logger.warning("send_new_meeting_notification: invalid member contribution or user email")
        return False

    try:
        context = {
            "user": mc.account.get_full_name() or mc.account.username,
            "site_url": site_url,
            "contribution": mc
        }

        html_message = render_to_string("emails/contributions/new_contribution_notification.html", context)
        text_message = strip_tags(html_message)

        from_email = getattr(settings, "DEFAULT_FROM_EMAIL", "noreply@bakgomong.co.za")
        email = EmailMultiAlternatives("BAKGOMONG | New Contribution Notification", text_message, from_email, [mc.account.email])
        email.attach_alternative(html_message, "text/html")
        email.send()

        logger.info("New contribution notification email sent to %s", mc.account.email)
        return True
    except Exception:
        logger.exception("Failed to send new contribution notification email to %s", mc.account.email)
        return False