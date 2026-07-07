from django.db import models, transaction, IntegrityError
import uuid
from uuid import UUID
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
from accounts.models import Family
from accounts.utils.file_handlers import handle_profile_upload
from bakgomong_kgotla_yamalla.utils.calendar import google_calendar_url, office365_calendar_url, outlook_calendar_url
from utilities.abstracts import AbstractCreate
from django.core.exceptions import ValidationError
from utilities.choices import SCOPE_CHOICES, PaymentStatus, Recurrence, Role

SINGLETON_ID = UUID("00000000-0000-0000-0000-000000060121")
class SingletonModel(models.Model):
    class Meta:
        abstract = True

    def save(self, *args, **kwargs):
        # Only prevent creating another object
        if self._state.adding and self.__class__.objects.exists():
            raise ValidationError(
                f"Only one {self.__class__.__name__} instance is allowed."
            )

        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        raise ValidationError(
            f"{self.__class__.__name__} cannot be deleted."
        )

    @classmethod
    def load(cls):
        obj = cls.objects.first()
        if obj:
            return obj

        return cls.objects.create()


class KgotlaBalance(SingletonModel, AbstractCreate):
    title = models.CharField(help_text=_('Enter balance title e.g General Fund Balance'), max_length=300, unique=True, default="General Fund Balance")
    slug = models.SlugField(max_length=400, unique=True, db_index=True, default="general-fund-balance")
    balance = models.DecimalField(help_text=_('Enter current balance amount'), max_digits=12, decimal_places=2, default=0)
    bank_statement = models.FileField(help_text=_('Upload bank statement for this balance'), upload_to=handle_profile_upload, null=True, blank=True)
    updated_by = models.ForeignKey(
        get_user_model(),
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="updated_kgotla_balances"
    )
    
    def __str__(self):
        return f"{self.title}: R{self.balance}"
    
    class Meta:
        verbose_name = _("Kgotla Balance")
        verbose_name_plural = _("Kgotla Balances")
        ordering = ["-updated"]
    
    def get_full_balance(self):
        return f"R{self.balance:,.2f}"
    
    @property
    def total_contributions(self):
        from contributions.models import MemberContribution

        return (
            MemberContribution.objects.filter(
                is_paid=PaymentStatus.PAID
            )
            .aggregate(total=Sum("amount_due"))
            .get("total") or 0
        )
    
    
    def get_total_balance(self):
        total_contributions = self.total_contributions
        new_balance = self.balance + total_contributions
        return new_balance or 0
    
    def get_expenses_balance(self):
        from .models import KgotlaExpense
        total_expenses = KgotlaExpense.objects.aggregate(total=Sum("amount"))["total"] or 0
        return total_expenses or 0
    
    def get_total_balance_after_expenses(self):
        total_contributions = self.total_contributions
        total_expenses = self.get_expenses_balance()
        new_balance = self.balance + total_contributions - total_expenses
        if new_balance < 0:
            return mark_safe(f'<p class="text-red-600 font-bold text-lg">R{new_balance:,.2f} (-R{total_expenses:,.2f})</p>')
        return mark_safe(f'<p class="text-green-600 font-bold text-lg">R{new_balance:,.2f} (-R{total_expenses:,.2f})</p>')
    
    def get_total_other_balance_after_expenses(self):
        total_contributions = self.total_contributions
        total_expenses = self.get_expenses_balance()
        new_balance = self.balance + total_contributions - total_expenses
        if new_balance < 0:
            return mark_safe(f'''
                             <div
                                class="card shadow-none border border-gray-200 dark:border-neutral-600 dark:bg-neutral-700 rounded-lg h-full bg-gradient-to-r from-red-600/10 to-bg-white">
                                <div class="card-body p-5">
                                    <div class="flex flex-wrap items-center justify-between gap-3">
                                        <div>
                                            <p class="font-medium text-neutral-900 dark:text-white mb-1">Total Actual Balance</p>
                                            <h6 class="mb-0 dark:text-white">R{new_balance:,.2f}</h6>
                                        </div>
                                        <div class="w-[50px] h-[50px] bg-red-600 rounded-full flex justify-center items-center">
                                            <iconify-icon icon="fa6-solid:file-invoice-dollar" class="text-white text-2xl mb-0"></iconify-icon>
                                        </div>
                                    </div>
                                    <p class="font-medium text-sm text-neutral-600 dark:text-white mt-3 mb-0 flex items-center gap-2">
                                        <span class="inline-flex items-center gap-1 text-success-600 dark:text-success-400">Total balance after expenses</span>
                                        
                                    </p>
                                </div>
                            </div>
                             ''')
        return mark_safe(f'''
                         
                         <div
                            class="card shadow-none border border-gray-200 dark:border-neutral-600 dark:bg-neutral-700 rounded-lg h-full bg-gradient-to-r from-success-600/10 to-bg-white">
                            <div class="card-body p-5">
                                <div class="flex flex-wrap items-center justify-between gap-3">
                                    <div>
                                        <p class="font-medium text-neutral-900 dark:text-white mb-1">Total Actual Balance</p>
                                        <h6 class="mb-0 dark:text-white">R{new_balance:,.2f}</h6>
                                    </div>
                                    <div class="w-[50px] h-[50px] bg-success-600 rounded-full flex justify-center items-center">
                                        <iconify-icon icon="solar:wallet-bold" class="text-white text-2xl mb-0"></iconify-icon>
                                    </div>
                                </div>
                                <p class="font-medium text-sm text-neutral-600 dark:text-white mt-3 mb-0 flex items-center gap-2">
                                    <span class="inline-flex items-center gap-1 text-success-600 dark:text-success-400">Total balance after expenses</span>
                                </p>
                            </div>
                        </div>
                         ''')
    
    def save(self, *args, **kwargs):
        self.slug = slugify(self.title) or "kgotla-balance"
        super(KgotlaBalance, self).save(*args, **kwargs)
    
    class Meta:
        verbose_name = _("Update Kgotla Balance")
        verbose_name_plural = _("Update Kgotla Balance")
        ordering = ["-updated"]

