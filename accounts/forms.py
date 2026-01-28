from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import (AuthenticationForm,  UserCreationForm)
from django.utils.translation import gettext_lazy as _
from accounts.models import Family
from utilities.choices import Role
from .models import Meeting

class MeetingForm(forms.ModelForm):
    class Meta:
        model = Meeting
        fields = [
            "title",
            "description",
            "meeting_type",
            "meeting_venue",
            "meeting_link",
            "audience",
            "meeting_date",
            "meeting_end_date",
            "family",
        ]

        widgets = {
            "meeting_date": forms.DateTimeInput(attrs={"type": "datetime-local", "class": "form-control rounded-lg bg-white dark:bg-neutral-700","id": "editstartDate"}),
            "meeting_end_date": forms.DateTimeInput(attrs={"type": "datetime-local", "class": "form-control rounded-lg bg-white dark:bg-neutral-700","id": "editendDate"}),
            'audience': forms.Select(attrs={"class": "form-control rounded-lg form-select"}),
            'family': forms.Select(attrs={"class": "form-control rounded-lg form-select"}),
            'meeting_type': forms.Select(attrs={"class": "form-control rounded-lg form-select"}),
        }

    def clean(self):
        cleaned = super().clean()
        meeting_type = cleaned.get("meeting_type")
        venue = cleaned.get("meeting_venue")
        link = cleaned.get("meeting_link")

        # Validation rules
        if meeting_type == Meeting.MeetingType.IN_PERSON and not venue:
            self.add_error("meeting_venue", "Venue is required for in-person meetings.")

        if meeting_type == Meeting.MeetingType.ONLINE and not link:
            self.add_error("meeting_link", "Meeting link is required for online meetings.")

        return cleaned

class UserLoginForm(AuthenticationForm):
    def __init__(self, *args, **kwargs):
        super(UserLoginForm, self).__init__(*args, **kwargs)
    
    username = forms.CharField(widget=forms.TextInput(attrs={'placeholder': 'Username or Email', 'id': 'id_username'}), label="Username or Email*")
    password = forms.CharField(widget=forms.PasswordInput(attrs={'placeholder': 'Password', 'id': 'id_password'}))

