from django.db.models.signals import post_save
from django.dispatch import receiver
from django_q.tasks import async_task
import logging
from accounts.models import Account
from utilities.choices import SCOPE_CHOICES, Role, Role, MemberClassification

logger = logging.getLogger("accounts.signals")


@receiver(post_save, sender=Account)
def notify_executives_of_new_member_added(sender, instance: Account, created, **kwargs):
    if not created:
        return
    try:
        async_task("accounts.tasks.send_notification_new_member_task", instance.id)
    except Exception as e:
        logger.exception("Error in notify_executives_of_new_member_added: %s", e)
        return
