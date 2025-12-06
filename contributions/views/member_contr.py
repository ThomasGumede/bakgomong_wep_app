# contributions/views.py
import logging
from django.http import HttpResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db import transaction
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django_q.tasks import async_task
from django.template.loader import get_template, render_to_string
from accounts.models import Family
from utilities.choices import Role, PaymentStatus
from ..models import MemberContribution
from ..forms import MemberContributionForm
from django.db.models import Sum, Q
from weasyprint import HTML
from io import BytesIO

logger = logging.getLogger("contributions.views")


def is_treasurer_or_admin(user):
    return user.is_staff or getattr(user, "role", None) == Role.TREASURER

@login_required
def download_invoice_pdf(request, id):
    """
    Generate and download PDF invoice for a member contribution.
    """
    contribution = get_object_or_404(MemberContribution.objects.select_related("account", "contribution_type"), id=id)
    # ensure non-admins may only view their own records
    if not request.user.is_staff and contribution.account != request.user and not is_treasurer_or_admin(request.user):
        messages.error(request, "You do not have permission to view this contribution.")
        return redirect("contributions:member-contributions-list")

    # Render HTML template
    html_string = render_to_string("emails/invoice.html", {"order": contribution.payment})

    # Generate PDF
    html = HTML(string=html_string)
    pdf_file = html.write_pdf()

    # Create HTTP response with PDF
    response = HttpResponse(pdf_file, content_type="application/pdf")
    response["Content-Disposition"] = f'attachment; filename="invoice_{contribution.id}.pdf"'

    return response

@login_required
def member_contributions_list(request, family_slug=None):
    """
    List member contributions with role-aware filtering, pagination and totals.
    """
    qs = MemberContribution.objects.select_related("account", "contribution_type", "account__family").order_by("-created")

    if family_slug:
        family = get_object_or_404(Family, slug=family_slug)
        qs = qs.filter(account__family=family)
    else:
        family = None
        # If regular member, show only their contributions
        if not request.user.is_staff and getattr(request.user, "role", None) != Role.TREASURER:
            qs = qs.filter(account=request.user)

    # Pagination
    paginator = Paginator(qs, 30)
    page = request.GET.get("page", 1)
    try:
        contributions_page = paginator.page(page)
    except (PageNotAnInteger, EmptyPage):
        contributions_page = paginator.page(1)

    # Totals (use enums)
    total_contributed = qs.filter(is_paid=PaymentStatus.PAID).aggregate(total=Sum("amount_due"))["total"] or 0
    total_due = qs.filter(is_paid=PaymentStatus.NOT_PAID).aggregate(total=Sum("amount_due"))["total"] or 0
    grand_total = qs.aggregate(total=Sum("amount_due"))["total"] or 0

    context = {
        "contributions": contributions_page,
        "family": family,
        "total_contributed": total_contributed,
        "total_due": total_due,
        "grand_total": grand_total,
    }

    return render(request, "member_inv/index.html", context)


@login_required
def my_member_contributions_list(request):
    """
    Shortcut for the logged-in user's contributions.
    """
    qs = MemberContribution.objects.select_related("account", "contribution_type").filter(account=request.user).order_by("-created")
    paginator = Paginator(qs, 30)
    page = request.GET.get("page", 1)
    try:
        contributions_page = paginator.page(page)
    except (PageNotAnInteger, EmptyPage):
        contributions_page = paginator.page(1)

    return render(request, "member_inv/index.html", {"contributions": contributions_page, "user": request.user})


@login_required
def member_contribution(request, id):
    qs = MemberContribution.objects.select_related("account", "contribution_type")
    contribution = get_object_or_404(qs, id=id)
    # ensure non-admins may only view their own records
    if not request.user.is_staff and contribution.account != request.user and not is_treasurer_or_admin(request.user):
        messages.error(request, "You do not have permission to view this contribution.")
        return redirect("contributions:member-contributions-list")
    return render(request, "member_inv/invoice.html", {"contribution": contribution})


# Add new member contribution
@login_required
def add_member_contribution(request):
    """
    Creation allowed for treasurer/admin or a member creating their own contribution.
    """
    if request.method == "POST":
        form = MemberContributionForm(request.POST)
        if form.is_valid():
            try:
                with transaction.atomic():
                    contribution = form.save(commit=False)
                    # If user is not treasurer/admin, ensure they are creating for themselves
                    if not is_treasurer_or_admin(request.user) and contribution.account != request.user:
                        messages.error(request, "You are not authorized to create contributions for other members.")
                        return redirect("contributions:member-contributions-list")
                    contribution.save()

                # queue creation notification (non-blocking)
                async_task("contributions.tasks.send_contribution_created_notification_task", contribution.pk)
                messages.success(request, "Member contribution added successfully.")
                return redirect("contributions:member-contributions-list")
            except Exception:
                logger.exception("Failed to create MemberContribution")
                messages.error(request, "Error creating member contribution.")
        else:
            messages.error(request, "Please fix the errors below.")
    else:
        form = MemberContributionForm()

    return render(request, "member_inv/member_contribution_form.html", {"form": form})


# Update member contribution
@login_required
def update_member_contribution(request, id):
    contribution = get_object_or_404(MemberContribution, id=id)
    # Only treasurer/admin or owner can update
    if not (is_treasurer_or_admin(request.user) or contribution.account == request.user or request.user.is_staff):
        messages.error(request, "You are not authorized to edit this contribution.")
        return redirect("contributions:member-contributions-list")

    if request.method == "POST":
        form = MemberContributionForm(request.POST, instance=contribution)
        if form.is_valid():
            try:
                with transaction.atomic():
                    form.save()
                messages.success(request, "Member contribution updated successfully.")
                return redirect("contributions:member-contributions-list")
            except Exception:
                logger.exception("Failed to update MemberContribution %s", id)
                messages.error(request, "Error updating member contribution.")
        else:
            messages.error(request, "Please fix the errors below.")
    else:
        form = MemberContributionForm(instance=contribution)

    return render(request, "member_inv/member_contribution_form.html", {"form": form, "contribution": contribution})


# Delete member contribution
@login_required
def delete_member_contribution(request, id):
    contribution = get_object_or_404(MemberContribution, id=id)
    # Only treasurer/admin or staff can delete
    if not (is_treasurer_or_admin(request.user) or request.user.is_staff):
        messages.error(request, "You are not authorized to delete this contribution.")
        return redirect("contributions:member-contributions-list")

    if request.method == "POST":
        try:
            contribution.delete()
            messages.success(request, "Member contribution deleted successfully.")
            return redirect("contributions:member-contributions-list")
        except Exception:
            logger.exception("Failed to delete MemberContribution %s", id)
            messages.error(request, "Error deleting member contribution.")

    return render(request, "member_inv/member_contribution_confirm_delete.html", {"contribution": contribution})
