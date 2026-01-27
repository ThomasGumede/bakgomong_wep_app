from celery import shared_task
from datetime import timedelta
from django.utils import timezone
from django.conf import settings
from django.template.loader import get_template, render_to_string
from django.utils.html import strip_tags
from django.core.mail import EmailMultiAlternatives
from django_q.tasks import async_task
from django.core.files.base import ContentFile
from weasyprint import HTML
from io import BytesIO

from contributions.models import MemberContribution, Payment
from contributions.utils.notifications import send_sms_via_smsportal, send_sms_via_bulksms
import logging, base64

from utilities.choices import PaymentStatus

logger = logging.getLogger('tasks')


def send_contribution_created_notification_task(mc_ids):

    contributions = MemberContribution.objects.filter(id__in=mc_ids).select_related("account", "contribution_type")
    for mc in contributions:
        try:
            send_contribution_created_notification(mc)
        except Exception:
            logger.exception("Notification failed for MemberContribution %s", mc.id)

    logger.info("Completed batch notification for %d contributions", len(mc_ids))


def send_contribution_created_notification(mc: MemberContribution):
    """
    Send a contribution notification email to a member
    when a MemberContribution is created.

    Safe for async job queues (Django-Q, Celery, Huey).
    """

    member = mc.account
    contribution = mc.contribution_type

    # -------------------------------------
    # Validate email availability
    # -------------------------------------
    if not member or not member.email:
        logger.warning(
            "Skipping contribution notification %s: member has no email",
            mc.id
        )
        return False

    # -------------------------------------
    # Build URLs safely
    # -------------------------------------
    base_url = getattr(settings, "SITE_URL", "").rstrip("/")

    payment_url = f"{base_url}/payment/checkout/{mc.id}"
    contr_url = f"{base_url}/contribution/{contribution.slug}"

    # -------------------------------------
    # Prepare email content
    # -------------------------------------
    try:
        context = {
            "user": member.get_full_name() or member.username,
            "contribution_name": contribution.name,
            "amount": mc.amount_due,
            "due_date": mc.due_date,
            "reference": mc.reference,
            "payment_url": payment_url,
            "contr_url": contr_url,
        }

        html_content = render_to_string("emails/contribution-notification.html", context)
        text_content = strip_tags(html_content)

        # -------------------------------------
        # Configure email
        # -------------------------------------
        from_email = getattr(settings, "DEFAULT_FROM_EMAIL", "noreply@bakgomong.co.za")

        msg = EmailMultiAlternatives(
            subject=f"New Contribution: {contribution.name}",
            body=text_content,
            from_email=from_email,
            to=[member.email],
        )
        msg.attach_alternative(html_content, "text/html")

        # -------------------------------------
        # Send email
        # -------------------------------------
        msg.send()

        logger.info(
            "Contribution notification sent to %s (MC %s)",
            member.email,
            mc.id,
        )
        
        # Send SMS notification if phone exists
        if member.phone:
            sms_message = (
                f"New contribution was created - {contribution.name} | "
                f"Amount: R{mc.amount_due:.2f} | "
                f"Due: {mc.due_date:%d %b %Y} | "
                f"Pay: {payment_url}"
            )
            try:
                success, response = send_sms_via_bulksms(member.phone, sms_message)
                if success:
                    logger.info("SMS notification sent to %s (MC %s)", member.phone, mc.id)
                else:
                    logger.warning("SMS notification failed for %s (MC %s): %s", member.phone, mc.id, response)
            except Exception:
                logger.exception("Failed to send SMS notification to %s", member.phone)
        return True

    except Exception:
        logger.exception(
            "Failed to send contribution notification for MemberContribution %s",
            mc.id
        )
        return False



