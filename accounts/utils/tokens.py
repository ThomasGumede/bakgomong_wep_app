from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.conf import settings
from datetime import datetime, timedelta, timezone
import jwt
import six



class AccountActivationTokenGenerator(PasswordResetTokenGenerator):

    def _make_hash_value(self, user, timestamp):
       
        return (
            six.text_type(user.pk)
            + six.text_type(timestamp)
            + six.text_type(user.is_active)
        )

account_activation_token = AccountActivationTokenGenerator()


def generate_activation_token(user):

    payload = {
        "user_id": user.id,
        "email": user.email,
        "username": user.username,
        "exp": datetime.now(timezone.utc) + timedelta(hours=24),  
        "iat": datetime.now(timezone.utc),  
        "purpose": "activation"
    }

    token = jwt.encode(payload, settings.SECRET_KEY, algorithm="HS256")
    return token

def verify_activation_token(token):

    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
        if payload.get("purpose") != "activation":
            return None
        return payload
    except jwt.ExpiredSignatureError:
        
        return None
    except jwt.InvalidTokenError:
        
        return None
