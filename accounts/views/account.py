from accounts.forms import AccountUpdateForm, MemberForm
from django.contrib.auth import  get_user_model
from django.shortcuts import redirect, render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
import logging
from django.db import transaction
from django.http import HttpResponseForbidden
from django_q.tasks import async_task
from accounts.models import Family
from utilities.choices import PaymentStatus, Role


logger = logging.getLogger("accounts")
User = get_user_model()
EXECUTIVE_ROLES = [
    Role.CLAN_CHAIRPERSON,
    Role.DEP_CHAIRPERSON,
    Role.SECRETARY,
    Role.DEP_SECRETARY,
    Role.TREASURER,
    Role.KGOSANA,

]

@login_required
def user_details(request, username):
    model = get_object_or_404(get_user_model().objects.all(), username=username)
    template = "accounts/profile.html"
    context = {
        "user": model
    }
    return render(request, template, context)

@login_required
def account_overview(request, username):
    context = {}
    users = get_user_model().objects.filter(is_active=True).select_related('family').prefetch_related('member_contributions', 'payments')
    model = get_object_or_404(users, username=username)
    
    context['user'] = model
    if request.user.role not in EXECUTIVE_ROLES  and request.user != model:
        template = "accounts/profile.html"
    else:
        template = "accounts/account-overview.html"
        mc = model.member_contributions.all()
        context['contributions'] =mc.order_by('-due_date')
        context['pending_invoices'] =mc.filter(is_paid__in=[PaymentStatus.PENDING, PaymentStatus.AWAITING_APPROVAL]).order_by('-due_date')
        context['unpaid_invoices'] =mc.filter(is_paid=PaymentStatus.NOT_PAID).order_by('-due_date')
        if request.user == model:
            context['latest_unpaid'] = mc.filter(is_paid=PaymentStatus.NOT_PAID).order_by('-due_date').first()
    
   
    return render(request, template, context)

@login_required
def account_update(request):
    template = "accounts/my-account.html"
 
    if request.method == 'POST':
        form = AccountUpdateForm(instance=request.user, data=request.POST, files=request.FILES)
        if form.is_valid():
            form.save()
            messages.success(request, "Your information was updated successfully")
            return redirect("accounts:profile-update")
        else:
            messages.error(request, "Please fix the errors below.")
            return render(request, template, {"form": form})
         
    form = AccountUpdateForm(instance=request.user)  
    return render(request, template, {"form": form})


@login_required
def get_members(request, family_slug):
    family = get_object_or_404(Family, slug=family_slug)
    members = get_user_model().objects.filter(is_approved=True, family=family).order_by("username").select_related("family")
    return render(request, 'members/members.html', {'members': members, 'family': family})

@login_required
def add_member(request, family_slug):
    family = get_object_or_404(Family, slug=family_slug)
    
    template_name = "members/add-member.html"
    success_url = "accounts:get-members"
    
    if not (request.user.is_staff or getattr(request.user, "family", None) == family):
        return HttpResponseForbidden()
    
    if request.method == "POST":
        form = MemberForm(data=request.POST, files=request.FILES)
        if form.is_valid():
            # role = form.cleaned_data['role']
            # EXECUTIVE_ROLES = [
            #     Role.CLAN_CHAIRPERSON,
            #     Role.DEP_CHAIRPERSON,
            #     Role.SECRETARY,
            #     Role.DEP_SECRETARY,
            #     Role.TREASURER,
            #     Role.KGOSANA,
            # ]
            # if role in EXECUTIVE_ROLES:
            #     executive = User.objects.filter(role=role).first()
            #     if executive:
            #         messages.error(request, f'Sorry, only one member can be {role}. Please choose another role')
            #         return render(
            #             request=request, template_name=template_name, context={"form": form}
            #         )
            try:
                with transaction.atomic():
                    user = form.save(commit=False)
                    user.is_active = False
                    user.is_email_activated = False
                    user.role = Role.MEMBER
                    user.save()
                    
                # queue verification email (non-blocking) via django-q
                async_task("accounts.tasks.send_sms_task", user.pk)
                async_task("accounts.tasks.send_verification_email_task", user.pk)
                async_task("accounts.tasks.send_notification_new_member_task", user.pk)
                logger.info("Queued verification email for user %s (pk=%s)", user.username, user.pk)
                messages.success(
                    request,
                    "Member added. A verification email has been queued for the member; they must confirm before they can log in."
                )
                return redirect("accounts:get-members", family_slug=family.slug)
            except Exception:
                logger.exception("Failed to add member to family %s", family_slug)
                messages.error(request, "Something went wrong while adding the member. Try again.")
                return render(request, template_name, {"form": form, "family": family})
        else:
            messages.error(request, "Something went wrong while adding member")
            return render(
                request=request, template_name=template_name, context={"form": form}
            )
    else:
        form = MemberForm()
    return render(request=request, template_name=template_name, context={"form": form, "family": family})

@login_required
def update_member(request, family_slug, username):
    """
    Update a family member. Only staff or members of the family may update.
    """
    family = get_object_or_404(Family, slug=family_slug)
    if not (request.user.is_staff or getattr(request.user, "family", None) == family):
        return HttpResponseForbidden()
    
    member = get_object_or_404(get_user_model(), username=username, family=family)
    
    template_name = "members/add-member.html"
    
    if request.method == "POST":
        form = MemberForm(request.POST, instance=member)
        if form.is_valid():
            try:
                with transaction.atomic():
                    form.save()
                messages.success(request, "Member updated successfully.")
                return redirect("accounts:get-members", family_slug=family.slug)
            except Exception:
                logger.exception("Failed to update member %s in family %s", username, family_slug)
                messages.error(request, "Something went wrong while updating the member. Try again.")
        else:
            messages.error(request, "Please fix the errors below.")
    else:
        form = MemberForm(instance=member)
    
    return render(request, template_name, {"form": form, "family": family, "member": member})

@login_required
def delete_member(request, family_slug, username):
    """
    Delete a family member. Only staff or family members may delete. Requires POST to perform delete.
    """
    family = get_object_or_404(Family, slug=family_slug)
    if not (request.user.is_staff or getattr(request.user, "family", None) == family):
        return HttpResponseForbidden()
    
    member = get_object_or_404(get_user_model(), username=username, family=family)
    
    # Prevent accidental GET deletes; show confirmation template
    if request.method == "POST":
        try:
            member.delete()
            messages.success(request, "Member deleted successfully.")
            return redirect("accounts:get-members", family_slug=family.slug)
        except Exception:
            logger.exception("Failed to delete member %s from family %s", username, family_slug)
            messages.error(request, "Could not delete member. Try again.")
            return redirect("accounts:get-members", family_slug=family.slug)
    
    return render(request, "members/confirm_delete.html", {"member": member, "family": family})