def send_payment_reminder():
    """
    Daily task: Remind members 10 days before + on due date + 10 days after.
    Queue SMS + email reminders asynchronously.
    """
    today = timezone.now().date()

    # 10 days before deadline
    upcoming = MemberContribution.objects.filter(
        due_date=today + timedelta(days=10),
        is_paid=PaymentStatus.NOT_PAID
    ).select_related("account", "contribution_type")

    # On the due date
    due_today = MemberContribution.objects.filter(
        due_date=today,
        is_paid=PaymentStatus.NOT_PAID
    ).select_related("account", "contribution_type")

    # 10 days overdue
    overdue = MemberContribution.objects.filter(
        due_date=today - timedelta(days=10),
        is_paid=PaymentStatus.NOT_PAID
    ).select_related("account", "contribution_type")

    reminder_list = list(upcoming) + list(due_today) + list(overdue)

    for mc in reminder_list:
        contribution = mc.contribution_type
        member = mc.account

        if not member:
            logger.warning("MemberContribution %s has no associated member", mc.id)
            continue

        payment_url = f"{settings.SITE_URL}/contributions/{mc.id}/pay/"

        # Determine reminder type
        if mc.due_date == today + timedelta(days=10):
            subject_prefix = "⏰ Upcoming Payment Due"
            reminder_type = "upcoming"
        elif mc.due_date == today:
            subject_prefix = "📌 Payment Due Today"
            reminder_type = "due_today"
        else:
            subject_prefix = "⚠️ Payment Overdue"
            reminder_type = "overdue"

        # Send SMS if phone exists
        if member.phone:
            sms_message = (
                f"Reminder: {contribution.name}\n"
                f"Amount: R{mc.amount_due:.2f}\n"
                f"Due: {mc.due_date}\n"
                f"Pay: {payment_url}"
            )
            try:
                send_sms_via_smsportal(member.phone, sms_message)
                logger.info("SMS reminder sent to %s for %s", member.phone, mc.id)
            except Exception:
                logger.exception("Failed to send SMS reminder to %s", member.phone)

        # Send email
        if member.email:
            try:
                context = {
                    "user": member.get_full_name() or member.username,
                    "contribution_name": contribution.name,
                    "amount": mc.amount_due,
                    "due_date": mc.due_date,
                    "reference": mc.reference,
                    "payment_url": payment_url,
                    "reminder_type": reminder_type,
                }
                html_content = render_to_string("emails/payment-reminder.html", context)
                text_content = strip_tags(html_content)

                from_email = getattr(settings, "DEFAULT_FROM_EMAIL", "noreply@bakgomong.co.za")
                msg = EmailMultiAlternatives(
                    subject=f"{subject_prefix}: {contribution.name}",
                    body=text_content,
                    from_email=from_email,
                    to=[member.email],
                )
                msg.attach_alternative(html_content, "text/html")
                msg.send()
                logger.info("Payment reminder sent to %s for %s", member.email, mc.id)
            except Exception:
                logger.exception("Failed to send email reminder to %s", member.email)

    logger.info("Sent payment reminders: %d upcoming, %d due today, %d overdue",
                len(upcoming), len(due_today), len(overdue))
    return True


def send_payment_confirmation_task(member_contribution_id, treasurer_name):
    """
    Sends payment confirmation email + PDF invoice (WeasyPrint) 
    when treasurer logs payment.
    """
    try:
        mc = (
            MemberContribution.objects
            .select_related("account", "contribution_type")
            .prefetch_related("payment")
            .get(id=member_contribution_id)
        )
    except MemberContribution.DoesNotExist:
        logger.error("MemberContribution %s not found", member_contribution_id)
        return False

    member = mc.account
    if not member or not member.email:
        logger.warning("MemberContribution %s missing email", member_contribution_id)
        return False

    # Detect payment object correctly
    payment = Payment.objects.filter(member_contribution=mc).first()
    if not payment:
        logger.error("No Payment record found for MemberContribution %s", mc.id)
        return False

    try:
        # Render invoice HTML
        template = get_template("emails/invoice.html")
        html_string = template.render({"order": payment})

        # Generate PDF using WeasyPrint
        pdf_io = BytesIO()
        HTML(string=html_string).write_pdf(pdf_io)
        pdf_bytes = pdf_io.getvalue()

        # Save PDF to model FileField
        payment.proof_of_payment.save(
            f"invoice_{mc.id}.pdf",
            ContentFile(pdf_bytes),
            save=True
        )

        # Email context
        context = {
            "user": member.get_full_name() or member.username,
            "contribution_name": mc.contribution_type.name,
            "amount_paid": mc.amount_due,
            "treasurer_name": treasurer_name,
            "reference": mc.reference,
            "status": PaymentStatus(mc.is_paid).label,
            "payment_date": mc.updated.strftime("%d %B %Y"),
            "dashboard_link": f"{settings.SITE_URL}/member-invoice/{mc.id}",
        }

        html_content = render_to_string("emails/payment-confirmation.html", context)
        text_content = strip_tags(html_content)

        from_email = getattr(settings, "DEFAULT_FROM_EMAIL", "noreply@bakgomong.co.za")

        # Prepare email
        email = EmailMultiAlternatives(
            subject=f"✓ Payment Confirmed: {mc.contribution_type.name}",
            body=text_content,
            from_email=from_email,
            to=[member.email],
        )

        # Attach PDF correctly
        email.attach(
            f"invoice_{mc.id}.pdf",
            pdf_bytes,
            "application/pdf"
        )

        # HTML content
        email.attach_alternative(html_content, "text/html")

        # Send email
        email.send()
        logger.info("Payment confirmation sent to %s", member.email)
        return True

    except Exception:
        logger.exception("Failed to send payment confirmation for %s", member_contribution_id)
        return False

