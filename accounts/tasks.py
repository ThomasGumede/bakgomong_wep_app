import logging
from django.contrib.auth import get_user_model
# from accounts.models import Family
from accounts.utils import custom_mail
from utilities.choices import Role
from django.template.loader import get_template, render_to_string
from django.utils.html import strip_tags
from django.core.mail import EmailMultiAlternatives
from django.utils import timezone
from django.conf import settings

logger = logging.getLogger("tasks")

def send_sms_task(user_pk):
    """
    Background task: send welcome SMS to user.
    Returns (success bool, response dict).
    """
    from contributions.utils.notifications import send_sms_via_bulksms
    User = get_user_model()
    
    try:
        user = User.objects.get(pk=user_pk)
    except User.DoesNotExist:
        logger.error("send_sms_task: user %s not found", user_pk)
        return False, {"error": "User not found"}
    
    # Validate phone exists
    if not user.phone:
        logger.warning("send_sms_task: user %s has no phone number", user_pk)
        return False, {"error": "User has no phone number"}
    
    try:
        message = f"Dear {user.get_full_name()}, welcome to Bakgomong Kgotla. Your account has been created successfully."
        success, response = send_sms_via_bulksms(user.phone, message)
        
        if success:
            logger.info("Welcome SMS sent to %s (User %s)", user.phone, user_pk)
        else:
            logger.warning("Failed to send welcome SMS to %s: %s", user.phone, response)
        
        return success, response
    except Exception:
        logger.exception("send_sms_task failed for user %s", user_pk)
        return False, {"error": "Exception occurred while sending SMS"}

def send_verification_email_task(user_pk):
    """
    Background task: send verification email to user id (no request object).
    Returns True/False based on send result.
    """
    User = get_user_model()
    try:
        user = User.objects.get(pk=user_pk)
    except User.DoesNotExist:
        logger.error("send_verification_email_task: user %s not found", user_pk)
        return False

    try:
        # custom_mail.send_verification_email(user, request=None) works without request
        if user.email:
            logger.info("Sending verification email to %s (User %s)", user.email, user_pk)
            return custom_mail.send_verification_email(user, None)
        if user.phone:
            logger.info("Sending verification SMS to user %s", user)
            from contributions.utils.notifications import send_smsportal_sms
            sms_message = f"Welcome to Bakgomong Kgotla Ya Malla, {user.get_full_name()}! Your account has been created. You can now login using your ID/Phone/Email/Username and password."
            success, response = send_smsportal_sms(user.phone, sms_message)
            if success:
                logger.info("Verification SMS sent to %s (User %s)", user.phone, user_pk)
            else:
                logger.warning("Failed to send verification SMS to %s: %s", user.phone, response)
    except Exception:
        logger.exception("send_verification_email_task failed for %s", user_pk)
        return False

def send_password_reset_email_task(user_pk):
    User = get_user_model()
    try:
        user = User.objects.get(pk=user_pk)
    except User.DoesNotExist:
        logger.error("send_password_reset_email_task: user %s not found", user_pk)
        return False

    try:
        return custom_mail.send_password_reset_email(user, None)
    except Exception:
        logger.exception("send_password_reset_email_task failed for %s", user_pk)
        return False

def send_email_confirmation_task(user_pk, new_email):
    User = get_user_model()
    try:
        user = User.objects.get(pk=user_pk)
    except User.DoesNotExist:
        logger.error("send_email_confirmation_task: user %s not found", user_pk)
        return False

    try:
        return custom_mail.send_email_confirmation_email(user, new_email, None)
    except Exception:
        logger.exception("send_email_confirmation_task failed for %s -> %s", user_pk, new_email)
        return False

def send_notification_new_meeting_task(meeting_pk, to, subject):
    from accounts.models import Meeting
    try:
        meeting = Meeting.objects.get(pk=meeting_pk)
    except Meeting.DoesNotExist:
        logger.error("send_notification_new_meeting_task: Meeting %s not found", meeting_pk)
        return False

    try:
        return custom_mail.send_new_meeting_notification(meeting, to, subject)
    except Exception:
        logger.exception("send_notification_new_meeting_task failed for %s", meeting_pk)
        return False

allowed_roles = [ 
            Role.DEP_SECRETARY, 
            Role.CLAN_CHAIRPERSON,
            Role.DEP_CHAIRPERSON,
            Role.TREASURER,
            Role.KGOSANA,
            Role.SECRETARY,
            
        ]
def send_notification_new_family_task(family_slug):
    """
    Notify executives when a new family is added.
    """
    from accounts.models import Family  # Load model inside function to avoid circular imports

    try:
        family = Family.objects.select_related("leader").get(slug=family_slug)
    except Family.DoesNotExist:
        logger.error("send_notification_new_family_task: Family '%s' not found", family_slug)
        return False

    User = get_user_model()
    executives = User.objects.filter(role__in=allowed_roles).values_list("email", flat=True)

    if not executives:
        logger.warning("No executives found for allowed roles.")
        return False

    html_content = render_to_string(
        "emails/new-family.html",
        {
            "full_name": family.name,
            "leader": family.leader,
            "registered_date": family.created,
        },
    )
    text_content = strip_tags(html_content)

    from_email = getattr(settings, "DEFAULT_FROM_EMAIL", "noreply@bakgomong.co.za")

    for email in executives:
        try:
            msg = EmailMultiAlternatives(
                subject=f"New Family Added: {family.name}",
                body=text_content,
                from_email=from_email,
                to=[email],
            )
            msg.attach_alternative(html_content, "text/html")
            msg.send()
        except Exception:
            logger.exception("Failed sending new family notification to %s", email)

    logger.info("Notification emails sent for new family %s", family.name)
    return True

def send_notification_new_member_task(user_pk):
    """
    Notify executives when a new member is added.
    """
    User = get_user_model()

    try:
        user = User.objects.get(pk=user_pk)
    except User.DoesNotExist:
        logger.error("send_notification_new_member_task: User %s not found", user_pk)
        return False

    executives = User.objects.filter(role__in=allowed_roles).values_list("email", flat=True)

    if not executives:
        logger.warning("No executives found for allowed roles.")
        return False

    html_content = render_to_string(
        "emails/new-member.html",
        {"user": user},
    )
    text_content = strip_tags(html_content)

    from_email = getattr(settings, "DEFAULT_FROM_EMAIL", "noreply@bakgomong.co.za")

    for email in executives:
        try:
            msg = EmailMultiAlternatives(
                subject=f"New Member Added: {user.get_full_name()}",
                body=text_content,
                from_email=from_email,
                to=[email],
            )
            msg.attach_alternative(html_content, "text/html")
            msg.send()
        except Exception:
            logger.exception("Failed sending new member notification to %s", email)

    logger.info("Notification emails sent for new member %s", user.get_full_name())
    return True

def send_html_email_task(subject, to_email, template_name, context, attachments=None):
    """
    Generic HTML email sender that calls your helper which accepts attachments.
    Keep args serializable (context should contain primitives).
    """
    try:
        return custom_mail.send_html_email_with_attachments(
            to_email=to_email,
            subject=subject,
            html_content=template_name and custom_mail.render_template_to_string(template_name, context) or context.get("html", ""),
            from_email=None if not hasattr(custom_mail, "DEFAULT_FROM_EMAIL") else custom_mail.DEFAULT_FROM_EMAIL,
            attachments=attachments,
        )
    except Exception:
        logger.exception("send_html_email_task failed for %s", to_email)
        return False