class KgotlaExpense(AbstractCreate):
    title = models.CharField(help_text=_('Enter expense title e.g "Catering for Annual Meeting"'), max_length=300)
    slug = models.SlugField(max_length=400, unique=True, db_index=True)
    amount = models.DecimalField(help_text=_('Enter expense amount'), max_digits=12, decimal_places=2)
    description = models.TextField(help_text=_('Enter a description for this expense'), blank=True, null=True)
    added_by = models.ForeignKey(
        get_user_model(),
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="expenses_added"
    )
    incurred_date = models.DateTimeField(help_text=_('Date when the expense was incurred'), default=timezone.now)
    recurring = models.CharField(help_text=_('Indicates whether this is a recurring expense'), max_length=10, choices=Recurrence.choices,
        default=Recurrence.ONCE_OFF,)
    proof_of_expense = models.FileField(help_text=_('Upload proof of expense (e.g., receipt, invoice)'), upload_to=handle_profile_upload, null=True, blank=True)
    approved = models.BooleanField(help_text=_('Indicates whether this expense has been approved by the clan chairperson or secretary'), default=False)
    
    def __str__(self):
        return f"{self.title}: R{self.amount}"
    
    class Meta:
        verbose_name = _("Kgotla Expense")
        verbose_name_plural = _("Kgotla Expenses")
        ordering = ["-incurred_date"]
    
    def save(self, *args, **kwargs):
        # Generate slug on creation
        if not self.slug:
            base = slugify(self.title) or "kgotla-expense"
            slug = base
            counter = 1
            while KgotlaExpense.objects.filter(slug=slug).exists():
                slug = f"{base}-{counter}"
                counter += 1
            self.slug = slug
        
        super(KgotlaExpense, self).save(*args, **kwargs)
        self.update_kgotla_balance()
        
    def __str__(self):
        return f"{self.title} - R{self.amount:,.2f}"
    
    def update_kgotla_balance(self):
        from .models import KgotlaBalance
        try:
            balance = KgotlaBalance.objects.get(slug="general-fund-balance")
            balance.balance -= self.amount
            balance.save()
            
        except KgotlaBalance.DoesNotExist:
            pass  # Handle the case where the balance record doesn't exist (e.g., log an error)
        
    def get_total_expenses(self):
        total = KgotlaExpense.objects.aggregate(total=Sum("amount"))["total"] or 0
        return total
    
    def is_updater_admin_or_secretary(self, user):
        return getattr(user, "role", None) in [Role.CLAN_CHAIRPERSON, Role.SECRETARY] or user.is_superuser
        
