from accounts.forms import UserLoginForm, RegistrationForm
from django.contrib.auth import login, logout, authenticate, get_user_model
from accounts.models import Family
from accounts.utils.custom_mail import send_email_confirmation_email, send_html_email, send_verification_email
from django_q.tasks import async_task
from django.shortcuts import redirect, render, get_object_or_404
from accounts.utils.decorators import user_not_authenticated
from accounts.utils.tokens import account_activation_token, verify_activation_token
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.conf import settings
from django.db import transaction
import logging, jwt


logger = logging.getLogger("accounts")
User = get_user_model()



@user_not_authenticated
def custom_login(request):
    next_page = request.GET.get("next", None)
    template_name = "accounts/login.html"
    success_url = "accounts:dashboard"
    if next_page:
        success_url = next_page

    if request.method == "POST":
        form = UserLoginForm(request=request, data=request.POST)
        if form.is_valid():
            user = authenticate(
                username=form.cleaned_data["username"],
                password=form.cleaned_data["password"],
            )
            if user is not None and user.is_active:
                login(request, user)
                messages.success(
                    request, f"Hello {user.username}! You have been logged in"
                )
                return redirect(success_url)
        else:
            # form is invalid; avoid using cleaned_data (may not exist)
            username = request.POST.get("username")
            account = User.objects.filter(username=username).first() if username else None
            if account and not account.is_active:
                messages.error(
                    request,
                    f"Account is not active. An activation email was sent to {account.email}."
                )
                sent = send_verification_email(account, request)
                if not sent:
                    logger.error("Failed to send activation email to %s", account.username)
                return redirect("accounts:login")

            # Render login with form errors
            return render(
                request=request, template_name=template_name, context={"form": form}
            )

    form = UserLoginForm()
    return render(request=request, template_name=template_name, context={"form": form})

@login_required
def custom_logout(request):
    logout(request)
    messages.info(request, "Logged out successfully!")
    return redirect("accounts:login")

@user_not_authenticated
def activate(request, uidb64, token):
    User = get_user_model()
    user = None

    try:
        payload = jwt.decode(uidb64, settings.SECRET_KEY, algorithms=['HS256'])
        user = User.objects.get(pk=payload["user_id"], username=payload["username"])
    except (User.DoesNotExist, jwt.ExpiredSignatureError, jwt.DecodeError) as e:
        logger.error(f"Activation error: {e}")
        user = None

    
    if user and account_activation_token.check_token(user, token):
        

        
        if not user.is_active:
            user.is_active = True
            
            user.save(update_fields=["is_active"])

        messages.success(
            request,
            "Thank you for confirming your email. You can now log in."
        )
        return redirect("accounts:login")

    if user:
        messages.error(
            request,
            f"Activation link is expired! A new activation link has been sent to {user.email}."
        )
        async_task("accounts.tasks.send_verification_email_task", user.pk)
    else:
        messages.error(request, "Invalid activation link. Please request a new one.")

    return redirect("accounts:login")

def confirm_email(request, uidb64, token):
    logout(request)
    User = get_user_model()
    try:
        payload = jwt.decode(uidb64, settings.SECRET_KEY, algorithms=['HS256'])
        user = User.objects.get(pk=payload["user_id"], username=payload["username"])
    except:
        user = None
    
    if user is not None and account_activation_token.check_token(user, token):
        user.is_active = True
        user.is_email_activated = True
        user.save(update_fields=["is_active", "is_email_activated"])

        messages.success(
            request,
            "Thank you for your email confirmation. Now you can login to your account with your new email.",
        )

        return redirect("accounts:login")
    
    else:
        messages.error(request, f"Email confirmation link is expired! A new confirmation link was sent to {user.email}")
        async_task("accounts.tasks.send_email_confirmation_task", user.pk, user.email)

    return redirect("accounts:login")

@user_not_authenticated
def register(request):
    # send_mail_to_everyone()
    template_name = "accounts/register.html"
    success_url = "dashboard:index"
    
    family = Family.objects.first()

    if request.method == "POST":
        form = RegistrationForm(request.POST)
        if form.is_valid():
            try:
                with transaction.atomic():
                    user = form.save(commit=False)
                    # keep user inactive until email verification completes
                    user.is_active = False
                    user.is_email_activated = False
                    if family:
                        user.family = family
                    user.save()
 
                # queue verification email (non-blocking)
                async_task("accounts.tasks.send_verification_email_task", user.pk)
                messages.success(
                    request,
                    f"Dear {user.username}, please check {user.email} for an activation link. Check your spam folder."
                )

                # don't auto-login until email is verified; send user to activation-sent page
                return redirect("accounts:login")
            except Exception as e:
                logger.exception("Registration failed")
                messages.error(request, "Something went wrong while signing up. Try again.")
        else:
            messages.error(request, "Please fix the errors below.")
            return render(request=request, template_name=template_name, context={"form": form})
    
    form = RegistrationForm()
    return render(request=request, template_name=template_name, context={"form": form})

@user_not_authenticated
def activation_sent(request):
    return render(request, "accounts/activation_sent.html")
