from django.db import models
from django.urls import reverse
from django.utils import timezone
from django.dispatch import receiver
from django.template.defaultfilters import slugify
from django.utils.safestring import mark_safe
from django.utils.translation import gettext as _
from django.contrib.auth.models import AbstractUser
from django.db.models.signals import pre_delete, post_save
from django.db.models import Sum
from django.contrib.auth import get_user_model
from django.core.exceptions import PermissionDenied
from accounts.utils.file_handlers import handle_profile_upload
from utilities.abstracts import AbstractCreate, AbstractProfile
from utilities.choices import PaymentStatus


class KgotlaExpense(AbstractCreate):
    title = models.CharField(help_text=_('Enter expense title e.g. Venue Rental'), max_length=300)
    description = models.TextField(help_text=_('Enter a brief description of the expense'), blank=True, null=True)
    amount = models.DecimalField(help_text=_('Enter the total amount for this expense'), max_digits=12, decimal_places=2)
    incurred_by = models.ForeignKey(
        get_user_model(),
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="incurred_expenses"
    )
    incurred_on = models.DateField(help_text=_('Select the date when the expense was incurred'), default=timezone.now)
    
    def __str__(self):
        return f"{self.title} - R{self.amount}"
    
    class Meta:
        verbose_name = _("Kgotla Expense")
        verbose_name_plural = _("Kgotla Expenses")
        ordering = ["-incurred_on", "-created"]

class KgotlaBalance(AbstractCreate):
    title = models.CharField(help_text=_('Enter balance title e.g General Fund Balance'), max_length=300, unique=True)
    slug = models.SlugField(max_length=400, unique=True, db_index=True)
    balance = models.DecimalField(help_text=_('Enter current balance amount'), max_digits=12, decimal_places=2, default=0)
    updated_by = models.ForeignKey(
        get_user_model(),
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="updated_kgotla_balances"
    )
    updated = models.DateTimeField(auto_now=True)
    created = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.title}: R{self.balance}"
    
    class Meta:
        verbose_name = _("Kgotla Balance")
        verbose_name_plural = _("Kgotla Balances")
        ordering = ["-updated"]
    
    def get_full_balance(self):
        return f"R{self.balance:,.2f}"
    
    def get_total_balance(self):
        from contributions.models import MemberContribution
        total_contributions = MemberContribution.objects.filter(is_paid=PaymentStatus.PAID).aggregate(total=Sum("amount_due"))["total"] or 0
        return self.balance + total_contributions
    
    def update_balance(self, amount, user=None, opt="add"):
        if opt == "add":
            self.balance += amount
        elif opt == "subtract":
            self.balance -= amount
        else:
            raise ValueError("Invalid operation for update_balance. Use 'add' or 'subtract'.")
        if user:
            self.updated_by = user
        self.save()
    
    def save(self, *args, **kwargs):
        # Generate slug on creation
        
        base = slugify(self.title) or "kgotla-balance"
        slug = base
        counter = 1
        while KgotlaBalance.objects.filter(slug=slug).exists():
            slug = f"{base}-{counter}"
            counter += 1
        self.slug = slug
        super(KgotlaBalance, self).save(*args, **kwargs)