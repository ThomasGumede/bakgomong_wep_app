from accounts.forms import FamilyForm
from accounts.models import ClanDocument, Family
from django.shortcuts import redirect, render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.http import HttpResponseForbidden
from django.contrib import messages
from django.conf import settings
from django.db.models import Sum
from django_q.tasks import async_task
from django.contrib.auth import get_user_model
import logging

from contributions.models import MemberContribution, Payment, ContributionType
from utilities.choices import SCOPE_CHOICES, PaymentStatus, Role

logger = logging.getLogger("accounts")

@login_required
def get_families(request):
    user  = request.user
    if user.role == Role.MEMBER and not user.is_staff:
        families = Family.objects.filter(is_approved=True, id=user.family.id)
    else:
        families = Family.objects.filter(is_approved=True)
    return render(request, 'family/families.html', {"families": families})


@login_required
def get_family(request, family_slug=None):
    """
    Show a family's profile, members, contributions, unpaid balances, and uploaded documents.
    """
    user = request.user
    context = {}
    # Determine which families the user can view
    if user.role == Role.MEMBER and not user.is_staff:
        families = Family.objects.filter(is_approved=True, id=user.family.id)
    else:
        families = Family.objects.filter(is_approved=True)

    family = get_object_or_404(families, slug=family_slug)
    family_contr = ContributionType.objects.filter(scope=SCOPE_CHOICES.FAMILY, family=family, is_active=True).order_by('-created')
    mc = MemberContribution.objects.filter(account__family=family).select_related("account", "contribution_type").order_by("-created")
    
    context['family'] = family
    context['family_balance'] = mc.filter(is_paid__in=[PaymentStatus.PAID]).aggregate(total=Sum("amount_due")).get("total") or 0
    context['family_outstanding'] = mc.filter(is_paid__in=[PaymentStatus.NOT_PAID, PaymentStatus.PENDING, PaymentStatus.AWAITING_APPROVAL]).aggregate(total=Sum("amount_due")).get("total") or 0
    context['total_unpaid'] = mc.filter(account=user, is_paid__in=[PaymentStatus.NOT_PAID, PaymentStatus.PENDING, PaymentStatus.AWAITING_APPROVAL]).aggregate(
            total=Sum("amount_due")
        ).get("total") or 0
    context['total_paid'] = mc.filter(account=user, is_paid__in=[PaymentStatus.PAID]).aggregate(
            total=Sum("amount_due")
        ).get("total") or 0
    
    if user.role == Role.MEMBER and not user.is_staff:
        contributions = mc.filter(
            account=user
        )[:5]
    else:
        contributions = mc[:5]

    # Get all members in the family
    members = family.members.select_related("family").all()

    # Fetch family documents if needed
    documents = ClanDocument.objects.filter(family=family).order_by("-created")

    context['members'] = members
    context["contributions"] = contributions
    context['fcs'] = family_contr
    context['documents'] = documents


    return render(request, "family/family.html", context)



EXECUTIVE_ROLES = [
    Role.CLAN_CHAIRPERSON,
    Role.DEP_CHAIRPERSON,
    Role.SECRETARY,
    Role.DEP_SECRETARY,
    Role.TREASURER,
    Role.KGOSANA,
]


@login_required
def add_family(request):

    # Restrict access to executives only
    if request.user.role not in EXECUTIVE_ROLES and not request.user.is_staff:
        return HttpResponseForbidden("You do not have permission to perform this action.")

    form = FamilyForm(request.POST or None)

    if request.method == "POST":
        if form.is_valid():
            try:
                with transaction.atomic():
                    family = form.save(commit=False)

                    # Mark for approval depending on creator role
                    if request.user.is_family_leader:
                        family.is_approved = False
                    else:
                        family.is_approved = True

                    # family.created_by = request.user
                    family.save()

                    # Link leader → family
                    leader = family.leader
                    leader.family = family
                    leader.save(update_fields=["family"])
                    
                    # Notify executives about new family (non-blocking) via django-q
                    async_task("accounts.tasks.send_notification_new_family_task", family.slug)
                messages.success(request, "Family added successfully.")
                return redirect("accounts:get-families")

            except Exception as e:
                logger.exception(f"Failed to create family: {e}")
                messages.error(request, "Something went wrong while adding the family.")

        else:
            messages.error(request, "Please fix the errors below.")

    return render(request, "family/add-family.html", {"form": form})

@login_required
def update_family(request, family_slug):
    family = get_object_or_404(Family, slug=family_slug)
    if not request.user.is_staff:
        return HttpResponseForbidden()
    form = FamilyForm(instance=family)
    if request.method == 'POST':
        form = FamilyForm(request.POST, instance=family)
        if form.is_valid():
            try:
                with transaction.atomic():
                    family = form.save()
                messages.success(request, "Family updated successfully")
                return redirect('accounts:get-families')
            except Exception:
                logger.exception("Failed to update family %s", family_slug)
                messages.error(request, 'Something went wrong while updating family')
        else:
            messages.error(request, 'Please fix the errors below.')
            
    return render(request, 'family/add-family.html', {"form": form})

@login_required
def delete_family(request, family_slug):
    if not request.user.is_staff:
        return HttpResponseForbidden()
    family = get_object_or_404(Family, slug=family_slug)
    # Only allow delete via POST (avoid accidental deletes via GET)
    if request.method == "POST":
        family.delete()
        messages.success(request, "Family deleted successfully")
        return redirect('accounts:get-families')
    # Render a simple confirmation template (create template if needed)
    return render(request, "family/confirm_delete.html", {"family": family})

