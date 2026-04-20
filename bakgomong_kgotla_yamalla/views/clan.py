import logging
import mimetypes
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.db.models import Sum
from django.contrib import messages
from django.contrib import messages
from bakgomong_kgotla_yamalla.models import KgotlaBalance, KgotlaExpense
from django.core.exceptions import PermissionDenied
from contributions.models import ContributionType, MemberContribution
from utilities.choices import PaymentStatus, Role
from accounts.models import Account


logger = logging.getLogger("bakgomong_kgotla_yamalla")

@login_required    
def clan_expenses(request):
    user = request.user
    context = {}
    context["members"] = Account.objects.filter(is_active=True).count()
    context["total_expenses_balance"] = KgotlaExpense.objects.aggregate(total=Sum("amount"))["total"] or 0
    context['expenses'] = KgotlaExpense.objects.all().order_by("-incurred_date")
    context["kgotla_balance"] = KgotlaBalance.objects.first()
    return render(request, "balance/clan-expenses.html", context)

@login_required
def dashboard(request):
    user = request.user
    context = {}

    member_contribs_qs = MemberContribution.objects.all().order_by("-created")
    
    # Total paid for clan
    context["clan_total_paid"] = member_contribs_qs.filter(
        is_paid=PaymentStatus.PAID
    ).aggregate(total_paid=Sum("amount_due"))["total_paid"] or 0
    

    # Last 5 unpaid/pending payments for user
    unpaid_statuses = [PaymentStatus.NOT_PAID, PaymentStatus.PENDING, PaymentStatus.AWAITING_APPROVAL]
    context["latest_unpaid"] = member_contribs_qs.filter(account=user, is_paid=PaymentStatus.NOT_PAID).order_by('-due_date').first()
    context["members"] = Account.objects.filter(is_active=True).count()
    context["kgotla_balance"] = KgotlaBalance.objects.first()
    context["total_expenses_balance"] = KgotlaExpense.objects.aggregate(total=Sum("amount"))["total"] or 0
   
    

    if user.is_staff:
        clan_unpaid_qs = member_contribs_qs.filter(is_paid__in=unpaid_statuses)
        context["clan_total_unpaid"] = clan_unpaid_qs.aggregate(
            total_unpaid=Sum("amount_due")
        )["total_unpaid"] or 0
        context["clan_total_unpaid_count"] = clan_unpaid_qs.count()
        context["payments"] = member_contribs_qs.select_related("account")[:5]

    return render(request, 'dashboard.html', context)



