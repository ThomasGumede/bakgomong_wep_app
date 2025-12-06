import logging, requests, json
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db import transaction
from django.urls import reverse
from django_q.tasks import async_task
from django.conf import settings
from contributions.forms import LogPaymentForm, PaymentCheckoutForm
from contributions.utils.yoco_funcs import decimal_to_str, headers
from utilities.choices import LogPaymentStatus, PaymentMethod, PaymentStatus, Role
from ..models import ContributionType, MemberContribution, Payment


logger = logging.getLogger("contributions")


@login_required
def checkout(request, id):
    user = request.user
    
    member_contribution = get_object_or_404(MemberContribution, id=id, is_paid__in=[PaymentStatus.NOT_PAID, PaymentStatus.PENDING, PaymentStatus.AWAITING_APPROVAL])
    contribution_type = member_contribution.contribution_type

    # Only allow users to pay their own contributions (or staff/admin)
    if member_contribution.account != request.user and not request.user.is_staff:
        messages.error(request, "You can only pay for your own contributions.")
        return redirect("contributions:member-contributions")
    
    if not contribution_type.is_active:
        messages.error(request, "This contribution is no longer active.")
        return redirect("contributions:member-contribution", id=member_contribution.id)
    
    payment = Payment.objects.filter(member_contribution=member_contribution, is_approved__in=[LogPaymentStatus.PENDING, LogPaymentStatus.NOT_PAID]).first()
    
    if payment:
        messages.info(request, "A payment record already exists for this contribution. Please proceed to payment.")
        if payment.payment_method_type == PaymentMethod.MOBILE:
            return redirect("contributions:yoco-checkout", payment_id=member_contribution.payment.id)
        return redirect("contributions:member-contribution", id=member_contribution.id)
    # If staff is paying on behalf of member, use the member account
    if request.user.is_staff and member_contribution.account != request.user:
        user = member_contribution.account
         
    if request.method == "POST":
        form = PaymentCheckoutForm(request.POST, user=request.user)
        if form.is_valid():
            payment_method = request.POST.get("payment_method", "").strip().lower()

            try:
                with transaction.atomic():
                    payment = form.save(commit=False)
                    payment.account = user
                    payment.contribution_type = contribution_type
                    payment.recorded_by = request.user
                    payment.payment_method_type = payment_method
                    payment.is_approved = LogPaymentStatus.PENDING
                    payment.reference = member_contribution.reference
                    payment.save()
                    # update member contribution status (also atomic via Payment.save)
                    

                logger.info(
                    "Payment created: %s R%.2f for %s (method: %s)",
                    payment.id,
                    member_contribution.amount_due,
                    user.username,
                    payment_method,
                )

                # Route based on payment method
                if payment_method in [PaymentMethod.CASH, PaymentMethod.BANK]:
                    # Queue email with banking details (non-blocking)
                    payment.update_member_contribution_status(PaymentStatus.AWAITING_APPROVAL)
                    async_task("contributions.tasks.send_payment_details_task", member_contribution.pk)
                    messages.success(
                        request,
                        f"Payment of R{member_contribution.amount_due:.2f} for {contribution_type.name} has been recorded successfully!"
                    )
                    messages.info(
                        request,
                        f"You chose {payment_method.replace('_', ' ').title()} as your payment method. We have emailed you banking details. Please upload proof of payment once completed."
                    )
                    return redirect("contributions:member-contribution", id=member_contribution.id)

                elif payment_method == PaymentMethod.MOBILE:
                    # Redirect to Yoco checkout
                    payment.update_member_contribution_status(PaymentStatus.AWAITING_APPROVAL)
                    messages.info(request, "Redirecting to Yoco secure payment...")
                    return redirect("contributions:yoco-checkout", payment_id=payment.id)

                else:
                    logger.warning("Unknown payment method: %s", payment_method)
                    messages.error(request, "Invalid payment method selected.")
                    return redirect("contributions:checkout", id=member_contribution.id)
            
            except Exception as e:
                logger.exception("Failed to create payment for contribution %s", id)
                messages.error(request, "An error occurred while recording your payment. Please try again.")
        else:
            logger.warning("PaymentCheckoutForm validation failed for contribution %s", id)
            messages.error(request, "Please fix the errors below.")
      
    else:
        form = PaymentCheckoutForm(user=user, initial={
            
            "member_contribution": member_contribution,
            "amount": member_contribution.amount_due,
        })
    
    context = {
        "contribution_type": contribution_type,
        "member_contribution": member_contribution,
        "form": form,
        "user": user,
    }
    return render(request, "payments/checkout.html", context)


@login_required
def log_paymens(request):
    """
    Redirect to member contributions page for treasurers to select a contribution to log payment for.
    """
    context = {}
    # Only treasurers can log payments
    if request.user.role != Role.TREASURER and not request.user.is_staff:
        messages.error(request, "Only treasurers can log payments.")
        return redirect("contributions:member-contributions")
    
    mcs = MemberContribution.objects.filter(is_paid__in=[PaymentStatus.PENDING, PaymentStatus.NOT_PAID]).order_by('-created')
    context['contributions'] = mcs
    return render(request, "payments/log-payments.html", context)

@login_required
def log_payment(request, id):
    """
    Treasurer-only view to manually log/record a payment for a member contribution.
    Auto-sends confirmation email to member and marks contribution as PAID.
    """
    # Only treasurers can log payments
    if request.user.role != Role.TREASURER and not request.user.is_staff:
        messages.error(request, "Only treasurers can log payments.")
        return redirect("contributions:member-contributions")

    member_contribution = get_object_or_404(MemberContribution, id=id)
    contribution_type = member_contribution.contribution_type

    if request.method == "POST":
        form = LogPaymentForm(request.POST, request.FILES, treasurer=request.user)
        if form.is_valid():
            try:
                with transaction.atomic():
                    payment = form.save(commit=False)
                    payment.account = member_contribution.account
                    payment.recorded_by = request.user  # treasurer who logged it
                    payment.member_contribution = member_contribution
                    payment.reference = member_contribution.reference
                    payment.is_approved = LogPaymentStatus.PENDING  # Require approval
                    payment.save()
                    payment.update_member_contribution_status(PaymentStatus.PENDING)

                    logger.info(
                        "Payment logged by treasurer %s for %s: R%.2f (%s)",
                        request.user.username,
                        member_contribution.account.username,
                        member_contribution.amount_due,
                        payment.payment_method,
                    )

                # Queue confirmation email to member (non-blocking)
                async_task(
                    "contributions.tasks.send_payment_confirmation_task",
                    member_contribution.pk,
                    request.user.get_full_name() or request.user.username,
                )

                messages.success(
                    request,
                    f"Payment of R{member_contribution.amount_due:.2f} for {contribution_type.name} "
                    f"has been recorded. Awaiting approval. Confirmation email sent to {member_contribution.account.email}."
                )
                return redirect("contributions:member-contribution", id=member_contribution.id)

            except Exception as e:
                logger.exception("Failed to log payment for contribution %s", id)
                messages.error(request, "An error occurred while logging payment. Please try again.")
        else:
            logger.warning("LogPaymentForm validation failed: %s", form.errors)
            messages.error(request, "Please fix the errors below.")

    else:
        form = LogPaymentForm(treasurer=request.user, initial={
            "contribution_type": contribution_type,
            "member_contribution": member_contribution,
            "amount": member_contribution.amount_due,
            "reference": member_contribution.reference
        })

    context = {
        "contribution_type": contribution_type,
        "member_contribution": member_contribution,
        "form": form,
        "is_log_payment": True,
    }
    return render(request, "payments/log-payment.html", context)
