import logging
from decimal import Decimal, InvalidOperation
from django import forms
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

from utilities.choices import PaymentStatus
from .models import ContributionType, MemberContribution, Payment
from django.contrib.auth import get_user_model

logger = logging.getLogger("contributions.forms")
unpaid_statuses = [PaymentStatus.NOT_PAID, PaymentStatus.PENDING, PaymentStatus.AWAITING_APPROVAL]

class MemberContributionForm(forms.ModelForm):
    class Meta:
        model = MemberContribution
        fields = [
            "account",
            "contribution_type",
            "amount_due",
            "reference",
            "due_date",
            "is_paid",
        ]
        widgets = {
            "due_date": forms.DateInput(attrs={"type": "date"}),
        }

    def __init__(self, *args, **kwargs):
        user = kwargs.pop("user", None)
        super().__init__(*args, **kwargs)
        # Limit contribution types if you have family- or active-flag
        self.fields["contribution_type"].queryset = ContributionType.objects.all().order_by("name")
        # If creating/updating for a specific user, restrict account choices
        if user and not user.is_staff:
            self.fields["account"].queryset = get_user_model().objects.filter(pk=user.pk)
        else:
            self.fields["account"].queryset = get_user_model().objects.all()
        # reference is normally generated — keep readonly in form when present
        if not self.instance or not self.instance.pk:
            self.fields["reference"].widget.attrs["readonly"] = True


class ContributionTypeForm(forms.ModelForm):
    class Meta:
        model = ContributionType
        fields = [
            'name', 'description', 'category', 'amount', 
            'recurrence', 'due_date', 'scope', 'family'
        ]
        widgets = {
            'due_date': forms.DateInput(attrs={'type': 'date'}),
            'description': forms.Textarea(attrs={'rows': 3}),
            'category': forms.Select(attrs={"class": "form-control rounded-lg form-select"}),
            'recurrence': forms.Select(attrs={"class": "form-control rounded-lg form-select"}),
            'scope': forms.Select(attrs={"class": "form-control rounded-lg form-select"}),
            'family': forms.Select(attrs={"class": "form-control rounded-lg form-select"}),
        }
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        for field_name, field in self.fields.items():
            field.widget.attrs['autocomplete'] = 'off'
            if self.initial.get(field_name) is None:
                self.initial[field_name] = ''



class PaymentCheckoutForm(forms.ModelForm):
    """Form for members to pay online (checkout)."""

    class Meta:
        model = Payment
        fields = ('member_contribution', 'amount', 'payment_method')

        widgets = {
            
            'member_contribution': forms.Select(attrs={
                "class": "form-control rounded-lg form-select",
                "placeholder": "Select Member Contribution"
            }),
            'amount': forms.NumberInput(attrs={
                "class": "form-control",
                "placeholder": "Enter Contribution Amount e.g R100",
                "step": "0.01"
            }),
            'payment_method': forms.Select(attrs={
                "class": "form-control rounded-lg form-select",
            }),
        }

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop("user", None)
        
        super().__init__(*args, **kwargs)

        

        if self.user:
            # Use single PaymentStatus value (not list)
            mc_qs = MemberContribution.objects.filter(
                account=self.user,
                is_paid='NOT_PAID'
            ).select_related('contribution_type')
            self.fields['member_contribution'].queryset = mc_qs
        else:
            self.fields['member_contribution'].queryset = MemberContribution.objects.none()

    def clean(self):
        cleaned_data = super().clean()
        member_contribution = cleaned_data.get("member_contribution")
        
        amount = cleaned_data.get("amount")

        if member_contribution:
            # Match contribution type
            

            # Amount validation
            try:
                amt = Decimal(amount)
            except (InvalidOperation, TypeError):
                raise ValidationError(_("Enter a valid payment amount."))

            if amt <= 0:
                raise ValidationError(_("Payment amount must be greater than zero."))

            outstanding = Decimal(member_contribution.amount_due)

            # Exact match required
            if amt != outstanding:
                raise ValidationError(
                    _("Payment amount must equal outstanding balance: R%(amount)s.") 
                    % {"amount": f"{outstanding:.2f}"}
                )

            # Ensure user pays only their own contributions
            if self.user and member_contribution.account != self.user:
                raise ValidationError(_("You cannot pay for another member's contribution."))

        return cleaned_data


