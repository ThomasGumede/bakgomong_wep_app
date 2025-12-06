from django.shortcuts import render, redirect
from django.contrib.auth import get_user_model
from django.contrib import messages
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.utils.http import urlsafe_base64_decode
from django.utils.encoding import force_str
from django.contrib.auth.forms import PasswordChangeForm, PasswordResetForm, SetPasswordForm
from django.shortcuts import render, redirect
from django.contrib.auth.tokens import default_token_generator
import logging

from django_q.tasks import async_task
from accounts.utils.decorators import user_not_authenticated

email_logger = logging.getLogger("emails")
account_logger = logging.getLogger("accounts")

def is_ajax(request):
    return request.headers.get("X-Requested-With") == "XMLHttpRequest"

@login_required
def password_change(request):
    user = request.user
    template = 'accounts/password/change_password.html'
    if request.method == 'POST':
        form = PasswordChangeForm(user, request.POST)
        if form.is_valid():
            form.save()

            messages.success(request, "Your password has been changed")
            return redirect('accounts:profile-update')
        else:
            messages.error(request, "Your password was not changed. Fix errors below")
            return render(request, template, {'form': form})

    form = PasswordChangeForm(user)
    return render(request, template, {'form': form})

@user_not_authenticated
def password_reset_request(request):
    try:
        if request.method == "POST":
            form = PasswordResetForm(request.POST)

            if form.is_valid():
                email = form.cleaned_data["email"]
                User = get_user_model()
                user = User.objects.filter(email__iexact=email).first()

                # Prevent account enumeration
                if user:
                    try:
                        if not user.is_active:
                            async_task("accounts.tasks.send_verification_email_task", user.pk)
                        else:
                            async_task("accounts.tasks.send_password_reset_email_task", user.pk)
                    except Exception:
                        account_logger.exception(f"Failed sending reset email for {email}")

                # AJAX RESPONSE
                if is_ajax(request):
                    return JsonResponse({"success": True})

                # Normal browser response
                messages.success(request, "If an account with that email exists, we have sent password reset instructions.")
                return redirect("accounts:password-reset-sent")

            else:
                # Form invalid
                if is_ajax(request):
                    return JsonResponse({"errors": form.errors}, status=400)

                return render(request, "accounts/password/pwd_reset_form.html", {"form": form})

    except Exception:
        account_logger.exception("Unexpected error in password_reset_request")

        if is_ajax(request):
            return JsonResponse({"success": True})

        messages.success(request, "If an account with that email exists, we have sent password reset instructions.")
        return redirect("accounts:password-reset-sent")

    # GET request
    form = PasswordResetForm()
    return render(request, "accounts/password/pwd_reset_form.html", {"form": form})
def password_reset_sent(request):
    return render(request, "accounts/password/password_email_sent.html")

def password_reset_confirm(request, uidb64, token):
    
    User = get_user_model()
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = User.objects.filter(pk=uid).first()
        print(user)
    except Exception:
        user = None
   
    if user is not None and default_token_generator.check_token(user, token):
        print("USER:", user, "CHECK:", default_token_generator.check_token(user, token))
        if request.method == 'POST':
            form = SetPasswordForm(user, request.POST)
            if form.is_valid():
                form.save()
                messages.success(request, "Your password has been set. You can log in now.")
                return redirect('accounts:login')
        else:
            form = SetPasswordForm(user)

        return render(request, 'accounts/password/pwd_reset_confirm.html', {'form': form})

    messages.error(request, "Password reset link is invalid or expired.")
    return redirect("accounts:reset-password")
