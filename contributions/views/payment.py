import logging, requests, json
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db import transaction
from django.urls import reverse
from django_q.tasks import async_task
from django.conf import settings
from django_q.tasks import async_task
from contributions.tasks import send_payment_confirmation_task
from contributions.utils.yoco_funcs import decimal_to_str, headers
from utilities.choices import LogPaymentStatus, PaymentMethod, PaymentStatus, Role
from ..models import ContributionType, MemberContribution, Payment

logger = logging.getLogger("payments")

def update_payment_status(payment: Payment, status: str):
    """Update payment and associated member contribution status."""
    with transaction.atomic():
        payment.is_approved = status
        payment.save(update_fields=["is_approved"])
        if payment.member_contribution:
            payment.update_member_contribution_status(
                PaymentStatus.PAID if status == LogPaymentStatus.APPROVED else PaymentStatus.NOT_PAID
            )
            

@login_required
def yoco_checkout(request, payment_id):
    """
    Yoco payment page. Build checkout UI and handle Yoco API calls.
    Yoco will callback to yoco_callback on success/failure.
    """
    payment = get_object_or_404(Payment, id=payment_id, account=request.user)
    member_contribution = payment.member_contribution

    if not member_contribution:
        messages.error(request, "Invalid payment record.")
        return redirect("contributions:member-contributions")
    
    if request.method == 'POST':
        success_url = request.build_absolute_uri(reverse("contributions:payment-success", kwargs={"payment_id": member_contribution.id}))
        cancel_url = request.build_absolute_uri(reverse("contributions:payment-cancelled", kwargs={"payment_id": member_contribution.id}))
        fail_url = request.build_absolute_uri(reverse("contributions:payment-failed", kwargs={"payment_id": member_contribution.id}))
        str_amount = decimal_to_str(payment.amount)
        
        lineitems = [
            {
                "displayName": payment.member_contribution.get_name(),
                "quantity": 1,
                "pricingDetails": {
                        "price": int(str_amount)
                    }
            }
        ]
        session_data = {
            'successUrl': success_url,
            'cancelUrl': cancel_url,
            "failureUrl": fail_url,
            'amount': int(str_amount),
            'currency': 'ZAR',
            'metadata': {
                "checkoutId": f"{payment.reference}"
            },
            "lineItems": lineitems

        }
        
        data = json.dumps(session_data)
        try:
            response = requests.request("POST", "https://payments.yoco.com/api/checkouts", data=data, headers=headers)
            response.raise_for_status()
            response_data = response.json()
            payment.checkout_id = response_data["id"]
            payment.is_approved = LogPaymentStatus.PENDING
            payment.save(update_fields=["is_approved", "checkout_id"])
            payment.update_member_contribution_status(PaymentStatus.PENDING)
            return redirect(response_data["redirectUrl"])

        except requests.ConnectionError as err:
            messages.error(request, "There was a connection error while processing your payment. Please try again later.")
            logger.error(f"Yoco - {err}")
            return redirect("contributions:checkout", id=member_contribution.id)
        
        except requests.HTTPError as err:
            logger.error(f"Yoco - {err}")
            messages.error(request, "There was an error processing your payment. Please try again later.")
            return redirect("contributions:checkout", id=member_contribution.id)
        
        except Exception as err:
            logger.error(f"Yoco - {err}")
            print(err)
            messages.error(request, "An unexpected error occurred. Please try again later.")
            return redirect("contributions:checkout", id=member_contribution.id)
            

    context = {
        "payment": payment,
        "mc": member_contribution,
    }
    return render(request, "payments/yoco-payment.html", context)


