import logging
from django.contrib import admin, messages
from django.utils.html import format_html
from django.urls import reverse
from django.db.models import Sum
from django.utils.translation import gettext_lazy as _

from contributions.models import ContributionType, MemberContribution, Payment, SMSLog

logger = logging.getLogger("contributions.admin")

@admin.register(ContributionType)
class ContributionTypeAdmin(admin.ModelAdmin):
    list_display = ("name", "amount", "recurrence", "due_date", "scope", "is_active", "created_by", "created")
    list_filter = ("recurrence", "scope", "is_active", "created")
    search_fields = ("name", "description")
    prepopulated_fields = {"slug": ("name",)}
    readonly_fields = ("created", "updated", "created_by")
    
    fieldsets = (
        (_("Basic Info"), {
            "fields": ("name", "slug", "description", "amount")
        }),
        (_("Schedule"), {
            "fields": ("recurrence", "due_date", "scope", "family")
        }),
        (_("Status"), {
            "fields": ("is_active",)
        }),
        (_("Audit"), {
            "fields": ("created_by", "created", "updated"),
            "classes": ("collapse",)
        }),
    )

    def save_model(self, request, obj, form, change):
        if not change:
            obj.created_by = request.user
        super().save_model(request, obj, form, change)
        if not change:
            messages.success(
                request,
                f"✓ Contribution '{obj.name}' created. Automatically created contributions for all eligible members."
            )
            logger.info(
                "ContributionType created: %s (slug: %s) by %s",
                obj.name, obj.slug, request.user.username
            )

@admin.register(MemberContribution)
class MemberContributionAdmin(admin.ModelAdmin):
    def account_link(self, obj):
        """Link to member profile."""
        url = reverse("admin:accounts_account_change", args=[obj.account.id])
        return format_html('<a href="{}">{}</a>', url, obj.account.get_full_name())
    account_link.short_description = _("Member")

    def amount_due_display(self, obj):
        """Display amount in currency format."""
        return format_html("<strong>R{}</strong>", obj.amount_due)
    amount_due_display.short_description = _("Amount Due")

    def due_date_display(self, obj):
        """Highlight overdue items."""
        from django.utils import timezone
        is_overdue = obj.due_date < timezone.now().date() and obj.is_paid != "PAID"
        if is_overdue:
            return format_html('<span style="color:red;font-weight:bold;">{} (OVERDUE)</span>', obj.due_date)
        return obj.due_date
    due_date_display.short_description = _("Due Date")

    def status_badge(self, obj):
        """Display payment status as badge."""
        colors = {
            "PAID": "#10b981",
            "PENDING": "#f59e0b",
            "NOT_PAID": "#ef4444",
        }
        color = colors.get(obj.is_paid, "#6b7280")
        return format_html(
            '<span style="background-color:{}; color:white; padding:4px 8px; border-radius:4px; font-weight:bold;">{}</span>',
            color,
            obj.get_is_paid_display()
        )
    status_badge.short_description = _("Status")
    
    list_display = (
        "reference",
        "account_link",
        "contribution_type",
        "amount_due_display",
        "due_date_display",
        "status_badge",
        "created"
    )
    list_filter = ("is_paid", "due_date", "contribution_type", "created")
    search_fields = ("account__username", "account__first_name", "account__last_name", "reference")
    readonly_fields = ("created", "updated", "reference")
    date_hierarchy = "due_date"

    fieldsets = (
        (_("Member & Contribution"), {
            "fields": ("account", "contribution_type", "reference")
        }),
        (_("Payment Details"), {
            "fields": ("amount_due", "due_date", "is_paid")
        }),
        (_("Audit"), {
            "fields": ("created", "updated"),
            "classes": ("collapse",)
        }),
    )

