from contributions.models import SMSLog

def create_sms_log(phone_number: str, message: str) -> SMSLog:
    return SMSLog.objects.create(
        phone_number=phone_number,
        message=message
    )