def send_bk_payment_details_task(member_contribution_id):
    """
    Sends payment details email + PDF invoice (WeasyPrint) 
    when treasurer logs payment.
    """
    try:
        mc = (
            MemberContribution.objects
            .select_related("account", "contribution_type")
            .prefetch_related("payment")
            .get(id=member_contribution_id)
        )
        mc.is_paid = PaymentStatus.AWAITING_APPROVAL
        mc.save(update_fields=['is_paid'])
    except MemberContribution.DoesNotExist:
        logger.error("MemberContribution %s not found", member_contribution_id)
        return False

    member = mc.account
    if not member or not member.email:
        logger.warning("MemberContribution %s missing email", member_contribution_id)
        return False

    # Detect payment object correctly
    payment = Payment.objects.filter(member_contribution=mc).first()
    if not payment:
        logger.error("No Payment record found for MemberContribution %s", mc.id)
        return False

    try:
        # Render invoice HTML
        template = get_template("emails/invoice.html")
        html_string = template.render({"order": payment})

        # Generate PDF using WeasyPrint
        pdf_io = BytesIO()
        HTML(string=html_string).write_pdf(pdf_io)
        pdf_bytes = pdf_io.getvalue()

        # Save PDF to model FileField
        payment.proof_of_payment.save(
            f"invoice_{mc.id}.pdf",
            ContentFile(pdf_bytes),
            save=True
        )

        # Email context
        context = {
            "mc": mc,
            "invoice_link": f"{settings.SITE_URL}/member-invoice/download/{mc.id}",
        }

        html_content = render_to_string("emails/payment-information.html", context)
        text_content = strip_tags(html_content)

        from_email = getattr(settings, "DEFAULT_FROM_EMAIL", "noreply@bakgomong.co.za")

        # Prepare email
        email = EmailMultiAlternatives(
            subject=f"✓ Payment Details: {mc.contribution_type.name}",
            body=text_content,
            from_email=from_email,
            to=[member.email],
        )

        # Attach PDF correctly
        email.attach(
            f"invoice_{mc.id}.pdf",
            pdf_bytes,
            "application/pdf"
        )

        # HTML content
        email.attach_alternative(html_content, "text/html")

        # Send email
        email.send()
        logger.info("Payment confirmation sent to %s", member.email)
        return True

    except Exception:
        logger.exception("Failed to send payment confirmation for %s", member_contribution_id)
        return False

def send_payment_details_task(obj_id, obj_type='contribution', treasurer_name=None):
    """
    Backwards-compatible wrapper for legacy django-q tasks that referenced
    `contributions.tasks.send_payment_details_task`.

    - obj_type='payment' expects a Payment id and will resolve its related
      MemberContribution before sending the confirmation.
    - obj_type='contribution' (default) treats obj_id as a MemberContribution id.

    Returns True on success, False otherwise.
    """
    try:
        logger.info("send_payment_details_task called: id=%s type=%s", obj_id, obj_type)
        if obj_type == 'payment':
            payment = Payment.objects.select_related('member_contribution', 'recorded_by').filter(id=obj_id).first()
            if not payment:
                logger.error("Payment %s not found", obj_id)
                return False
            mc = payment.member_contribution
            treasurer = treasurer_name or (payment.recorded_by.get_full_name() if payment.recorded_by else None)
            if not mc:
                logger.warning("Payment %s has no linked MemberContribution", obj_id)
                return False
            return send_payment_confirmation_task(mc.id, treasurer)
        else:
            # treat as MemberContribution id
            return send_payment_confirmation_task(obj_id, treasurer_name)
    except Exception as exc:
        logger.exception("send_payment_details_task failed for %s: %s", obj_id, exc)
        return False
