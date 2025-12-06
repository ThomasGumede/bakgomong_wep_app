from django.contrib.auth.backends import ModelBackend
from django.contrib.auth import get_user_model
from django.db.models import Q

UserModel = get_user_model()

class EmailBackend(ModelBackend):
    def authenticate(self, request, username=None, password=None, **kwargs):
        try:
            user = get_user_model().objects.get(Q(username__iexact=username) | Q(email__iexact=username))
        except get_user_model().DoesNotExist:
            get_user_model()().set_password(password)
            return
        except get_user_model().MultipleObjectsReturned:
            user = get_user_model().objects.filter(Q(username__iexact=username) | Q(email__iexact=username)).order_by('id').first()

        if user.check_password(password) and self.user_can_authenticate(user):
            return user