@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    def account_link(self, obj):
        """Link to member profile."""
        url = reverse("admin:accounts_account_change", args=[obj.account.id])
        return format_html('<a href="{}">{}</a>', url, obj.account.get_full_name())
    account_link.short_description = _("Member")

    def amount_display(self, obj):
        """Display amount in currency format."""
        return format_html("<strong>R{}</strong>", obj.amount)
    amount_display.short_description = _("Amount")

    def approval_badge(self, obj):
        """Display approval status as badge."""
        colors = {
            "APPROVED": "#10b981",
            "PENDING": "#f59e0b",
            "REJECTED": "#ef4444",
        }
        color = colors.get(obj.is_approved, "#6b7280")
        return format_html(
            '<span style="background-color:{}; color:white; padding:4px 8px; border-radius:4px; font-weight:bold;">{}</span>',
            color,
            obj.get_is_approved_display()
        )
    approval_badge.short_description = _("Status")

    def proof_preview(self, obj):
        """Preview proof of payment."""
        if obj.proof_of_payment:
            if obj.proof_of_payment.name.lower().endswith('.pdf'):
                return format_html(
                    '<a href="{}" target="_blank">📄 View PDF</a>',
                    obj.proof_of_payment.url
                )
            else:
                return format_html(
                    '<img src="{}" style="max-width:300px; max-height:200px;" />',
                    obj.proof_of_payment.url
                )
        return _("No proof attached")
    proof_preview.short_description = _("Proof of Payment")

    def approve_payment(self, request, queryset):
        """Bulk approve payments."""
        updated = 0
        for payment in queryset.filter(is_approved="PENDING"):
            payment.approve_payment(request.user)
            updated += 1
        
        if updated:
            self.message_user(
                request,
                f"✓ {updated} payment(s) approved successfully.",
                messages.SUCCESS
            )
            logger.info("%s approved %d payments", request.user.username, updated)
        else:
            self.message_user(request, "No pending payments to approve.", messages.WARNING)

    approve_payment.short_description = _("✓ Approve selected payments")

    def reject_payment(self, request, queryset):
        """Bulk reject payments."""
        updated = queryset.filter(is_approved="PENDING").update(is_approved="REJECTED")
        if updated:
            self.message_user(
                request,
                f"✗ {updated} payment(s) rejected.",
                messages.SUCCESS
            )
            logger.warning("%s rejected %d payments", request.user.username, updated)

    reject_payment.short_description = _("✗ Reject selected payments")
    list_display = (
        "reference",
        "account_link",
        "amount_display",
        "payment_method",
        "approval_badge",
        "recorded_by",
        "payment_date"
    )
    list_filter = ("is_approved", "payment_method", "payment_date", "payment_verified_date")
    search_fields = ("reference", "account__username", "account__first_name", "receipt")
    readonly_fields = (
        "payment_date",
        "created",
        "updated",
        "payment_verified_by",
        "payment_verified_date",
        "proof_preview"
    )
    date_hierarchy = "payment_date"
    
    fieldsets = (
        (_("Payment Info"), {
            "fields": ("reference", "account", "amount", "payment_method")
        }),
        (_("Receipt & Proof"), {
            "fields": ("receipt", "proof_of_payment", "proof_preview")
        }),
        (_("Related Contribution"), {
            "fields": ("member_contribution", "contribution_type")
        }),
        (_("Approval Status"), {
            "fields": ("is_approved", "rejection_reason", "payment_verified_by", "payment_verified_date"),
            "description": "Review and approve/reject payments here"
        }),
        (_("Recorded By"), {
            "fields": ("recorded_by", "payment_date")
        }),
        (_("Audit"), {
            "fields": ("created", "updated"),
            "classes": ("collapse",)
        }),
    )

    

    actions = ["approve_payment", "reject_payment"]

    def save_model(self, request, obj, form, change):
        """Track who approves payments."""
        if not change:
            obj.recorded_by = request.user
        super().save_model(request, obj, form, change)
        if change and "is_approved" in form.changed_data:
            logger.info(
                "Payment %s approval status changed to %s by %s",
                obj.reference,
                obj.is_approved,
                request.user.username
            )


@admin.register(SMSLog)
class SMSLogAdmin(admin.ModelAdmin):
    list_display = (
        "phone_number",
        "status",
        "created",
        "sent_at",
    )
    list_filter = ("status",)
    search_fields = ("phone_number", "message")
    readonly_fields = (
        "provider_response",
        "error_message",
    )