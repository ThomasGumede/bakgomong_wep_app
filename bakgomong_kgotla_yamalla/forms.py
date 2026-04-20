from django import forms
from django.utils.translation import gettext_lazy as _
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
