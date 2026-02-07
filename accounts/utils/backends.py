import logging
from typing import Optional, Any

from django.contrib.auth.backends import ModelBackend
from django.contrib.auth import get_user_model
from django.db.models import Q

UserModel = get_user_model()
logger = logging.getLogger("accounts.backends")


class EmailBackend(ModelBackend):
    def authenticate(self, request: Any, username: Optional[str] = None, password: Optional[str] = None, **kwargs):
        """Authenticate by username, email, or id_number (case-insensitive).

        Improvements:
        - Accepts `email` in kwargs when `username` is not provided
        - Normalizes input
        - Mitigates timing attacks by setting a dummy password on a new user instance
        - Adds logging and type hints
        """
        if username is None:
            username = kwargs.get("username") or kwargs.get("email")

        if not username or password is None:
            return None

        username = str(username).strip()

        try:
            user = UserModel.objects.get(
                Q(username__iexact=username) | Q(email__iexact=username) | Q(id_number__iexact=username)
            )
        except UserModel.DoesNotExist:
            # Mitigate timing attacks by hashing the provided password
            UserModel().set_password(password)
            return None
        except UserModel.MultipleObjectsReturned:
            user = UserModel.objects.filter(
                Q(username__iexact=username) | Q(email__iexact=username)
            ).order_by("id").first()

        try:
            if user and user.check_password(password) and self.user_can_authenticate(user):
                return user
        except Exception:
            logger.exception("Error verifying password for user lookup '%s'", username)

        return None
        
