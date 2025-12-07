from django.db import models
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from django.utils.text import slugify
from accounts.models import Family
from django.contrib.auth import get_user_model
from django.db.models import Sum
import random, uuid
from django.utils.crypto import get_random_string
from django.db import transaction

from utilities.abstracts import AbstractCreate, AbstractPayment
from utilities.choices import SCOPE_CHOICES,  LogPaymentStatus, PaymentMethod, PaymentStatus, Recurrence


class ContributionType(AbstractCreate):
    class Category(models.TextChoices):
        EVENT = 'event', _('Event / Celebration')
        BURIAL = 'burial', _('Burial / Funeral Fund')
        SAVINGS = 'savings', _('Savings / Stokvel')
        INVESTMENT = 'investment', _('Investment Fund')
        BUSINESS = 'business', _('Business or Income Project')
        HOLIDAY = 'holiday', _('Holiday / Travel Fund')
        GROCERY = 'grocery', _('Grocery / Monthly Food Club')
        EMERGENCY = 'emergency', _('Emergency Support')
        EDUCATION = 'education', _('Education or Skills Fund')
        OTHER = 'other', _('Other')
        
    name = models.CharField(
        max_length=100,
        help_text=_("Enter contribution name (e.g. Kgotla Monthly Fee or Kgotla Funeral Fund)"),
    )
    slug = models.SlugField(max_length=150, unique=True, blank=True)
    description = models.TextField(blank=True, null=True)
    category = models.CharField(
        max_length=50,
        choices=Category.choices,
        default=Category.OTHER,
        help_text=_("Select the contribution category (e.g. Burial, Savings, Event)"),
    )
    family = models.ForeignKey(Family, on_delete=models.SET_NULL, null=True, blank=True, related_name='family_contribution_types', help_text=_('Select family if this contribution is only for specific family'))
    amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        help_text=_("Default amount to be contributed for this type"),
    )
    recurrence = models.CharField(
        max_length=20,
        choices=Recurrence.choices,
        default=Recurrence.ONCE_OFF,
        help_text=_("Specify if this contribution is once-off, monthly, or annual"),
    )
    scope = models.CharField(max_length=20, choices=SCOPE_CHOICES.choices, default=SCOPE_CHOICES.CLAN, help_text=_("Specify if this contribution is Entire Kgotla, Family leader only, or specific family"),)
    due_date = models.DateField(blank=True, null=True, help_text=_("For Annual and Once-off contributions"))
    created_by = models.ForeignKey(
        get_user_model(),
        on_delete=models.SET_NULL,
        null=True,
        related_name="created_contributions",
    )
    is_active = models.BooleanField(default=True)
    

    class Meta:
        verbose_name = _("Contribution Type")
        verbose_name_plural = _("Contribution Types")
        ordering = ["-created"]

    def __str__(self):
        return f"{self.name} ({self.get_category_display()})"

    def save(self, *args, **kwargs):
        # ensure unique slug (append counter when needed)
        base = slugify(self.name) or "contribution"
        if not self.slug or slugify(self.slug) != base:
            slug = base
            counter = 1
            while ContributionType.objects.filter(slug=slug).exclude(pk=getattr(self, "pk", None)).exists():
                slug = f"{base}-{counter}"
                counter += 1
            self.slug = slug
        super().save(*args, **kwargs)
        
    def clean(self):
        """
        Enforce family selection when scope is 'family',
        and ensure family is None for other scopes.
        """
        from django.core.exceptions import ValidationError

        if self.scope == SCOPE_CHOICES.FAMILY and not self.family:
            raise ValidationError("A family must be selected when scope is 'Specific Family'.")

        if self.scope != SCOPE_CHOICES.FAMILY and self.family is not None:
            raise ValidationError("Family should only be set for 'Specific Family' scope.")
            
    @property
    def total_collected(self):
        from .models import Payment 
        result = Payment.objects.filter(contribution_type=self).aggregate(total=Sum("amount"))
        return result["total"] or 0
    
    def get_absolute_url(self):
        return reverse("contributions:get-contribution", kwargs={"contribution_slug": self.slug})
    
    def get_update_url(self):
        return reverse("contributions:update-contribution", kwargs={"contribution_slug": self.slug})

    def get_delete_url(self):
        return reverse("contributions:delete-contribution", kwargs={"contribution_slug": self.slug})
    

class MemberContribution(AbstractCreate):
    
    account = models.ForeignKey(get_user_model(), on_delete=models.CASCADE, related_name="member_contributions")
    contribution_type = models.ForeignKey(ContributionType, on_delete=models.CASCADE, related_name="member_contributions")
    amount_due = models.DecimalField(max_digits=10, decimal_places=2)
    reference = models.CharField(max_length=100, blank=True, null=True, help_text=_("Receipt or transaction reference"), unique=True)
    due_date = models.DateField(blank=True, null=True)
    is_paid = models.CharField(max_length=100, choices=PaymentStatus.choices, default=PaymentStatus.NOT_PAID, db_index=True)
    

    class Meta:
        verbose_name = _("Member Contribution")
        verbose_name_plural = _("Member Contributions")
        unique_together = ('account', 'contribution_type', 'due_date')
        ordering = ["-created"]

    def __str__(self):
        return f"{self.account.get_full_name()} - {self.contribution_type.name} (R{self.amount_due})"
    
    def get_name(self):
        return f"{self.contribution_type.name} - R{self.amount_due}"

    @property
    def balance(self):
        # consistent calculation using DB aggregation
        result = self.payments.aggregate(total=Sum("amount"))
        total_paid = result.get("total") or 0
        return self.amount_due - total_paid
    
    @property
    def is_overdue(self):
        from django.utils import timezone
        if self.is_paid != PaymentStatus.PAID and self.due_date and self.due_date < timezone.now().date():
            return True
        return False
    
    def save(self, *args, **kwargs):
        # reference has default UUID; ensure not overwritten on update
        super().save(*args, **kwargs)
        
    def get_absolute_url(self):
        return reverse("contributions:member-contribution", kwargs={"id": self.id})
    
    get_payments_url = lambda self: reverse("contributions:checkout", kwargs={"id": self.id})


