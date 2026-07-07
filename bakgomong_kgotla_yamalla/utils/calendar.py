from datetime import datetime
from urllib.parse import urlencode
from zoneinfo import ZoneInfo

from django.http import HttpResponse
from django.utils import timezone


SA_TIMEZONE = ZoneInfo("Africa/Johannesburg")


def _ensure_timezone(dt: datetime) -> datetime:
    """
    Ensures a datetime is timezone-aware and converted to Africa/Johannesburg.
    """
    if timezone.is_naive(dt):
        dt = timezone.make_aware(dt, SA_TIMEZONE)

    return dt.astimezone(SA_TIMEZONE)


def _calendar_datetime(dt: datetime) -> str:
    """
    Returns datetime in iCalendar local format.

    Example:
    20260213T140000
    """
    return _ensure_timezone(dt).strftime("%Y%m%dT%H%M%S")


def _calendar_utc(dt: datetime) -> str:
    """
    Returns UTC datetime for DTSTAMP.

    Example:
    20260213T120000Z
    """
    return (
        _ensure_timezone(dt)
        .astimezone(ZoneInfo("UTC"))
        .strftime("%Y%m%dT%H%M%SZ")
    )


def _meeting_location(meeting):
    if meeting.is_online():
        return meeting.meeting_link or ""

    return meeting.meeting_venue or ""


# ===========================================================
# Google Calendar
# ===========================================================

def google_calendar_url(meeting):
    params = {
        "action": "TEMPLATE",
        "text": meeting.title,
        "dates": (
            f"{_calendar_datetime(meeting.meeting_date)}/"
            f"{_calendar_datetime(meeting.meeting_end_date)}"
        ),
        "ctz": "Africa/Johannesburg",
        "details": meeting.description or "",
        "location": _meeting_location(meeting),
    }

    return (
        "https://calendar.google.com/calendar/render?"
        + urlencode(params)
    )


# ===========================================================
# Outlook.com
# ===========================================================

def outlook_calendar_url(meeting):
    params = {
        "path": "/calendar/action/compose",
        "rru": "addevent",
        "subject": meeting.title,
        "startdt": _ensure_timezone(
            meeting.meeting_date
        ).isoformat(),
        "enddt": _ensure_timezone(
            meeting.meeting_end_date
        ).isoformat(),
        "body": meeting.description or "",
        "location": _meeting_location(meeting),
    }

    return (
        "https://outlook.live.com/calendar/0/deeplink/compose?"
        + urlencode(params)
    )


# ===========================================================
# Microsoft 365
# ===========================================================

def office365_calendar_url(meeting):
    params = {
        "path": "/calendar/action/compose",
        "rru": "addevent",
        "subject": meeting.title,
        "startdt": _ensure_timezone(
            meeting.meeting_date
        ).isoformat(),
        "enddt": _ensure_timezone(
            meeting.meeting_end_date
        ).isoformat(),
        "body": meeting.description or "",
        "location": _meeting_location(meeting),
    }

    return (
        "https://outlook.office.com/calendar/0/deeplink/compose?"
        + urlencode(params)
    )


# ===========================================================
# ICS Generator
# ===========================================================

def generate_ics(meeting):
    uid = f"{meeting.pk}@bakgomong.org"

    ics = f"""BEGIN:VCALENDAR
VERSION:2.0
PRODID:-//Bakgomong Ba Ga Maila//Meetings//EN
CALSCALE:GREGORIAN
METHOD:PUBLISH

BEGIN:VTIMEZONE
TZID:Africa/Johannesburg
X-LIC-LOCATION:Africa/Johannesburg
BEGIN:STANDARD
TZOFFSETFROM:+0200
TZOFFSETTO:+0200
TZNAME:SAST
DTSTART:19700101T000000
END:STANDARD
END:VTIMEZONE

BEGIN:VEVENT
UID:{uid}
DTSTAMP:{_calendar_utc(timezone.now())}
DTSTART;TZID=Africa/Johannesburg:{_calendar_datetime(meeting.meeting_date)}
DTEND;TZID=Africa/Johannesburg:{_calendar_datetime(meeting.meeting_end_date)}
SUMMARY:{meeting.title}
DESCRIPTION:{meeting.description or ""}
LOCATION:{_meeting_location(meeting)}
STATUS:CONFIRMED
SEQUENCE:0
END:VEVENT

END:VCALENDAR
"""

    response = HttpResponse(
        ics,
        content_type="text/calendar; charset=utf-8",
    )

    response[
        "Content-Disposition"
    ] = f'attachment; filename="{meeting.slug}.ics"'

    return response