import logging
import mimetypes
from django.utils import timezone
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.db.models import Sum
import decimal
from django.contrib import messages
from bakgomong_kgotla_yamalla.models import KgotlaBalance, KgotlaExpense, Meeting
from django.core.exceptions import PermissionDenied
from contributions.models import ContributionType, MemberContribution
from utilities.choices import PaymentStatus, Role
from accounts.models import Account
from bakgomong_kgotla_yamalla.forms import KgotlaExpenseForm, ClanDocumentForm, MeetingForm

logger = logging.getLogger("bakgomong_kgotla_yamalla")

def home(request):
    return render(request, "home.html", {})

@login_required    
def clan_expenses(request):
    user = request.user
    context = {}
    
    total_contributions = MemberContribution.objects.aggregate(total=Sum("amount_due"))["total"] or 0
    total_contributions_paid = MemberContribution.objects.filter(is_paid=PaymentStatus.PAID).aggregate(total=Sum("amount_due"))["total"] or 0
    total_contributions_unpaid = MemberContribution.objects.filter(is_paid__in=[PaymentStatus.NOT_PAID, PaymentStatus.PARTIALLY_PAID, PaymentStatus.PENDING, PaymentStatus.AWAITING_APPROVAL]).aggregate(total=Sum("amount_due"))["total"] or 0

    percentage_paid = (decimal.Decimal(total_contributions_paid) / decimal.Decimal(total_contributions) * 100) if total_contributions else 0
    outstanding_percentage = (decimal.Decimal(total_contributions_unpaid) / decimal.Decimal(total_contributions) * 100) if total_contributions else 0
    context["members"] = Account.objects.count()
    context['families'] = Account.objects.values_list('family', flat=True).distinct().count()
    context["total_contributions"] = total_contributions
    context["total_contributions_paid"] = total_contributions_paid
    context["total_contributions_unpaid"] = total_contributions_unpaid
    context["outstanding_percentage"] = outstanding_percentage or 0
    context["total_expenses_balance"] = KgotlaExpense.objects.aggregate(total=Sum("amount"))["total"] or 0
    context['expenses'] = KgotlaExpense.objects.all().order_by("-incurred_date")
    context["kgotla_balance"] = KgotlaBalance.objects.first()
    return render(request, "balance/clan-expenses.html", context)

@login_required
def record_expense(request):
    user = request.user
    if user.role != Role.TREASURER:
        raise PermissionDenied("You do not have permission to record expenses.")
    
    if request.method == "POST":
        form = KgotlaExpenseForm(request.POST, request.FILES)
        if form.is_valid():
            expense = form.save(commit=False)
            expense.recorded_by = user
            expense.save()
            
            messages.success(request, "Expense recorded successfully.")
            return redirect("bakgomong_kgotla_yamalla:clan-expenses")
        else:
            messages.error(request, "There was an error recording the expense. Please check the form for errors.")
            form = KgotlaExpenseForm(request.POST, request.FILES)  # Reinitialize the form with POST data to display errors
            return render(request, "balance/record-expense.html", {"form": form})
    else:
        form = KgotlaExpenseForm()
        return render(request, "balance/record-expense.html", {"form": form})

@login_required
def dashboard(request):
    user = request.user
    context = {}

    member_contribs_qs = MemberContribution.objects.all().order_by("-created")
    
    # Total paid for clan
    context["clan_total_paid"] = member_contribs_qs.filter(
        is_paid=PaymentStatus.PAID
    ).aggregate(total_paid=Sum("amount_due"))["total_paid"] or 0
    
    user_unpaids = member_contribs_qs.filter(account=user, is_paid=PaymentStatus.NOT_PAID).order_by('-due_date')
    
    # Last 5 unpaid/pending payments for user
    context["latest_unpaids"] = user_unpaids
    context["unpaid_amount"] = user_unpaids.aggregate(total=Sum("amount_due"))["total"] or 0
    context["members"] = Account.objects.filter(is_active=True).count()
    context["upcoming_meetings"] = Meeting.objects.filter(meeting_date__gt=timezone.now()).order_by("meeting_date")[:5]
    

    return render(request, 'dashboard.html', context)