class Payment(AbstractCreate, AbstractPayment):
    
        
    checkout_id = models.CharField(
        max_length=200,
        unique=True,
        null=True,
        blank=True,
        db_index=True
    )
    account = models.ForeignKey(
        get_user_model(),
        on_delete=models.CASCADE,
        related_name="payments"
    )

    member_contribution = models.OneToOneField(
        MemberContribution,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="payment"
    )
    payment_method = models.CharField(
        max_length=20,
        choices=PaymentMethod.choices,
        default=PaymentMethod.CASH
    )
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    reference = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        help_text=_("Receipt or transaction reference")
    )
    receipt = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        help_text=_("Receipt number from bank/payment provider")
    )
    proof_of_payment = models.FileField(
        upload_to="payments/proof/",
        blank=True,
        null=True,
        help_text=_("Upload bank statement, screenshot, or receipt image")
    )
    payment_date = models.DateField(auto_now_add=True)
    recorded_by = models.ForeignKey(
        get_user_model(),
        on_delete=models.SET_NULL,
        null=True,
        related_name="recorded_payments",
        help_text=_("Treasurer or admin who logged this payment")
    )
    is_approved = models.CharField(
        max_length=20,
        choices=LogPaymentStatus.choices,
        default=LogPaymentStatus.PENDING,
        help_text=_("Payment verification status"),
        db_index=True
    )
    payment_verified_by = models.ForeignKey(
        get_user_model(),
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="verified_payments",
        help_text=_("Admin/treasurer who verified/approved payment")
    )
    payment_verified_date = models.DateTimeField(
        null=True,
        blank=True,
        help_text=_("When payment was verified")
    )
    rejection_reason = models.TextField(
        blank=True,
        null=True,
        help_text=_("Reason if payment was rejected")
    )

    class Meta:
        verbose_name = _("Payment")
        verbose_name_plural = _("Payments")
        ordering = ["-payment_date"]
        indexes = [
            models.Index(fields=["account", "-payment_date"]),
            models.Index(fields=["is_approved", "payment_date"]),
        ]

    def __str__(self):
        return f"{self.account.get_full_name()} - R{self.amount} ({self.get_is_approved_display()})"

    def get_absolute_url(self):
        return reverse("admin:contributions_payment_change", args=[self.id])

    def approve_payment(self, approved_by, rejection_reason=None):
        """Approve or reject payment."""
        from django.utils import timezone

        if rejection_reason:
            self.is_approved = LogPaymentStatus.REJECTED
            self.rejection_reason = rejection_reason
        else:
            self.is_approved = LogPaymentStatus.APPROVED
            self.rejection_reason = None

        self.payment_verified_by = approved_by
        self.payment_verified_date = timezone.now()
        self.save()

        # Update member contribution status if approved
        if self.is_approved == LogPaymentStatus.APPROVED and self.member_contribution:
            self.update_member_contribution_status(PaymentStatus.PAID)

    def update_member_contribution_status(self, status):
         """Automatically update member contribution payment status."""
         if not self.member_contribution:
             return

         self.member_contribution.is_paid = status
         self.member_contribution.save(update_fields=['is_paid'])

    def save(self, *args, **kwargs):
        import logging
        logger = logging.getLogger("contributions")

        # Validate proof_of_payment if treasurer is recording
        if self.recorded_by and not self.pk:
            if self.recorded_by.role == "TREASURER" and not self.proof_of_payment:
                raise ValueError("Proof of payment is required when treasurer logs a payment.")

        with transaction.atomic():
            super().save(*args, **kwargs)

            if self.member_contribution:
                # One-to-one logic: only THIS payment affects the status
                if self.is_approved == LogPaymentStatus.APPROVED:
                    total_paid = self.amount
                else:
                    total_paid = 0

                # Determine new status
                if total_paid >= self.member_contribution.amount_due:
                    new_status = PaymentStatus.PAID
                elif total_paid > 0:
                    new_status = PaymentStatus.PARTIALLY_PAID
                else:
                    new_status = PaymentStatus.AWAITING_APPROVAL

                # Save only if status changed
                if self.member_contribution.is_paid != new_status:
                    self.member_contribution.is_paid = new_status
                    self.member_contribution.save(update_fields=["is_paid"])

                logger.info(
                    "Payment %s saved; member contribution %s status updated to %s",
                    self.id,
                    self.member_contribution.id,
                    new_status
                )



