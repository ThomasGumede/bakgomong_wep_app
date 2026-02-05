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
from utilities.choices import SCOPE_CHOICES, Gender, PaymentStatus, Role, Title, EmploymentStatus, MemberClassification

# class Role(AbstractCreate):
#     pass

# class KgotlaBalance(AbstractCreate):
#     title = models.CharField(help_text=_('Enter balance title e.g General Fund Balance'), max_length=300, unique=True)
#     slug = models.SlugField(max_length=400, unique=True, db_index=True)
#     balance = models.DecimalField(help_text=_('Enter current balance amount'), max_digits=12, decimal_places=2, default=0)
#     updated_by = models.ForeignKey(
#         get_user_model(),
#         on_delete=models.SET_NULL,
#         null=True,
#         blank=True,
#         related_name="updated_kgotla_balances"
#     )
#     updated = models.DateTimeField(auto_now=True)
#     created = models.DateTimeField(auto_now_add=True)
    
#     def __str__(self):
#         return f"{self.title}: R{self.balance}"
    
#     class Meta:
#         verbose_name = _("Kgotla Balance")
#         verbose_name_plural = _("Kgotla Balances")
#         ordering = ["-updated"]
    
#     def get_full_balance(self):
#         return f"R{self.balance:,.2f}"
    
#     def get_total_balance(self):
#         from contributions.models import MemberContribution
#         total_contributions = MemberContribution.objects.filter(is_paid=PaymentStatus.PAID).aggregate(total=Sum("amount_due"))["total"] or 0
#         return self.balance + total_contributions
    
#     def save(self, *args, **kwargs):
#         # Generate slug on creation
        
#         base = slugify(self.title) or "kgotla-balance"
#         slug = base
#         counter = 1
#         while KgotlaBalance.objects.filter(slug=slug).exists():
#             slug = f"{base}-{counter}"
#             counter += 1
#         self.slug = slug
#         super(KgotlaBalance, self).save(*args, **kwargs)

class Family(AbstractCreate):
    name = models.CharField(max_length=300, help_text=_('Enter family name e.g Dladla Family'), unique=True)
    slug = models.SlugField(max_length=400, unique=True, db_index=True)
    leader = models.OneToOneField('Account', related_name='family_leader', on_delete=models.SET_NULL, null=True, blank=True)
    is_approved = models.BooleanField(default=False, help_text=_("Should be approved by executives"))
    
    class Meta:
        verbose_name = _("Family")
        verbose_name_plural = _("Families")
        ordering = ["-created"]
        indexes = [
            models.Index(fields=["is_approved"]),
            models.Index(fields=["slug"]),
        ]
        
    def __str__(self):
        return self.name
    
    def save(self, *args, **kwargs):
        # Only generate slug when creating or when name changed
        base = slugify(self.name) or "family"
        if not self.pk:
            slug = base
            counter = 1
            while Family.objects.filter(slug=slug).exists():
                slug = f"{base}-{counter}"
                counter += 1
            self.slug = slug
        else:
            # keep existing slug unless name changed
            try:
                old = Family.objects.get(pk=self.pk)
                if old.name != self.name:
                    slug = base
                    counter = 1
                    while Family.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                        slug = f"{base}-{counter}"
                        counter += 1
                    self.slug = slug
            except Family.DoesNotExist:
                self.slug = base
        super(Family, self).save(*args, **kwargs)
        
        if self.leader and self.leader.family_id != self.pk:
            self.leader.is_family_leader = True
            self.leader.family = self
            self.leader.save(update_fields=["family","is_family_leader"])
        
    def get_absolute_url(self):
        return reverse("accounts:get-family", kwargs={"family_slug": self.slug})
    
    def get_delete_url(self):
        return reverse("accounts:delete-family", kwargs={"family_slug": self.slug})
    
    # def clean(self):
    #     from django.core.exceptions import ValidationError

        
    #     if self.pk and self.leader:
    #         if getattr(self.leader, "family_id", None) != self.pk:
    #             raise ValidationError({"leader": _("Leader must belong to this family.")})
        
    @property
    def total_unpaid(self):
        from contributions.models import MemberContribution
        result = MemberContribution.objects.filter(account__family=self, is_paid=PaymentStatus.NOT_PAID).aggregate(total=Sum("amount_due"))
        return result["total"] or 0
    
    @property
    def total_paid(self):
        from contributions.models import MemberContribution
        result = MemberContribution.objects.filter(account__family=self, is_paid=PaymentStatus.PAID).aggregate(total=Sum("amount_due"))
        return result["total"] or 0
    
    @property
    def total_pending(self):
        from contributions.models import MemberContribution
        return MemberContribution.objects.filter(
            account__family=self,
            is_paid=PaymentStatus.PENDING
        ).aggregate(total=Sum("amount_due"))["total"] or 0

