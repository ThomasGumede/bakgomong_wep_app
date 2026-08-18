from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone
from django_q.tasks import async_task
from datetime import timedelta
from django.db.models import Sum, Q, Count
from dateutil.relativedelta import relativedelta
from accounts.models import Account
from utilities.choices import MemberClassification, Role, PaymentStatus, Recurrence
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
            members_qs = Account.objects.filter(is_active=True, is_approved=True).exclude(Q(member_classification__in=[MemberClassification.CHILD,  MemberClassification.GRANDCHILD]) and Q(role__in=[Role.DEVELOPER, Role.SPONSOR]))
        elif instance.scope == SCOPE_CHOICES.FAMILY and instance.family:
            members_qs = Account.objects.filter(is_active=True, is_approved=True, family=instance.family).exclude(Q(member_classification__in=[MemberClassification.CHILD,  MemberClassification.GRANDCHILD]) and Q(role__in=[Role.DEVELOPER, Role.SPONSOR]))
        elif instance.scope == SCOPE_CHOICES.FAMILY_LEADERS:
            members_qs = Account.objects.filter(is_active=True, is_approved=True, is_family_leader=True).exclude(Q(member_classification__in=[MemberClassification.CHILD,  MemberClassification.GRANDCHILD]) and Q(role__in=[Role.DEVELOPER, Role.SPONSOR]))
        elif instance.scope == SCOPE_CHOICES.EXECUTIVES:
            members_qs = Account.objects.filter(is_active=True, is_approved=True, role__in=[
                Role.CLAN_CHAIRPERSON, Role.DEP_CHAIRPERSON, Role.DEP_SECRETARY,
                Role.KGOSANA, Role.SECRETARY, Role.TREASURER
            ]).exclude(Q(member_classification__in=[MemberClassification.CHILD,  MemberClassification.GRANDCHILD]) and Q(role__in=[Role.DEVELOPER, Role.SPONSOR]))
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

@receiver(post_save, sender=ContributionType) 
def update_member_member_contributions(sender, instance: ContributionType, **kwargs):
    """Update existing contributions when a ContributionType is updated."""
    try:
        # Update due date if changed
        if instance.due_date:
            MemberContribution.objects.filter(contribution_type=instance).update(due_date=instance.due_date)
            logger.info("Updated due date for contributions of type %s", instance.id)

        # Update amount due if changed
        if instance.amount:
            MemberContribution.objects.filter(contribution_type=instance).update(amount_due=instance.amount)
            logger.info("Updated amount due for contributions of type %s", instance.id)
            
        # Update recurrence if changed
        if instance.recurrence:
            new_due_date = calculate_due_date(instance.recurrence)
            MemberContribution.objects.filter(contribution_type=instance).update(due_date=new_due_date)
            logger.info("Updated due date based on recurrence for contributions of type %s", instance.id)
        
        # Update scope if changed
        if instance.scope:
            # Determine target members based on new scope
            if instance.scope == SCOPE_CHOICES.CLAN:
                members_qs = Account.objects.filter(is_active=True, is_approved=True).exclude(Q(member_classification__in=[MemberClassification.CHILD,  MemberClassification.GRANDCHILD]) and Q(role__in=[Role.DEVELOPER, Role.SPONSOR]))
            elif instance.scope == SCOPE_CHOICES.FAMILY and instance.family:
                members_qs = Account.objects.filter(is_active=True, is_approved=True, family=instance.family).exclude(Q(member_classification__in=[MemberClassification.CHILD,  MemberClassification.GRANDCHILD]) and Q(role__in=[Role.DEVELOPER, Role.SPONSOR]))
            elif instance.scope == SCOPE_CHOICES.FAMILY_LEADERS:
                members_qs = Account.objects.filter(is_active=True, is_approved=True, is_family_leader=True).exclude(Q(member_classification__in=[MemberClassification.CHILD,  MemberClassification.GRANDCHILD]) and Q(role__in=[Role.DEVELOPER, Role.SPONSOR]))
            elif instance.scope == SCOPE_CHOICES.EXECUTIVES:
                members_qs = Account.objects.filter(is_active=True, is_approved=True, role__in=[
                    Role.CLAN_CHAIRPERSON, Role.DEP_CHAIRPERSON, Role.DEP_SECRETARY,
                    Role.KGOSANA, Role.SECRETARY, Role.TREASURER
                ]).exclude(Q(member_classification__in=[MemberClassification.CHILD,  MemberClassification.GRANDCHILD]) and Q(role__in=[Role.DEVELOPER, Role.SPONSOR]))
            else:
                logger.warning("Unknown scope '%s' for ContributionType %s", instance.scope, instance.id)
                return

            # Update contributions to match new scope
            existing_contributions = MemberContribution.objects.filter(contribution_type=instance)
            existing_member_ids = set(existing_contributions.values_list('account_id', flat=True))
            new_member_ids = set(members_qs.values_list('id', flat=True))

            # Remove contributions for members no longer in scope
            to_remove_ids = existing_member_ids - new_member_ids
            if to_remove_ids:
                MemberContribution.objects.filter(contribution_type=instance, account_id__in=to_remove_ids, is_paid=PaymentStatus.NOT_PAID).delete()
                logger.info("Removed contributions for %d members no longer in scope for ContributionType %s", len(to_remove_ids), instance.id)
                
            # Create contributions for new members in scope
            to_add_ids = new_member_ids - existing_member_ids
            if to_add_ids:
                new_contributions = [
                    MemberContribution(
                        account_id=member_id,
                        contribution_type=instance,
                        amount_due=instance.amount,
                        reference=generate_reference(),
                        due_date=instance.due_date or calculate_due_date(instance.recurrence),
                        is_paid=PaymentStatus.NOT_PAID
                    )
                    for member_id in to_add_ids
                ]
                MemberContribution.objects.bulk_create(new_contributions, batch_size=1000)
                logger.info("Added contributions for %d new members in scope for ContributionType %s", len(to_add_ids), instance.id)

    except Exception:
        logger.exception("Failed updating contributions for ContributionType %s", instance.id)
        raise