class ClanDocument(AbstractCreate):
    class Visibility(models.TextChoices):
        CLAN = "clan", _("Entire Clan")
        FAMILY = "family", _("Specific Family")
        PRIVATE = "private", _("Private (Admin Only)")

    class Category(models.TextChoices):
        MINUTES = "minutes", _("Meeting Minutes")
        REPORT = "report", _("Financial / Contribution Report")
        EVENT = "event", _("Event Notice or Program")
        POLICY = "policy", _("Policy / Constitution")
        OTHER = "other", _("Other")

    title = models.CharField(max_length=255, help_text=_("Enter the document title"))
    slug = models.SlugField(max_length=300, unique=True, blank=True)
    description = models.TextField(blank=True, null=True)
    category = models.CharField(max_length=30, choices=Category.choices, default=Category.OTHER)
    file = models.FileField(upload_to="clan_documents/%Y/%m/")
    uploaded_by = models.ForeignKey(
        get_user_model(),
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="uploaded_documents"
    )
    family = models.ForeignKey(
        Family,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="documents",
        help_text=_("Optional: restrict this document to a specific family"),
    )
    visibility = models.CharField(
        max_length=20,
        choices=Visibility.choices,
        default=Visibility.CLAN,
        help_text=_("Who can access this document"),
    )

    class Meta:
        verbose_name = _("Kgotla Document")
        verbose_name_plural = _("Kgotla Documents")
        ordering = ["-created"]

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)
        super().save(*args, **kwargs)
        
    def clean(self):
        """
        Enforce family selection when scope is 'family',
        and ensure family is None for other scopes.
        """
        from django.core.exceptions import ValidationError

        if self.visibility ==self.Visibility.FAMILY and not self.family:
            raise ValidationError("A family must be selected when visibility is 'Specific Family'.")

        if self.visibility != self.Visibility.FAMILY and self.family is not None:
            raise ValidationError("Family should only be set for 'Specific Family' visibility.")

    # -----------------------------------------------
    # 🔐 ACCESS CONTROL LOGIC
    # -----------------------------------------------
    def user_has_access(self, user):
        """
        Determines if a given user can view/download this document.
        """
        # Unauthenticated users have no access
        if not user.is_authenticated:
            return False

        # Admins can access everything
        if getattr(user, "role", None) == Role.CLAN_CHAIRPERSON or user.is_superuser:
            return True

        # Clan-wide document
        if self.visibility == self.Visibility.CLAN:
            return True

        # Family-only document
        if self.visibility == self.Visibility.FAMILY:
            if self.family and user.family == self.family:
                return True
            return False

        # Private (Admin-only)
        if self.visibility == self.Visibility.PRIVATE:
            return False

        return False

    def ensure_user_has_access(self, user):
        """
        Raises PermissionDenied if user doesn't have access.
        Useful in views or API endpoints.
        """
        if not self.user_has_access(user):
            raise PermissionDenied(_("You do not have permission to access this document."))
        return True

    def file_name(self):
        return self.file.name.split('/')[-1]