class Account(AbstractUser, AbstractProfile):
    profile_image = models.ImageField(help_text=_("Upload profile image"), upload_to=handle_profile_upload, null=True, blank=True)
    title = models.CharField(max_length=30, choices=Title.choices)
    gender = models.CharField(max_length=30, choices=Gender.choices)
    maiden_name = models.CharField(help_text=_("Enter your maiden name"), max_length=300, blank=True, null=True)
    biography = models.TextField(blank=True)
    role = models.CharField(max_length=100, choices=Role.choices, default=Role.MEMBER)
    id_number = models.CharField(max_length=15, help_text=_("Enter your ID number"), unique=True, blank=True, null=True, db_index=True)
    family = models.ForeignKey(Family, related_name='members', on_delete=models.SET_NULL, null=True, blank=True)
    birth_date = models.DateField(help_text=_("Enter your date of birth"), null=True, blank=True)
    employment_status = models.CharField(max_length=20, choices=EmploymentStatus.choices, help_text=_("Select employment status"), null=True, blank=True)
    member_classification = models.CharField(max_length=20, choices=MemberClassification.choices, help_text=_("Select member classification"), null=True, blank=True)
    langueges_spoken = models.CharField(max_length=300, help_text=_("Enter languages you speak, separated by commas"), blank=True, null=True)
    is_approved = models.BooleanField(default=False, help_text=_("Should be approved by executives"))
    is_family_leader = models.BooleanField(default=False, help_text=_("Tick if member is a family leader"))
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = _("Account")
        verbose_name_plural = _("Accounts")
        ordering = ["-created"]
        indexes = [
            models.Index(fields=["is_approved"]),
            models.Index(fields=["family"]),
        ]

    def __str__(self):
        full = self.get_full_name() or ""
        return full.strip() or self.username
    
    get_absolute_url = lambda self: reverse("accounts:user-details", kwargs={"username": self.username})
    get_update_url = lambda self: reverse("accounts:profile-update")
    
    
    def get_unpaid_invoices(self):
        from contributions.models import MemberContribution
        results = MemberContribution.objects.filter(account=self, is_paid=PaymentStatus.NOT_PAID)
        return results
    
    @property
    def total_unpaid(self):
        from contributions.models import MemberContribution
        result = MemberContribution.objects.filter(account=self, is_paid__in=[PaymentStatus.NOT_PAID, PaymentStatus.PENDING, PaymentStatus.AWAITING_APPROVAL]).aggregate(total=Sum("amount_due"))
        return result["total"] or 0
    
    @property
    def total_paid(self):
        from contributions.models import MemberContribution
        result = MemberContribution.objects.filter(account=self, is_paid=PaymentStatus.PAID).aggregate(total=Sum("amount_due"))
        return result["total"] or 0
    
    @property
    def total_pending(self):
        from contributions.models import MemberContribution
        return MemberContribution.objects.filter(
            account=self,
            is_paid__in=[PaymentStatus.PENDING, PaymentStatus.AWAITING_APPROVAL]
        ).aggregate(total=Sum("amount_due"))["total"] or 0
    
    def get_oustandings(self):
        from contributions.models import MemberContribution
        return MemberContribution.objects.filter(account=self, is_paid__in=[PaymentStatus.NOT_PAID, PaymentStatus.PENDING, PaymentStatus.AWAITING_APPROVAL])
    
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
        return reverse("accounts:clan-meetings")
    
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