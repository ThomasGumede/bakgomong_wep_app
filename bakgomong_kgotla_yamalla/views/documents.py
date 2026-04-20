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


logger = logging.getLogger("documents")

@login_required
def clan_documents(request):
    documents = ClanDocument.objects.all()
    docs = [doc for doc in documents if doc.user_has_access(request.user)]
    return render(request, 'documents/documents.html', {'docs': docs})

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