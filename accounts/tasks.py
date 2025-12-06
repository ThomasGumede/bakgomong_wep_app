import logging
from django.contrib.auth import get_user_model
from accounts.models import Family
from accounts.utils import custom_mail
from utilities.choices import Role

logger = logging.getLogger("tasks")

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
        return custom_mail.send_verification_email(user, None)
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

def send_notification_new_family_task(family_slug):
    try:
        family = Family.objects.get(slug=family_slug)
        allowed_roles = [ 
            Role.DEP_SECRETARY, 
            Role.CLAN_CHAIRPERSON,
            Role.DEP_CHAIRPERSON,
            Role.TREASURER,
            Role.KGOSANA,
            Role.SECRETARY,
            
        ]
        executives = get_user_model().objects.filter(role__in=allowed_roles)
        for member in executives:
            email = custom_mail.send_html_email('New Family Added', [member.email], 'emails/new-family.html', {'full_name': family.name, 'leader': family.leader, 'registered_date': family.created})
            if email:
                logger.info('email send for family')
            else:
                logger.error(f'Failed to send email for new family to {member.email}')
    except Family.DoesNotExist:
        logger.exception("Family not found")
        return False


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