class Meeting(AbstractCreate):
    class MeetingType(models.TextChoices):
        ONLINE = "online", _("Online Meeting")
        IN_PERSON = "in_person", _("Live / In-Person Meeting")

    title = models.CharField(max_length=150, help_text=_("Enter meeting title"))
    slug = models.SlugField(max_length=200, unique=True, blank=True)
    description = models.TextField(blank=True, null=True)
    meeting_type = models.CharField(
        max_length=20,
        choices=MeetingType.choices,
        default=MeetingType.IN_PERSON,
        help_text=_("Specify whether this meeting is online or in-person."),
    )
    meeting_venue = models.CharField(max_length=150, help_text=_("Meeting Venue for in-person meetings"), blank=True, null=True)
    meeting_link = models.URLField(
        blank=True,
        null=True,
        help_text=_("Link for online meetings (e.g., Zoom, Google Meet)."),
    )
    audience = models.CharField(
        max_length=30,
        choices=SCOPE_CHOICES.choices,
        default=SCOPE_CHOICES.CLAN,
        help_text=_("Specify who this meeting is for."),
    )
    meeting_date = models.DateTimeField(help_text=_("Start date and time of the meeting"))
    meeting_end_date = models.DateTimeField(help_text=_("End date and time of the meeting"))
    created_by = models.ForeignKey(
        get_user_model(),
        on_delete=models.SET_NULL,
        null=True,
        related_name="meetings_created",
        help_text=_("User who created this meeting"),
    )
    family = models.ForeignKey(
        Family,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="meetings",
        help_text=_("Optional: assign this meeting to a specific family if needed."),
    )
    meeting_status = models.CharField(
        max_length=20,
        choices=[
            ("scheduled", "Scheduled"),
            ("in_progress", "In Progress"),
            ("completed", "Completed"),
            ("cancelled", "Cancelled"),
        ],
        default="scheduled",
        help_text=_("Status of the meeting (e.g., Scheduled, In Progress, Completed)."),
    )

    class Meta:
        verbose_name = _("Meeting")
        verbose_name_plural = _("Meetings")
        ordering = ["-meeting_date"]

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(f"{self.title}-{self.meeting_date.strftime('%Y%m%d%H%M')}")
        super().save(*args, **kwargs)
        
    def clean(self):
        from django.core.exceptions import ValidationError

        if self.meeting_type == self.MeetingType.IN_PERSON and not self.meeting_venue:
            raise ValidationError("Meeting venue is required for in-person meetings.")

        if self.meeting_type == self.MeetingType.ONLINE and not self.meeting_link:
            raise ValidationError("Online meeting link is required for online meetings.")
        
        if self.audience == SCOPE_CHOICES.FAMILY and not self.family:
            raise ValidationError("A family must be selected when audience is 'Specific Family'.")

        if self.audience != SCOPE_CHOICES.FAMILY and self.family is not None:
            raise ValidationError("Family should only be set for 'Specific Family' audience.")

        
    @property
    def date_time_formatter(self):
        start_local = timezone.localtime(self.meeting_date)
        end_local = timezone.localtime(self.meeting_end_date)
        if start_local.date() == end_local.date():
            return f"{start_local.strftime('%a %d %b %Y')}, {start_local.strftime('%H:%M')} - {end_local.strftime('%H:%M')}"
        else:
            return f"{start_local.strftime('%a %d %b %Y, %H:%M')} - {end_local.strftime('%a %d %b %Y, %H:%M')}"
        
    @property
    def duration(self):
        delta = self.meeting_end_date - self.meeting_date
        hours = delta.total_seconds() // 3600
        minutes = (delta.total_seconds() % 3600) // 60
        return f"{int(hours)}h {int(minutes)}min"
    
    @property
    def google_calendar_url(self):
        return google_calendar_url(self)


    @property
    def outlook_calendar_url(self):
        return outlook_calendar_url(self)


    @property
    def office365_calendar_url(self):
        return office365_calendar_url(self)

    # ---------------------------------------------
    # 🧠 Helper Methods
    # ---------------------------------------------
    def is_online(self):
        return self.meeting_type == self.MeetingType.ONLINE

    def is_for_clan(self):
        return self.audience == SCOPE_CHOICES.CLAN

    def is_for_family(self):
        return self.audience == SCOPE_CHOICES.FAMILY and self.family is not None
    
    def get_absolute_url(self):
        return reverse("bakgomong_kgotla_yamalla:meeting-details", kwargs={"meeting_slug": self.slug})
    
    def get_audience_display_name(self):
        """Human-readable version of who the meeting is for."""
        if self.audience == SCOPE_CHOICES.CLAN:
            return "Entire Kgotla"
        elif self.audience == SCOPE_CHOICES.EXECUTIVES:
            return "Kgotla Executives"
        elif self.audience == SCOPE_CHOICES.FAMILY_LEADERS:
            return "Family Leaders"
        elif self.audience == SCOPE_CHOICES.FAMILY and self.family:
            return f"{self.family.name}"
        return "—"
    
    def get_audience_members(self):
        """Returns a queryset of members who should attend this meeting based on the audience."""
        User = get_user_model()
        if self.audience == SCOPE_CHOICES.CLAN:
            return User.objects.filter(is_active=True, is_approved=True).exclude(member_classification__in=['CHILD', 'GRANDCHILD'])
        elif self.audience == SCOPE_CHOICES.FAMILY and self.family:
            return User.objects.filter(is_active=True, is_approved=True, family=self.family).exclude(member_classification__in=['CHILD', 'GRANDCHILD'])
        elif self.audience == SCOPE_CHOICES.FAMILY_LEADERS:
            return User.objects.filter(is_active=True, is_approved=True, is_family_leader=True).exclude(member_classification__in=['CHILD', 'GRANDCHILD'])
        elif self.audience == SCOPE_CHOICES.EXECUTIVES:
            return User.objects.filter(is_active=True, is_approved=True, role__in=[
                Role.CLAN_CHAIRPERSON, Role.DEP_CHAIRPERSON, Role.DEP_SECRETARY,
                Role.KGOSANA, Role.SECRETARY, Role.TREASURER
            ]).exclude(member_classification__in=['CHILD', 'GRANDCHILD'])
        else:
            return User.objects.none()
    
    # -----------------------------------------------
    # 🔐 ACCESS CONTROL LOGIC
    # -----------------------------------------------
    def user_has_access(self, user):
        """
        Determines if a given user can view/download this document.
        """
        # Unauthenticated users have no access
        if not user.is_authenticated:
            return False

        # Admins can access everything
        if getattr(user, "role", None) == Role.CLAN_CHAIRPERSON or user.is_superuser:
            return True

        # Clan-wide document
        if self.audience == SCOPE_CHOICES.CLAN:
            return True

        # Family-only document
        if self.audience == SCOPE_CHOICES.FAMILY:
            if self.family and user.family == self.family:
                return True
            return False

        # Private (Admin-only)
        if self.audience == SCOPE_CHOICES.FAMILY_LEADERS or self.audience == SCOPE_CHOICES.EXECUTIVES:
            return False

        return False

    def ensure_user_has_access(self, user):
        """
        Raises PermissionDenied if user doesn't have access.
        Useful in views or API endpoints.
        """
        if not self.user_has_access(user):
            raise PermissionDenied(_("You do not have permission to access this meeting."))
        return True