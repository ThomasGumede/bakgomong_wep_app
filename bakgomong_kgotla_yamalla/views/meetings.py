import logging
import mimetypes
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.db.models import Sum
from django.contrib import messages
from django.contrib import messages
from django.http import HttpResponse, JsonResponse
from django.core import serializers
from bakgomong_kgotla_yamalla.forms import MeetingForm
from bakgomong_kgotla_yamalla.models import ClanDocument, Meeting
from django.core.exceptions import PermissionDenied
from contributions.models import ContributionType, MemberContribution
from utilities.choices import PaymentStatus, Role

def can_manage_meetings(user):
    return (
        user.is_superuser or 
        getattr(user, "role", None) in [Role.CLAN_CHAIRPERSON, Role.DEP_CHAIRPERSON, Role.SECRETARY, Role.TREASURER, Role.DEP_SECRETARY, Role.KGOSANA]
    )
    
@login_required
def clan_documents(request):
    documents = ClanDocument.objects.all()
    docs = [doc for doc in documents if doc.user_has_access(request.user)]
    return render(request, 'home/documents.html', {'docs': docs, "family": getattr(request.user, "family", None)})


@login_required
def clan_meetings(request):
    form = MeetingForm()
    meetings = Meeting.objects.all()
    meets = [meet for meet in meetings if meet.user_has_access(request.user)]
    return render(request, 'meetings/meetings.html', {"form": form, 'meetings': meets, "family": getattr(request.user, "family", None)})


@login_required
def meeting_create(request):
    if not can_manage_meetings(request.user):
        raise PermissionDenied("You cannot create meetings.")
    meetings = Meeting.objects.all()
    meets = [meet for meet in meetings if meet.user_has_access(request.user)]
    if request.method == "POST":
        form = MeetingForm(request.POST)
        if form.is_valid():
            meeting = form.save(commit=False)
            meeting.created_by = request.user
            meeting.save()
            return redirect("accounts:clan-meetings")
    else:
        form = MeetingForm()
        
    
    return render(request, "meetings/meetings.html", {"form": form, "meetings": meets, "family": getattr(request.user, "family", None)})


# -------------------------
# UPDATE
# -------------------------
@login_required
def meeting_update(request, meeting_slug):
    meetings = Meeting.objects.all()
    meeting = get_object_or_404(meetings, slug=meeting_slug)

    if not can_manage_meetings(request.user):
        raise PermissionDenied("You cannot edit meetings.")
    
    
    meets = [meet for meet in meetings if meet.user_has_access(request.user)]
    if request.method == "POST":
        form = MeetingForm(request.POST, instance=meeting)
        if form.is_valid():
            form.save()
            messages.success(request, "Meeting updated successfully.")
            return redirect("accounts:clan-meetings")
    else:
        form = MeetingForm(instance=meeting)
        messages.info(request, "Unable to update the meeting Please fix the errors below.")
        for error in form.errors:
            messages.error(request, f"{error}: {form.errors[error].as_text()}")
        return redirect("accounts:clan-meetings")

    return render(request, "meetings/meetings.html", {"form": form, "meetings": meets, "family": getattr(request.user, "family", None)})


# -------------------------
# DELETE
# -------------------------
@login_required
def meeting_delete(request, meeting_slug):
    meetings = Meeting.objects.all()
    meeting = get_object_or_404(meetings, slug=meeting_slug)
    meets = [meet for meet in meetings if meet.user_has_access(request.user)]
    form = MeetingForm(instance=meeting)
    if not can_manage_meetings(request.user):
        raise PermissionDenied("You cannot delete meetings.")

    if request.method == "POST":
        meeting.delete()
        messages.success(request, "Meeting deleted successfully.")
        return redirect("accounts:clan-meetings")

    return render(request, "meetings/meetings.html", {"form": form, "meetings": meets, "family": getattr(request.user, "family", None)})

def get_clan_meetings_api(request):
    try:
        meetings = Meeting.objects.all()
        data = serializers.serialize("json", meetings)
        return JsonResponse({"success": True, "meetings": data}, status=200)
    except Exception as ex:
        return JsonResponse({"success": False, "message": f"Something went wrong: {ex}"}, status=200)
