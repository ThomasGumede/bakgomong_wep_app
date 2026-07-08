from django.db import models
from django.urls import reverse
from django.utils import timezone
from django.dispatch import receiver
from django.template.defaultfilters import slugify
from django.utils.translation import gettext as _
from django.contrib.auth.models import AbstractUser
from django.db.models.signals import pre_delete, post_save
from django.core.exceptions import ValidationError
from django.db.models import Sum
from django.contrib.auth import get_user_model
from accounts.utils.file_handlers import handle_profile_upload
from utilities.abstracts import AbstractCreate, AbstractProfile
from utilities.choices import Gender, PaymentStatus, Role, Title, EmploymentStatus, MemberClassification


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
        
    def save(self, *args, **kwargs):
        
        # Make sure executives are staff members
        if self.role in [Role.CLAN_CHAIRPERSON, Role.MMAKGOSANA, Role.SECRETARY, Role.DEP_SECRETARY, Role.TREASURER, Role.DEP_CHAIRPERSON, Role.SPONSOR]:
            self.is_staff = True
        else:
            self.is_staff = False  
        
        super(Account, self).save(*args, **kwargs)
        
    def clean(self):
        # Ensure only one user can have a specific role at a time
        
        user_with_role = Account.objects.filter(role=self.role).exclude(pk=self.pk).first()
        if user_with_role:
            if self.role == Role.CLAN_CHAIRPERSON:
                raise ValidationError("There can only be one Kgosana (Kgotla Chairperson) at a time.")
            elif self.role == Role.MMAKGOSANA:
                raise ValidationError("There can only be one Mmakgosana (Deputy Chairperson) at a time.")
            elif self.role == Role.SECRETARY:
                raise ValidationError("There can only be one Secretary at a time.")
            elif self.role == Role.DEP_SECRETARY:
                raise ValidationError("There can only be one Deputy Secretary at a time.")
            elif self.role == Role.TREASURER:
                raise ValidationError("There can only be one Treasurer at a time.")
            elif self.role == Role.DEP_CHAIRPERSON:
                raise ValidationError("There can only be one Deputy Chairperson at a time.")
            elif self.role == Role.SPONSOR:
                raise ValidationError("There can only be one Sponsor at a time.")
            elif self.role == Role.KGOSANA:
                raise ValidationError("There can only be one Kgosana at a time.")
            else:
                raise ValidationError(f"There can only be one user with the role {self.role} at a time.")
        super(Account, self).clean()

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
    