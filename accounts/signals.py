from django.db.models.signals import post_save
from django.dispatch import receiver
from django_q.tasks import async_task
import logging
from accounts.models import Account, Meeting
from utilities.choices import SCOPE_CHOICES, Role, Role

logger = logging.getLogger("accounts.signals")

@receiver(post_save, sender=Meeting)
def notify_members_on_meeting_create(sender, instance: Meeting, created, **kwargs):
    if not created:
        return

    try:
        if instance.audience == SCOPE_CHOICES.CLAN:
            members_qs = Account.objects.filter(is_active=True, is_approved=True).exclude(member_classification__in=['CHILD', 'GRANDCHILD'])
        elif instance.audience == SCOPE_CHOICES.FAMILY and instance.family:
            members_qs = Account.objects.filter(is_active=True, is_approved=True, family=instance.family).exclude(member_classification__in=['CHILD', 'GRANDCHILD'])
        elif instance.audience == SCOPE_CHOICES.FAMILY_LEADERS:
            members_qs = Account.objects.filter(is_active=True, is_approved=True, is_family_leader=True).exclude(member_classification__in=['CHILD', 'GRANDCHILD'])
        elif instance.audience == SCOPE_CHOICES.EXECUTIVES:
            members_qs = Account.objects.filter(is_active=True, is_approved=True, role__in=[
                Role.CLAN_CHAIRPERSON, Role.DEP_CHAIRPERSON, Role.DEP_SECRETARY,
                Role.KGOSANA, Role.SECRETARY, Role.TREASURER
            ]).exclude(member_classification__in=['CHILD', 'GRANDCHILD'])
        else:
            logger.warning("Unknown audience '%s' for Meeting %s", instance.audience, instance.id)
            return
        
        if not members_qs.exists():
            logger.warning("No members found for ContributionType %s (scope %s)", instance.id, instance.scope)
            return
        email_subject = f"New Meeting Scheduled: {instance.title}"
        sms_message = f"New Meeting: {instance.title} on {instance.date_time_formatter}, at {instance.meeting_venue}. Contact excecutives for more information."
        
        for member in members_qs:
            logger.info("Queuing notifications for Meeting %s to member %s (email: %s, phone: %s)", 
                instance.id, member.username, member.email, getattr(member, "phone", "<no phone>"))
            if member.email:
                async_task("accounts.tasks.send_notification_new_meeting_task", instance.id, member.email, email_subject)
            if getattr(member, "phone", None):
                async_task("contributions.utils.notifications.send_smsportal_sms", member.phone, sms_message)
            
    except Exception as e:
        logger.exception("Error in notify_members_on_meeting_create: %s", e)
        return

@receiver(post_save, sender=Account)
def notify_executives_of_new_member_added(sender, instance: Account, created, **kwargs):
    if not created:
        return
    try:
        async_task("accounts.tasks.send_notification_new_member_task", instance.id)
    except Exception as e:
        logger.exception("Error in notify_executives_of_new_member_added: %s", e)
        return
