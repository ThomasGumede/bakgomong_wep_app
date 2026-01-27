import json
from django.http import JsonResponse, HttpResponseBadRequest
from django.views.decorators.csrf import csrf_exempt
from contributions.models import NotificationLog

@csrf_exempt
def bulksms_delivery_report(request):
    try:
        data = json.loads(request.body)
        for report in data:
            NotificationLog.objects.create(
                message_id=report.get("messageId"),
                status=report.get("status"),
                recipient=report.get("to"),
                provider="BULKSMS",
                raw_response=report,
            )
        return JsonResponse({"status": "ok"})
    except Exception:
        return HttpResponseBadRequest("Invalid payload")
