from django.conf import settings
import logging
from accounts.utils import custom_mail
from bakgomong_kgotla_yamalla.models import Meeting
logger = logging.getLogger("tasks")

def send_notification_new_meeting_task(meeting_pk, to, subject):
    
    try:
        meeting = Meeting.objects.get(pk=meeting_pk)
    except Meeting.DoesNotExist:
        logger.error("send_notification_new_meeting_task: Meeting %s not found", meeting_pk)
        return False

    try:
        pass
        # return custom_mail.send_new_meeting_notification(meeting, to, subject)
    except Exception:
        logger.exception("send_notification_new_meeting_task failed for %s", meeting_pk)
        return False

def send_notification_new_meeting_to_members_task(meeting_pk):
    
    try:
        meeting = Meeting.objects.get(pk=meeting_pk)
        users = meeting.get_audience_members()
        
        for user in users:
            if user.email:
                send_notification_new_meeting_task(meeting_pk, user.email, f"New Meeting Scheduled: {meeting.title}")
                logger.info(f"Email sent to {user.email}")
                
            if user.phone:
                from contributions.utils.notifications import send_smsportal_sms
                sms_message = f"New Upcoming Meeting: {meeting.title} on {meeting.date_time_formatter}, at {meeting.meeting_venue}. Contact excecutives for more information."
                logger.info(f"Text sms sent to {user.phone}")
                send_smsportal_sms(user.phone, sms_message)
        
        return f"Notification was sent to person with {user.email} and {user.phone}"
                
    except Meeting.DoesNotExist:
        logger.error("send_notification_new_meeting_to_members_task: Meeting %s not found", meeting_pk)
        return False