import logging
from django.shortcuts import render, redirect, get_object_or_404
from django.db.models import Sum, Q, Count
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.contrib import messages
from django_q.tasks import async_task
from contributions.forms import ContributionTypeForm
from contributions.models import ContributionType, MemberContribution, Payment
from utilities.choices import LogPaymentStatus, PaymentStatus, Role


logger = logging.getLogger("contributions")


def is_treasurer_or_admin(user):
    """Check if user is treasurer or admin."""
    return user.is_staff or user.role in [Role.TREASURER, Role.CLAN_CHAIRPERSON]


@login_required
def get_contributions(request):
    """List all active contributions."""
    contributions = ContributionType.objects.all().order_by("-created")
    return render(request, 'contributions/index.html', {'contributions': contributions})


@login_required
def get_contribution(request, contribution_slug):
    """
    Display contribution details: total collected, outstanding, by family.
    Optimized queries with select_related/prefetch_related.
    """
    
    user = request.user
    contribution = get_object_or_404(ContributionType, slug=contribution_slug)

    payments = None
    outstandings = None
    
    mcs = MemberContribution.objects.filter(contribution_type=contribution)
    payments = Payment.objects.filter(member_contribution__contribution_type=contribution)
    
    
    
    # Display based on roles
    if is_treasurer_or_admin(user):
        payments = payments.filter(is_approved=LogPaymentStatus.APPROVED).select_related("account")
        outstandings = mcs.filter(
        is_paid__in=[PaymentStatus.NOT_PAID, PaymentStatus.PENDING, PaymentStatus.AWAITING_APPROVAL]
        ).select_related("account")
    else:
        payments = payments.filter(is_approved=LogPaymentStatus.APPROVED).filter(account=user)
        outstandings = mcs.filter(
        is_paid__in=[PaymentStatus.NOT_PAID, PaymentStatus.PENDING, PaymentStatus.AWAITING_APPROVAL], account=user
        ).select_related("account")

    

    
    
    # Aggregate totals (single query)
    unpaid_amount = outstandings.aggregate(total=Sum('amount_due'))['total'] or 0
    total_collected = mcs.filter(is_paid=PaymentStatus.PAID).aggregate(total=Sum("amount_due"))["total"] or 0
    total_collected_m = mcs.filter(account=user).aggregate(total=Sum("amount_due"))["total"] or 0
    outstanding_count = outstandings.count()

    context = {
        "contribution": contribution,
        "payments": payments,
        "total_collected": total_collected,
        "total_collected_m": total_collected_m,
        "unpaid_amount": unpaid_amount,
        "outstanding_count": outstanding_count,
        "outstandings": outstandings,  # Show first 20 outstanding
    }

    return render(request, "contributions/contribution.html", context)


@login_required
def add_contribution(request):
    """Create a new contribution type (treasurer/admin only)."""
    if not is_treasurer_or_admin(request.user):
        messages.error(request, "You don't have permission to create contributions.")
        logger.warning("Unauthorized contribution creation attempt by %s", request.user.username)
        return redirect('contributions:get-contributions')

    if request.method == 'POST':
        form = ContributionTypeForm(request.POST)
        if form.is_valid():
            try:
                contribution = form.save(commit=False)
                contribution.created_by = request.user
                contribution.save()
                
                logger.info(
                    "Contribution created: %s (slug: %s) by %s",
                    contribution.name,
                    contribution.slug,
                    request.user.username
                )
                
                messages.success(request, 'Contribution added successfully.')
                return redirect('contributions:get-contributions')
            except Exception as e:
                logger.exception("Failed to create contribution")
                messages.error(request, 'An error occurred while creating the contribution.')
        else:
            logger.warning("ContributionTypeForm validation failed: %s", form.errors)
            messages.error(request, 'Please fix the errors below.')
    else:
        form = ContributionTypeForm()
    
    return render(request, 'contributions/add-contribution.html', {"form": form})


@login_required
def update_contribution(request, contribution_slug):
    """Update contribution type (treasurer/admin only)."""
    if not is_treasurer_or_admin(request.user):
        messages.error(request, "You don't have permission to edit contributions.")
        logger.warning("Unauthorized contribution edit attempt by %s", request.user.username)
        return redirect('contributions:get-contributions')

    contribution = get_object_or_404(ContributionType, slug=contribution_slug)
    
    if request.method == 'POST':
        form = ContributionTypeForm(request.POST, instance=contribution)
        if form.is_valid():
            try:
                form.save()
                logger.info(
                    "Contribution updated: %s by %s",
                    contribution.slug,
                    request.user.username
                )
                messages.success(request, 'Contribution updated successfully.')
                return redirect('contributions:get-contribution', contribution.slug)
            except Exception as e:
                logger.exception("Failed to update contribution %s", contribution.slug)
                messages.error(request, 'An error occurred while updating the contribution.')
        else:
            logger.warning("ContributionTypeForm validation failed for %s: %s", contribution.slug, form.errors)
            messages.error(request, 'Please fix the errors below.')
    else:
        form = ContributionTypeForm(instance=contribution)
    
    return render(request, 'contributions/add-contribution.html', {'form': form, 'contribution': contribution})


@login_required
def delete_contribution(request, contribution_slug):
    """Delete contribution type (admin only)."""
    if not request.user.is_staff:
        messages.error(request, "Only admins can delete contributions.")
        logger.warning("Unauthorized contribution deletion attempt by %s", request.user.username)
        return redirect('contributions:get-contributions')

    contribution = get_object_or_404(ContributionType, slug=contribution_slug)
    
    # Prevent deletion if there are outstanding payments
    has_payments = Payment.objects.filter(member_contribution__contribution_type=contribution).exists()
    if has_payments:
        messages.error(
            request,
            f"Cannot delete '{contribution.name}'. This contribution has associated payments. Archive it instead."
        )
        logger.warning("Deletion blocked: contribution %s has payments", contribution.slug)
        return redirect('contributions:get-contribution', contribution.slug)

    if request.method == 'POST':
        try:
            name = contribution.name
            contribution.delete()
            logger.info(
                "Contribution deleted: %s by %s",
                name,
                request.user.username
            )
            messages.success(request, f"Contribution '{name}' deleted successfully.")
            return redirect('contributions:get-contributions')
        except Exception as e:
            logger.exception("Failed to delete contribution %s", contribution.slug)
            messages.error(request, 'An error occurred while deleting the contribution.')
    
    return render(request, 'contributions/delete-contribution.html', {'contribution': contribution})
