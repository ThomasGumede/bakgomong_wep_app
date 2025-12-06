import logging
import mimetypes
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.db.models import Sum
from django.contrib import messages
from django.contrib import messages
from django.http import HttpResponse, JsonResponse
from django.core import serializers
from accounts.forms import MeetingForm
from accounts.models import ClanDocument, Meeting
from django.core.exceptions import PermissionDenied
from contributions.models import ContributionType, MemberContribution
from utilities.choices import PaymentStatus, Role


logger = logging.getLogger("accounts")

def can_manage_meetings(user):
    return (
        user.is_superuser or 
        getattr(user, "role", None) in [Role.CLAN_CHAIRPERSON, Role.DEP_CHAIRPERSON, Role.SECRETARY, Role.TREASURER, Role.DEP_SECRETARY, Role.KGOSANA]
    )

@login_required
def dashboard(request):
    user = request.user
    context = {}

    member_contribs_qs = MemberContribution.objects.all().order_by("-created")
    
    # Total paid for clan
    context["clan_total_paid"] = member_contribs_qs.filter(
        is_paid=PaymentStatus.PAID
    ).aggregate(total_paid=Sum("amount_due"))["total_paid"] or 0
    

    # Last 5 unpaid/pending payments for user
    unpaid_statuses = [PaymentStatus.NOT_PAID, PaymentStatus.PENDING, PaymentStatus.AWAITING_APPROVAL]
    context["latest_unpaid"] = member_contribs_qs.filter(account=user, is_paid=PaymentStatus.NOT_PAID).order_by('-due_date').first()
   
    

    if user.is_staff:
        clan_unpaid_qs = member_contribs_qs.filter(is_paid__in=unpaid_statuses)
        context["clan_total_unpaid"] = clan_unpaid_qs.aggregate(
            total_unpaid=Sum("amount_due")
        )["total_unpaid"] or 0
        context["clan_total_unpaid_count"] = clan_unpaid_qs.count()
        context["payments"] = member_contribs_qs.select_related("account")[:5]

    return render(request, 'dashboard.html', context)

@login_required
def clan_documents(request):
    documents = ClanDocument.objects.all()
    docs = [doc for doc in documents if doc.user_has_access(request.user)]
    return render(request, 'home/documents.html', {'docs': docs})


@login_required
def clan_meetings(request):
    form = MeetingForm()
    meetings = Meeting.objects.all()
    meets = [meet for meet in meetings if meet.user_has_access(request.user)]
    return render(request, 'home/meetings.html', {"form": form, 'meetings': meets})


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
        
    
    return render(request, "home/meetings.html", {"form": form, "meetings": meets})


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

    return render(request, "home/meetings.html", {"form": form, "meetings": meets})


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

    return render(request, "home/meetings.html", {"form": form, "meetings": meets})

def get_clan_meetings_api(request):
    try:
        meetings = Meeting.objects.all()
        data = serializers.serialize("json", meetings)
        return JsonResponse({"success": True, "meetings": data}, status=200)
    except Exception as ex:
        return JsonResponse({"success": False, "message": f"Something went wrong: {ex}"}, status=200)


@login_required
def download_file(request, file_id):
    media = get_object_or_404(ClanDocument.objects.all(), id=file_id)

    try:
        file_path = media.file.path
        file_name = media.file.name
        if file_path and file_name:
            with open(file_path, 'rb') as file:
                file_data = file.read()
                mime_type, _ = mimetypes.guess_type(file_path)
                mime_type = mime_type or 'application/octet-stream'
                response = HttpResponse(file_data, content_type=mime_type)

            response['Content-Disposition'] = f'attachment; filename="{file_name.split("/")[-1]}"'

        return response
    except Exception as ex:
        logger.error("Missing Media file: %s", ex)
        messages.error(request, "Media file not uploaded yet, send us an email if you have questions")
        return redirect("dashboard:clan-documents")