class RegistrationForm(UserCreationForm):
    """Custom registration form for the Clan Contribution Tracker."""

    class Meta:
        model = get_user_model()
        fields = ('email', 'first_name', 'last_name', 'password1', 'password2')

        widgets = {
            'email': forms.EmailInput(attrs={
                "class": "w-full px-8 py-4 rounded-lg font-medium bg-gray-100 border border-gray-200 placeholder-gray-500 text-sm focus:outline-none focus:border-gray-400 focus:bg-white",
                "placeholder": _("Enter your email address"),
            }),
            'first_name': forms.TextInput(attrs={
                "class": "w-full px-8 py-4 rounded-lg font-medium bg-gray-100 border border-gray-200 placeholder-gray-500 text-sm focus:outline-none focus:border-gray-400 focus:bg-white",
                "placeholder": _("First name"),
            }),
            'last_name': forms.TextInput(attrs={
                "class": "w-full px-8 py-4 rounded-lg font-medium bg-gray-100 border border-gray-200 placeholder-gray-500 text-sm focus:outline-none focus:border-gray-400 focus:bg-white",
                "placeholder": _("Last name"),
            }),
            'password1': forms.PasswordInput(attrs={
                "class": "w-full px-8 py-4 rounded-lg font-medium bg-gray-100 border border-gray-200 placeholder-gray-500 text-sm focus:outline-none focus:border-gray-400 focus:bg-white",
                "placeholder": _("Enter password"),
            }),
            'password2': forms.PasswordInput(attrs={
                "class": "w-full px-8 py-4 rounded-lg font-medium bg-gray-100 border border-gray-200 placeholder-gray-500 text-sm focus:outline-none focus:border-gray-400 focus:bg-white",
                "placeholder": _("Confirm password"),
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        for field_name, field in self.fields.items():
            field.widget.attrs['autocomplete'] = 'off'
            if self.initial.get(field_name) is None:
                self.initial[field_name] = ''

    def clean_email(self):
        """Ensure email uniqueness across users."""
        email = (self.cleaned_data.get("email") or "").strip().lower()
        User = get_user_model()
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError(
                _(f"This email ({email}) is already registered.")
            )
        return email

    def save(self, commit=True):
        """Save the user with email as username."""
        user = super().save(commit=False)
        email = (self.cleaned_data['email'] or "").strip().lower()
        user.email = email
        user.username = email
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']

        if commit:
            user.save()
            if hasattr(self, "save_m2m"):
                self.save_m2m()
        return user


class MemberForm(UserCreationForm):
    class Meta:
        model = get_user_model()
        fields = ("username", "title", "family", "profile_image", "first_name", "last_name", 'maiden_name', "biography", "gender", "email", "phone", "address", 'password1', 'password2', 'birth_date', 'langueges_spoken', "employment_status", "member_classification", 'id_number')

        widgets = {
            'email': forms.EmailInput(attrs={
                "class": "w-full px-8 py-4 rounded-lg font-medium bg-gray-100 border border-gray-200 placeholder-gray-500 text-sm focus:outline-none focus:border-gray-400 focus:bg-white",
                "placeholder": _("Enter your email address"),
            }),
            'first_name': forms.TextInput(attrs={
                "class": "w-full px-8 py-4 rounded-lg font-medium bg-gray-100 border border-gray-200 placeholder-gray-500 text-sm focus:outline-none focus:border-gray-400 focus:bg-white",
                "placeholder": _("First name"),
            }),
            'last_name': forms.TextInput(attrs={
                "class": "w-full px-8 py-4 rounded-lg font-medium bg-gray-100 border border-gray-200 placeholder-gray-500 text-sm focus:outline-none focus:border-gray-400 focus:bg-white",
                "placeholder": _("Last name"),
            }),
            'password1': forms.PasswordInput(attrs={
                "class": "w-full px-8 py-4 rounded-lg font-medium bg-gray-100 border border-gray-200 placeholder-gray-500 text-sm focus:outline-none focus:border-gray-400 focus:bg-white",
                "placeholder": _("Enter password"),
            }),
            'password2': forms.PasswordInput(attrs={
                "class": "w-full px-8 py-4 rounded-lg font-medium bg-gray-100 border border-gray-200 placeholder-gray-500 text-sm focus:outline-none focus:border-gray-400 focus:bg-white",
                "placeholder": _("Confirm password"),
            }),
            'gender': forms.Select(attrs={"class": "form-control rounded-lg form-select"}),
            'title': forms.Select(attrs={"class": "form-control rounded-lg form-select"}),
            'family': forms.Select(attrs={"class": "form-control rounded-lg form-select"}),
            'birth_date': forms.DateInput(attrs={"type": "date", "class": "form-control rounded-lg bg-white dark:bg-neutral-700"}),
            'employment_status': forms.Select(attrs={"class": "form-control rounded-lg form-select"}),
            'member_classification': forms.Select(attrs={"class": "form-control rounded-lg form-select"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        for field_name, field in self.fields.items():
            field.widget.attrs['autocomplete'] = 'off'
            if self.initial.get(field_name) is None:
                self.initial[field_name] = ''

    def clean_email(self):
        """Ensure email uniqueness across users."""
        email = (self.cleaned_data.get("email") or "").strip().lower()
        User = get_user_model()
        if User.objects.exclude(pk=getattr(self.instance, "pk", None)).filter(email=email).exists():
            raise forms.ValidationError(
                _(f"This email ({email}) is already registered.")
            )
        return email

    def clean_username(self):
        username = (self.cleaned_data.get("username") or "").strip()
        User = get_user_model()
        if User.objects.exclude(pk=getattr(self.instance, "pk", None)).filter(username=username).exists():
            raise forms.ValidationError(_(f"This username ({username}) is already in use."))
        return username

    def save(self, commit=True):
        """Save the user with email as username."""
        user = super().save(commit=False)
        email = (self.cleaned_data.get('email') or "").strip().lower()
        user.email = email
        # if username not provided or equals email field, keep it consistent
        if not user.username or user.username == "":
            user.username = email
        # keep new members inactive until they verify / are approved
        if not getattr(user, "pk", None):
            user.is_active = False
            if hasattr(user, "is_email_activated"):
                user.is_email_activated = False

        if commit:
            user.save()
            if hasattr(self, "save_m2m"):
                self.save_m2m()
        return user
    
class AccountUpdateForm(forms.ModelForm):
    
    class Meta:
        model = get_user_model()
        fields = ["username", "title", "profile_image", "first_name", "last_name", 'maiden_name', "id_number", "biography", "gender", "email", "phone", "address", "birth_date", "langueges_spoken"]

        widgets = {
            'username': forms.TextInput(attrs={"class": "text-custom-text pl-5 pr-[50px] outline-none border-2 border-[#e4ecf2] focus:border focus:border-custom-primary h-[65px] block w-full rounded-none focus:ring-0 focus:outline-none placeholder:text-custom-text placeholder:text-sm"}),
            'title': forms.Select(attrs={"class": "form-control rounded-lg form-select"}),
            'first_name': forms.TextInput(attrs={"class": "text-custom-text pl-5 pr-[50px] outline-none border-2 border-[#e4ecf2] focus:border focus:border-custom-primary h-[65px] block w-full rounded-none focus:ring-0 focus:outline-none placeholder:text-custom-text placeholder:text-sm"}),
            'maiden_name': forms.TextInput(attrs={"class": "text-custom-text pl-5 pr-[50px] outline-none border-2 border-[#e4ecf2] focus:border focus:border-custom-primary h-[65px] block w-full rounded-none focus:ring-0 focus:outline-none placeholder:text-custom-text placeholder:text-sm"}),
            'last_name': forms.TextInput(attrs={"class": "text-custom-text pl-5 pr-[50px] outline-none border-2 border-[#e4ecf2] focus:border focus:border-custom-primary h-[65px] block w-full rounded-none focus:ring-0 focus:outline-none placeholder:text-custom-text placeholder:text-sm"}),
            #'hobbies': forms.TextInput(attrs={"class": "text-custom-text pl-5 pr-[50px] outline-none border-2 border-[#e4ecf2] focus:border focus:border-custom-primary h-[65px] block w-full rounded-none focus:ring-0 focus:outline-none placeholder:text-custom-text placeholder:text-sm"}),
            'gender': forms.Select(attrs={"class": "form-control rounded-lg form-select"}),
        }

    def __init__(self, *args, **kwargs):
        super(AccountUpdateForm, self).__init__(*args, **kwargs)
        for field_name, field_value in self.initial.items():
            if field_value is None:
                self.initial[field_name] = ''
     
class FamilyForm(forms.ModelForm):
    class Meta:
        model = Family
        fields = ('name', 'leader')
        
        widgets = {
            'name': forms.TextInput(attrs={"class": "text-custom-text pl-5 pr-[50px] outline-none border-2 border-[#e4ecf2] focus:border focus:border-custom-primary h-[65px] block w-full rounded-none focus:ring-0 focus:outline-none placeholder:text-custom-text placeholder:text-sm"}),
            'leader': forms.Select(attrs={"class": "form-control rounded-lg form-select"}),
            
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        for field_name, field in self.fields.items():
            field.widget.attrs['autocomplete'] = 'off'
            if self.initial.get(field_name) is None:
                self.initial[field_name] = ''
                
        User = get_user_model()
        allowed_roles = [ 
            Role.DEP_SECRETARY, 
            Role.CLAN_CHAIRPERSON,
            Role.DEP_CHAIRPERSON,
            Role.TREASURER,
            Role.KGOSANA,
            Role.SECRETARY,
            Role.MEMBER
        ]

        self.fields["leader"].queryset = User.objects.filter(role__in=allowed_roles)
        
        # Ensure editing pre-selects the current leader (if any)
        if self.instance.pk and self.instance.leader:
            self.initial["leader"] = self.instance.leader.pk
            
class AddFamilyForm(forms.ModelForm):
    class Meta:
        model = Family
        fields = ('name', 'leader')
        
        widgets = {
            'name': forms.TextInput(attrs={"class": "text-custom-text pl-5 pr-[50px] outline-none border-2 border-[#e4ecf2] focus:border focus:border-custom-primary h-[65px] block w-full rounded-none focus:ring-0 focus:outline-none placeholder:text-custom-text placeholder:text-sm"}),
            'leader': forms.Select(attrs={"class": "form-control rounded-lg form-select"}),
            
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        for field_name, field in self.fields.items():
            field.widget.attrs['autocomplete'] = 'off'
            if self.initial.get(field_name) is None:
                self.initial[field_name] = ''
        # Limit choices to only members who are family leaders
        if getattr(self.instance, "pk", None):
            User = get_user_model()
            self.fields["leader"].queryset = User.objects.filter(role_in=[Role.MEMBER, Role.DEP_SECRETARY, Role.CLAN_CHAIRPERSON, Role.DEP_CHAIRPERSON, Role.TREASURER])
