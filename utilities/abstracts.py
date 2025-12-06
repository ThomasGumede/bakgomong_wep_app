import re, uuid
from django.db import models
from django.utils.translation import gettext as _

from utilities.validators import validate_fcbk_link, validate_twitter_link, validate_insta_link, validate_in_link, validate_rsa_phone


class AbstractProfile(models.Model):
    address = models.CharField(max_length=300, blank=True, null=True)
    phone = models.CharField(
        help_text=_("Enter cellphone number"),
        max_length=15,
        validators=[validate_rsa_phone],
        null=True,
        blank=True,
    )

    class Meta:
        abstract = True

    def clean(self):
        # normalize phone by removing non-digits (validators will still run)
        if self.phone:
            normalized = re.sub(r"\D+", "", self.phone)
            # optionally keep leading + if required by validator; adjust as needed
            self.phone = normalized
        
class AbstractCreate(models.Model):
    # primary key UUID; DB will index PK automatically (db_index not required)
    id = models.UUIDField(default=uuid.uuid4, primary_key=True, unique=True, editable=False)
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True

class AbstractPayment(models.Model):
    payment_method_type = models.CharField(max_length=50, null=True, blank=True)
    payment_method_card_holder = models.CharField(max_length=50, null=True, blank=True)
    payment_method_masked_card = models.CharField(max_length=50, null=True, blank=True)
    payment_method_scheme = models.CharField(max_length=50, null=True, blank=True)
    # prefer a datetime field for payment date; use CharField only if you store provider raw payloads
    payment_date = models.DateTimeField(null=True, blank=True)

    class Meta:
        abstract = True