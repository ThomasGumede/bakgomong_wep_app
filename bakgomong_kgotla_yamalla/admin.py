from django.contrib import admin, messages
from django.utils.html import format_html
from django.core.exceptions import PermissionDenied
from django.utils.translation import gettext_lazy as _
from django_q.tasks import async_task
import logging
from django.db import models
from django.db.models import Count
from django.shortcuts import get_object_or_404, redirect, render

from bakgomong_kgotla_yamalla.models import ClanDocument, Meeting, KgotlaBalance, KgotlaExpense
from utilities.choices import Role

logger = logging.getLogger("bakgomong_kgotla_yamalla")

executive_roles = [Role.CLAN_CHAIRPERSON, Role.DEP_CHAIRPERSON, Role.DEP_SECRETARY, Role.KGOSANA, Role.SECRETARY, Role.TREASURER, Role.MMAKGOSANA, Role.SPONSOR]

@admin.action(description="Notify members of new meeting")
def notify_members_of_new_meeting(modeladmin, request, queryset):
    if not request.user.role in executive_roles or not request.user.is_family_leader or not request.user.is_superuser:
        messages.error(request, "Only executives are allowed to notify members of new meetings.")
        return
    
    for meeting in queryset:
        async_task("bakgomong_kgotla_yamalla.tasks.send_notification_new_meeting_to_members_task", meeting.id)
    messages.success(request, f"Notification tasks queued for {queryset.count()} meeting(s).")
    

@admin.register(KgotlaExpense)
class KgotlaExpenseAdmin(admin.ModelAdmin):
    def has_change_permission(self, request, obj = None):
        user = request.user
        if not user.is_superuser and getattr(user, "role", None) not in [Role.CLAN_CHAIRPERSON, Role.SECRETARY]:
            return False
        
        return super().has_change_permission(request, obj)
    
    def save_model(self, request, obj, form, change):
        user = request.user
        if not user.is_superuser and getattr(user, "role", None) not in [Role.CLAN_CHAIRPERSON, Role.SECRETARY]:
            raise PermissionDenied("You do not have permission to edit the Kgotla Expenses.")
        
        obj.added_by = user
        return super().save_model(request, obj, form, change)
    
    list_display = ("title", "amount", "incurred_date", "added_by", "created")
    list_filter = ("incurred_date",)
    search_fields = ("title", "description")
    prepopulated_fields = {"slug": ("title",)}
    ordering = ("-incurred_date",)

@admin.register(KgotlaBalance)
class KgotlaBalanceAdmin(admin.ModelAdmin):
    def has_add_permission(self, request):
        # Prevent adding new instances if one already exists
        if KgotlaBalance.objects.exists():
            return False
        return super().has_add_permission(request)
    def has_delete_permission(self, request, obj=None):
        # Prevent deletion of the singleton instance
        return False
    
    def has_change_permission(self, request, obj = None):
        user = request.user
        if not user.is_superuser and getattr(user, "role", None) not in [Role.CLAN_CHAIRPERSON, Role.SECRETARY]:
            return False
        
        return super().has_change_permission(request, obj)
    
    def save_model(self, request, obj, form, change):
        user = request.user
        if not user.is_superuser and getattr(user, "role", None) not in [Role.CLAN_CHAIRPERSON, Role.SECRETARY]:
            raise PermissionDenied("You do not have permission to edit the Kgotla Balance.")
        
        obj.updated_by = user
        return super().save_model(request, obj, form, change)
    
    def changelist_view(self, request, extra_context = None):
        obj = KgotlaBalance.load()
        return redirect(f"admin:bakgomong_kgotla_yamalla_kgotlabalance_change", obj.id)
    
    list_display = ("title", "balance", "updated_by", "updated")
    list_filter = ("updated",)
    search_fields = ("title",)

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