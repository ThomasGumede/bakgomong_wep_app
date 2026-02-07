from django.contrib import admin, messages
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _
from django.contrib.auth.admin import UserAdmin
from django_q.tasks import async_task
import logging
from django.db import models
from django.db.models import Count

from accounts.models import Account, ClanDocument, Family, Meeting
from utilities.choices import Role

logger = logging.getLogger("accounts")

@admin.action(description="Approve selected members/family")
def approve_members(modeladmin, request, queryset):
    if not request.user.role in [Role.CLAN_CHAIRPERSON, Role.DEP_CHAIRPERSON, Role.DEP_SECRETARY, Role.KGOSANA, Role.SECRETARY, Role.TREASURER, Role.MMAKGOSANA] or not request.user.is_family_leader or not request.user.is_superuser:
        messages.error(request, "Only executives are allowed to approve members.")
        return
    
    queryset.update(
        is_approved=True,
    )
    messages.success(request, f"{queryset.count()} member(s) or families approved successfully.")
    
@admin.action(description="Welcome new member")
def welcome_new_member(modeladmin, request, queryset):
    if not request.user.role in [Role.CLAN_CHAIRPERSON, Role.DEP_CHAIRPERSON, Role.DEP_SECRETARY, Role.KGOSANA, Role.SECRETARY, Role.TREASURER, Role.MMAKGOSANA] or not request.user.is_family_leader or not request.user.is_superuser:
        messages.error(request, "Only executives are allowed to welcome new members.")
        return
    
    for account in queryset:
        async_task("accounts.tasks.welcome_member_task", account.id)
    messages.success(request, f"Welcome tasks queued for {queryset.count()} new member(s).")

@admin.action(description="Notify members of new meeting")
def notify_members_of_new_meeting(modeladmin, request, queryset):
    if not request.user.role in [Role.CLAN_CHAIRPERSON, Role.DEP_CHAIRPERSON, Role.DEP_SECRETARY, Role.KGOSANA, Role.SECRETARY, Role.TREASURER, Role.MMAKGOSANA] or not request.user.is_family_leader or not request.user.is_superuser:
        messages.error(request, "Only executives are allowed to notify members of new meetings.")
        return
    
    for meeting in queryset:
        async_task("accounts.tasks.send_notification_new_meeting_to_members_task", meeting.id)
    messages.success(request, f"Notification tasks queued for {queryset.count()} meeting(s).")
# ------------------------------------------------------------
# Inline display: show all members under a family
# ------------------------------------------------------------
class AccountInline(admin.TabularInline):
    model = Account
    fields = ("first_name", "email", "phone", "role", "is_active", "is_approved")
    extra = 0
    readonly_fields = ("first_name", "email", "phone", "role")
    can_delete = False
    show_change_link = True


# ------------------------------------------------------------
# Family Admin
# ------------------------------------------------------------
@admin.register(Family)
class FamilyAdmin(admin.ModelAdmin):
    def leader_display(self, obj):
        return obj.leader.first_name if obj.leader else "—"
    leader_display.short_description = _("Leader")

    def member_count(self, obj):
        # use annotated value if present to avoid extra query
        return getattr(obj, "member_count", obj.members.count())
    member_count.short_description = _("Members")
    
    list_display = ("name", "leader_display", "member_count", "created", "is_approved")
    search_fields = ("name", "leader__first_name", "leader__email")
    list_filter = ("created", "is_approved",)
    prepopulated_fields = {"slug": ("name",)}
    inlines = [AccountInline]
    ordering = ("-created",)
    actions = [approve_members]
    raw_id_fields = ("leader",)

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        # annotate member counts once
        return qs.annotate(member_count=Count("members"))


# ------------------------------------------------------------
# Account Admin
# ------------------------------------------------------------
@admin.register(Account)
class AccountAdmin(UserAdmin):
    def profile_image_preview(self, obj):
        if obj.profile_image:
            return format_html('<img src="{}" width="50" height="50" style="border-radius:50%;" />', obj.profile_image.url)
        return "—"
    profile_image_preview.short_description = _("Profile Image Preview")
    
    list_display = ("profile_image_preview", "username", "first_name", "email", "family", "role", "is_active", "is_approved")
    list_filter = ("role", "is_active", "gender", "is_approved", "created")
    search_fields = ("username", "first_name", "email", "phone", "family__name")
    list_select_related = ("family",)
    autocomplete_fields = ("family",)
    ordering = ("-created",)
    list_per_page = 50
    date_hierarchy = "created"
    readonly_fields = ("created", "updated", "profile_image_preview", "last_login")
    filter_horizontal = ("groups",)
    actions = [approve_members, welcome_new_member]
    add_fieldsets = (
        (_("Personal Info"), {
            "fields": (
                "profile_image",
                "username",
                "first_name",
                "last_name",
                "id_number",
                "birth_date",
                "email",
                "title",
                "gender",
                "password1",
                "password2",
            ),
        }),
        (_("Member Info"), {
            "fields": (
                "biography",
                "employment_status",
                "member_classification",
                "maiden_name",
                "family",
            ),
        }),
        (_("Contact Information"), {
            "fields": (
                "phone",
                "address",
            ),
        }),
        (_("Permissions"), {
            "fields": (
                "role",
                "is_active",
                "is_staff",
                "is_approved",
                "is_superuser",
                "is_family_leader",
                
            ),
        }),
    )
    fieldsets = (
        (_("Personal Information"), {
            "fields": (
                "profile_image",
                "profile_image_preview",
                "title",
                "first_name",
                "last_name",
                "id_number",
                "birth_date",
                "email",
                "phone",
                "gender",
                "address",
            ),
        }),
        (_("Member Info"), {
            "fields": (
                "biography",
                "employment_status",
                "member_classification",
                "maiden_name",
            ),
        }),
        (_("Clan Information"), {
            "fields": ("role", "family", "is_family_leader"),
        }),
        (_("Permissions & Status"), {
            "fields": ("is_active", "is_staff", "is_superuser", "is_approved",),
        }),
        (_("Password Management"), {
            "classes": ("collapse",),
            "fields": ("password",),
            "description": _("Reset password (collapsible section)"),
        }),
        (_("Important Dates"), {
            "fields": ("last_login", "created", "updated"),
        }),
    )


@admin.register(ClanDocument)
class ClanDocumentAdmin(admin.ModelAdmin):
    list_display = ("title", "category", "visibility", "family", "uploaded_by", "created")
    list_filter = ("visibility", "category", "family")
    search_fields = ("title", "description")
    prepopulated_fields = {"slug": ("title",)}

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        user = request.user

        # Admins see all documents
        if user.is_superuser or getattr(user, "role", "") == Role.CLAN_CHAIRPERSON:
            return qs

        # Family leaders see their family's documents
        if getattr(user, "role", "") == Role.FAMILY_LEADER:
            return qs.filter(models.Q(visibility="clan") | models.Q(family=user.family))

        # Regular members see only clan-wide and their family’s documents
        return qs.filter(
            models.Q(visibility="clan") |
            models.Q(family=user.family, visibility="family")
        )

@admin.register(Meeting)
class MeetingAdmin(admin.ModelAdmin):
    list_display = ("title", "meeting_type", "audience", "meeting_date", "created_by", "family")
    list_filter = ("meeting_type", "audience", "meeting_date", "family")
    search_fields = ("title", "description")
    prepopulated_fields = {"slug": ("title",)}
    ordering = ("-meeting_date",)
    actions = [notify_members_of_new_meeting]