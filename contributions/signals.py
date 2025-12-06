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


@receiver(post_save, sender=ContributionType)
def create_member_contributions(sender, instance: ContributionType, created, **kwargs):
    """
    Automatically creates MemberContribution records for all eligible members
    whenever a new ContributionType is created.
    
    Handles scope-based targeting: CLAN, FAMILY, FAMILY_LEADERS, EXECUTIVES.
    Queues async notifications (non-blocking).
    """
    
    if not created:
        return

    try:
        # Determine target members based on scope
        if instance.scope == SCOPE_CHOICES.CLAN:
            members_qs = Account.objects.filter(
                is_active=True,
                is_approved=True
            )

        elif instance.scope == SCOPE_CHOICES.FAMILY and instance.family:
            members_qs = Account.objects.filter(
                is_active=True,
                is_approved=True,
                family=instance.family
            )

        elif instance.scope == SCOPE_CHOICES.FAMILY_LEADERS:
            members_qs = Account.objects.filter(
                is_active=True,
                is_approved=True,
                is_family_leader=True
            )

        elif instance.scope == SCOPE_CHOICES.EXECUTIVES:
            members_qs = Account.objects.filter(
                is_active=True,
                is_approved=True,
                is_family_leader=True,
                role__in=[
                    Role.CLAN_CHAIRPERSON,
                    Role.DEP_CHAIRPERSON,
                    Role.DEP_SECRETARY,
                    Role.KGOSANA,
                    Role.SECRETARY,
                    Role.TREASURER,
                    
                ]
            )

        else:
            logger.warning("Unknown scope for ContributionType %s: %s", instance.id, instance.scope)
            members_qs = Account.objects.none()

        member_count = members_qs.count()
        if member_count == 0:
            logger.warning("No eligible members found for ContributionType %s (scope: %s)", 
                           instance.id, instance.scope)
            return

        # Calculate due date
        due_date = instance.due_date or calculate_due_date(instance.recurrence)

        # Prevent duplicate contributions for the same type
        # (in case signal is triggered multiple times)
        existing_count = MemberContribution.objects.filter(
            contribution_type=instance
        ).count()
        if existing_count > 0:
            logger.warning(
                "Contributions already exist for ContributionType %s (%d found). Skipping creation.",
                instance.id, existing_count
            )
            return

        # Bulk create contributions (optimized)
        contributions_to_create = []
        for member in members_qs:
            mc = MemberContribution(
                account=member,
                contribution_type=instance,
                amount_due=instance.amount,
                reference=generate_reference(),
                due_date=due_date,
                is_paid=PaymentStatus.NOT_PAID,
            )
            contributions_to_create.append(mc)

        # Batch create
        created_contributions = MemberContribution.objects.bulk_create(
            contributions_to_create,
            batch_size=1000  # Insert in batches to avoid memory issues
        )
        logger.info(
            "Created %d member contributions for ContributionType %s (name: %s, scope: %s)",
            len(created_contributions),
            instance.id,
            instance.name,
            instance.scope
        )

        # Queue async notifications for each contribution (non-blocking)
        # Fetch IDs to avoid passing entire objects
        contribution_ids = MemberContribution.objects.filter(
            contribution_type=instance
        ).values_list("id", flat=True)[:100]  # Limit to first 100 to avoid queue spam

        for mc_id in contribution_ids:
            async_task(
                "contributions.tasks.send_contribution_created_notification_task",
                mc_id
            )
        logger.info("Queued %d notification tasks for ContributionType %s", len(contribution_ids), instance.id)

    except Exception as e:
        logger.exception(
            "Failed to create member contributions for ContributionType %s",
            instance.id
        )
        raise  # Re-raise to allow Django to handle signal errors

