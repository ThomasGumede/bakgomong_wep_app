from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone
from django_q.tasks import async_task
from datetime import timedelta

from dateutil.relativedelta import relativedelta
from accounts.models import Account
from utilities.choices import Role, PaymentStatus, Recurrence
from contributions.utils.notifications import generate_reference
from contributions.models import ContributionType, MemberContribution, SCOPE_CHOICES

import logging

logger = logging.getLogger("signals")


def chunk_list(data, size=100):
    """Yield successive chunks of size `size` from list `data`."""
    for i in range(0, len(data), size):
        yield data[i:i + size]


def calculate_due_date(recurrence):
    """Calculate due date based on recurrence type."""
    today = timezone.now().date()

    if recurrence == Recurrence.MONTHLY:
        return today + relativedelta(months=1)
    elif recurrence == Recurrence.ANNUAL:
        return today + relativedelta(years=1)
    elif recurrence == Recurrence.ONCE_OFF:
        return today + timedelta(days=7)
    else:
        return today

# signals.py
@receiver(post_save, sender=ContributionType)
def create_member_contributions(sender, instance: ContributionType, created, **kwargs):
    if not created:
        return

    try:
        # Determine target members
        if instance.scope == SCOPE_CHOICES.CLAN:
            members_qs = Account.objects.filter(is_active=True, is_approved=True).exclude(member_classification__in=['CHILD', 'GRANDCHILD'])
        elif instance.scope == SCOPE_CHOICES.FAMILY and instance.family:
            members_qs = Account.objects.filter(is_active=True, is_approved=True, family=instance.family).exclude(member_classification__in=['CHILD', 'GRANDCHILD'])
        elif instance.scope == SCOPE_CHOICES.FAMILY_LEADERS:
            members_qs = Account.objects.filter(is_active=True, is_approved=True, is_family_leader=True).exclude(member_classification__in=['CHILD', 'GRANDCHILD'])
        elif instance.scope == SCOPE_CHOICES.EXECUTIVES:
            members_qs = Account.objects.filter(is_active=True, is_approved=True, role__in=[
                Role.CLAN_CHAIRPERSON, Role.DEP_CHAIRPERSON, Role.DEP_SECRETARY,
                Role.KGOSANA, Role.SECRETARY, Role.TREASURER
            ]).exclude(member_classification__in=['CHILD', 'GRANDCHILD'])
        else:
            logger.warning("Unknown scope '%s' for ContributionType %s", instance.scope, instance.id)
            return

        if not members_qs.exists():
            logger.warning("No members found for ContributionType %s (scope %s)", instance.id, instance.scope)
            return

        # Avoid duplicates
        if MemberContribution.objects.filter(contribution_type=instance).exists():
            logger.warning("Contributions already exist for ContributionType %s — skipped.", instance.id)
            return

        # Calculate due date
        due_date = instance.due_date or calculate_due_date(instance.recurrence)

        # Create contributions in bulk
        contributions = [
            MemberContribution(
                account=member,
                contribution_type=instance,
                amount_due=instance.amount,
                reference=generate_reference(),
                due_date=due_date,
                is_paid=PaymentStatus.NOT_PAID
            )
            for member in members_qs
        ]

        created_entries = MemberContribution.objects.bulk_create(contributions, batch_size=1000)
        logger.info("Created %d contributions for type %s (%s, scope=%s)", len(created_entries), instance.id, instance.name, instance.scope)

        # Queue notifications in batches of 100
        all_ids = list(MemberContribution.objects.filter(contribution_type=instance).values_list("id", flat=True))
        for batch in chunk_list(all_ids, size=100):
            async_task("contributions.tasks.send_contribution_created_notification_task", batch)

        logger.info("Queued %d batched notification tasks for ContributionType %s", len(list(chunk_list(all_ids, 100))), instance.id)

    except Exception:
        logger.exception("Failed creating contributions for ContributionType %s", instance.id)
        raise