class LogPaymentForm(forms.ModelForm):
    """Form for treasurer to manually log/record a payment with proof."""

    class Meta:
        model = Payment
        fields = (
            'member_contribution',
            'amount',
            'payment_method',
            'reference',
            'receipt',
            'proof_of_payment',
            
        )

        widgets = {
            'member_contribution': forms.Select(attrs={
                "class": "form-control rounded-lg form-select",
                "placeholder": "Select Member Contribution",
                "required": True
            }),
            
           
            'amount': forms.NumberInput(attrs={
                "class": "form-control",
                "placeholder": "e.g. R500.00",
                "step": "0.01",
                "required": True
            }),
            'payment_method': forms.Select(attrs={
                "class": "form-control rounded-lg form-select",
                "required": True
            }),
            'reference': forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "e.g. Bank ref, invoice #, transaction ID",
                "help_text": "Transaction/reference number for tracking"
            }),
            'receipt': forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "e.g. Receipt number from bank",
                "help_text": "Receipt number from payment provider"
            }),
            'proof_of_payment': forms.FileInput(attrs={
                "class": "form-control",
                "accept": ".pdf,.jpg,.jpeg,.png,.gif",
                "required": True,
                "help_text": "Upload bank statement, screenshot, or receipt (PDF, JPG, PNG)"
            }),
        }

    def __init__(self, *args, **kwargs):
        self.treasurer = kwargs.pop("treasurer", None)  # User logging the payment
        super().__init__(*args, **kwargs)

        # Show only unpaid contributions
        self.fields['member_contribution'].queryset = (
            MemberContribution.objects
            .filter(is_paid__in=unpaid_statuses)
            .select_related('account', 'contribution_type')
            .order_by('-created')
        )

        # Set help texts
        self.fields['member_contribution'].help_text = "Select the member contribution to log payment for"
        self.fields['amount'].help_text = "Must match the outstanding amount"
        self.fields['payment_method'].help_text = "How was payment received?"

        # Make proof_of_payment required
        self.fields['proof_of_payment'].required = True
        self.fields['reference'].required = True

    def clean(self):
        cleaned_data = super().clean()
        member_contribution = cleaned_data.get("member_contribution")
        amount = cleaned_data.get("amount")
        proof_of_payment = cleaned_data.get("proof_of_payment")
        payment_method = cleaned_data.get("payment_method")

        # Validate member contribution exists
        if not member_contribution:
            raise ValidationError(_("Please select a member contribution."))

        # Validate amount
        try:
            amt = Decimal(amount) if amount else Decimal(0)
        except (InvalidOperation, TypeError):
            raise ValidationError(_("Enter a valid payment amount."))

        if amt <= 0:
            raise ValidationError(_("Payment amount must be greater than zero."))

        outstanding = Decimal(member_contribution.amount_due)

        # Exact match required (treasurer must verify amount)
        if amt != outstanding:
            raise ValidationError(
                _("Payment amount must equal outstanding balance: R%(amount)s.") 
                % {"amount": f"{outstanding:.2f}"}
            )

        # Proof of payment is required
        if not proof_of_payment:
            raise ValidationError(_("Proof of payment (receipt/statement) is required."))

        # Validate file type
        allowed_types = ['application/pdf', 'image/jpeg', 'image/png', 'image/gif']
        if proof_of_payment.content_type not in allowed_types:
            raise ValidationError(
                _("Invalid file type. Accepted: PDF, JPG, PNG, GIF")
            )

        # Validate file size (max 5MB)
        if proof_of_payment.size > 5 * 1024 * 1024:
            raise ValidationError(
                _("File size exceeds 5MB limit.")
            )

        # Payment method must be selected
        if not payment_method:
            raise ValidationError(_("Please select a payment method."))

        logger.info(
            "LogPaymentForm validation: member_contribution=%s, amount=R%s, method=%s",
            member_contribution.reference,
            amt,
            payment_method
        )

        return cleaned_data