@login_required
def yoco_callback(request):
    """
    Yoco callback endpoint. Handle success/failure response from Yoco.
    Yoco will POST transactionId, status, etc. Verify and update Payment record.
    """
    import hmac
    import hashlib

    try:
        yoco_transaction_id = request.POST.get("transactionId")
        yoco_status = request.POST.get("status", "").lower()  # e.g., "success", "failed"
        yoco_signature = request.POST.get("signature")

        if not yoco_transaction_id or not yoco_status:
            logger.warning("Yoco callback missing transactionId or status")
            return render(request, "payments/yoco-callback-error.html", {"error": "Invalid callback data"}, status=400)

        # Verify Yoco signature (optional but recommended)
        secret = getattr(settings, "YOCO_SECRET_KEY", "")
        if secret and yoco_signature:
            expected_sig = hmac.new(
                secret.encode(),
                f"{yoco_transaction_id}{yoco_status}".encode(),
                hashlib.sha256
            ).hexdigest()
            if not hmac.compare_digest(yoco_signature, expected_sig):
                logger.error("Yoco callback signature mismatch for %s", yoco_transaction_id)
                return render(request, "payments/yoco-callback-error.html", {"error": "Signature verification failed"}, status=403)

        # Find payment by transaction reference (or query Yoco API to confirm)
        payment = Payment.objects.filter(payment_method_masked_card=yoco_transaction_id).first()
        if not payment:
            logger.warning("Yoco callback: no matching payment for transaction %s", yoco_transaction_id)
            return render(request, "payments/yoco-callback-error.html", {"error": "Payment not found"}, status=404)

        with transaction.atomic():
            if yoco_status == "success":
                payment.payment_method_masked_card = yoco_transaction_id
                payment.save()
                if payment.member_contribution:
                    payment.update_member_contribution_status(PaymentStatus.PAID)
                logger.info("Yoco payment successful for %s (txn: %s)", payment.account.username, yoco_transaction_id)
                messages.success(request, f"Payment of R{payment.member_contribution.amount_due:.2f} completed successfully!")
                return redirect("contributions:member-contribution", id=payment.member_contribution.id)
            else:
                payment.payment_method_masked_card = yoco_transaction_id
                if payment.member_contribution:
                    payment.update_member_contribution_status(PaymentStatus.NOT_PAID)
                payment.save()
                logger.warning("Yoco payment failed for %s (txn: %s, status: %s)", payment.account.username, yoco_transaction_id, yoco_status)
                messages.error(request, "Payment failed. Please try again or contact support.")
                return redirect("contributions:checkout", id=payment.member_contribution.id)

    except Exception as e:
        logger.exception("Yoco callback error")
        return render(request, "payments/yoco-callback-error.html", {"error": "An error occurred"}, status=500)

def payment_success(request, payment_id):
    messages.success(request, "Your payment was successful!")
    member_contribution = get_object_or_404(MemberContribution, id=payment_id)
    payment: Payment = member_contribution.payment
    payment.is_approved = LogPaymentStatus.APPROVED
    payment.save(update_fields=["is_approved"])
    payment.update_member_contribution_status(PaymentStatus.PAID)
    async_task(
        "contributions.tasks.send_payment_confirmation_task", member_contribution.pk,
        request.user.get_full_name() or request.user.username,
    )
    return redirect("contributions:member-contribution", id=member_contribution.id)

def payment_cancelled(request, payment_id):
    messages.warning(request, "Your payment was cancelled.")
    member_contribution = get_object_or_404(MemberContribution, id=payment_id)
    
    payment: Payment = member_contribution.payment
    payment.is_approved = LogPaymentStatus.REJECTED
    payment.update_member_contribution_status(PaymentStatus.CANCELLED)
    payment.save(update_fields=["is_approved"])
    return redirect("contributions:checkout", id=payment_id)

def payment_failed(request, payment_id):
    member_contribution = get_object_or_404(MemberContribution, id=payment_id)
    
    payment: Payment = member_contribution.payment
    payment.update_member_contribution_status(PaymentStatus.NOT_PAID)
    payment.is_approved = LogPaymentStatus.NOT_PAID
    payment.save(update_fields=["is_approved"])
    messages.error(request, "Your payment failed. Please try again.")
    return redirect("contributions:checkout", id=payment_id)