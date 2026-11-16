from django.urls import path
from bakgomong_kgotla_yamalla.views.clan import clan_expenses, dashboard, home, record_expense
from bakgomong_kgotla_yamalla.views.documents import clan_documents, download_file, upload_document
from bakgomong_kgotla_yamalla.views.meetings import add_to_calendar_apple, clan_meetings, get_clan_meetings_api, meeting_create, meeting_delete, meeting_details, meeting_update

app_name = "bakgomong_kgotla_yamalla"

urlpatterns = [
    path("", home, name="home"),
    path("dashboard", dashboard, name="dashboard"),
    path('dashboard/kgotla-ya-malla-meetings', clan_meetings, name='clan-meetings'),
    path('dashboard/kgotla-ya-malla-meetings/<meeting_slug>', meeting_details, name='meeting-details'),
    path('dashboard/kgotla-ya-malla-documents', clan_documents, name='clan-documents'),
    path('dashboard/kgotla-ya-malla-expenses', clan_expenses, name='clan-expenses'),
    path('dashboard/api/meetings', get_clan_meetings_api, name='get-meetings-api'),
    path('dashboard/documents/<file_id>', download_file, name='download-file'),
    path('dashboard/upload-documents/', upload_document, name='upload-document'),
    path("dashboard/record-expense/", record_expense, name="record-expense"),

    path("dashboard/create-meeting/", meeting_create, name="meeting-create"),
    path("dashboard/<meeting_slug>/edit-meeting/", meeting_update, name="meeting-update"),
    path("dashboard/<meeting_slug>/delete-meeting/", meeting_delete, name="meeting-delete"),
    path("dashboard/<meeting_slug>/add-to-calendar/", add_to_calendar_apple, name="add-to-calendar-apple"),
]
