from django.db import models
from django.utils.translation import gettext as _

from utilities.abstracts import AbstractCreate

class Title(models.TextChoices):
    MR = ("MR", "Mr")
    MRS = ("MRS", "Mrs")
    MS = ("MS", "Ms")
    DR = ("DR", "Dr")
    PROF = ("PROF", "Prof.")

class PaymentStatus(models.TextChoices):
    PAID = ("PAID", "Paid")
    PENDING = ("PENDING", "Pending")
    AWAITING_APPROVAL = ("AWAITING APPROVAL", "Awaiting Approval")
    NOT_PAID = ("NOT_PAID", "Not paid")
    CANCELLED = ("CANCELLED", "Cancelled")
    PARTIALLY_PAID = ("PARTIALLY_PAID", "PARTIALLY PAID")
        
class Gender(models.TextChoices):
    MALE = ("MALE", "Male")
    FEMALE = ("FEMALE", "Female")
    OTHER = ("OTHER", "Other")

class EmploymentStatus(models.TextChoices):
    EMPLOYED = ("EMPLOYED", "Employed")
    SELF_EMPLOYED = ("SELF_EMPLOYED", "Self-Employed")
    UNEMPLOYED = ("UNEMPLOYED", "Unemployed")
    RETIRED = ("RETIRED", "Retired")
    STUDENT = ("STUDENT", "Student")
    HOMEMAKER = ("HOMEMAKER", "Homemaker")
    DISABLED = ("DISABLED", "Disabled")

class MemberClassification(models.TextChoices):
    RELATIVE = ("RELATIVE", "Relative")
    CHILD = ("CHILD", "Child")
    PARENT = ("PARENT", "Parent")
    GRANDPARENT = ("GRANDPARENT", "Grandparent")
    OTHER = ("OTHER", "Other")
    
class Role(models.TextChoices):
    KGOSANA = ("KGOSANA", "Kgosana")
    CLAN_CHAIRPERSON = ("CLAN_CHAIRPERSON", "Chairperson")
    MEMBER = ("MEMBER", "Member")
    DEP_CHAIRPERSON = ("DEP_CHAIRPERSON", "Deputy Chairperson")
    SECRETARY = ("SECRETARY", "Secretary")
    DEP_SECRETARY = ("DEP_SECRETARY", "Deputy Secretary")
    TREASURER = ("TREASURER", "Treasurer")
    
class PaymentMethod(models.TextChoices):
        CASH = 'cash', _('Cash')
        BANK = 'bank', _('Bank Deposit')
        MOBILE = 'mobile', _('Yoco Mobile Payment')
        OTHER = 'other', _('Other')

class SCOPE_CHOICES(models.TextChoices):
        CLAN = "clan", _("Entire Kgotla")
        FAMILY_LEADERS = "family_leaders", _("Family Leaders")
        FAMILY = "family", _("Specific Family")
        EXECUTIVES = "executives", _("Executives")
        
        
class LogPaymentStatus(models.TextChoices):
        NOT_PAID = ("NOT PAID", "Not paid")
        PENDING = "PENDING", _("Pending Verification")
        APPROVED = "APPROVED", _("Approved")
        REJECTED = "REJECTED", _("Rejected")
        
class PaymentMethod(models.TextChoices):
        CASH = 'cash', _('Cash')
        BANK = 'bank', _('Bank Deposit')
        MOBILE = 'mobile', _('Yoco Mobile Payment')
        OTHER = 'other', _('Other')

        
class Recurrence(models.TextChoices):
        ONCE_OFF = 'once_off', _('Once Off')
        MONTHLY = 'monthly', _('Monthly')
        ANNUAL = 'annual', _('Annual')

    # 🧱 StokFella-style contribution categories
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
    