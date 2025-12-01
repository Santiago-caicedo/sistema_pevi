from django.contrib.auth.backends import ModelBackend
from django.contrib.auth import get_user_model
from django.db.models import Q

User = get_user_model()

class EmailOrUsernameModelBackend(ModelBackend):
    """
    Permite iniciar sesión usando el username O el email.
    """
    def authenticate(self, request, username=None, password=None, **kwargs):
        try:
            # Buscamos un usuario que coincida por username O por email
            user = User.objects.get(Q(username__iexact=username) | Q(email__iexact=username))
        except User.DoesNotExist:
            return None
        except User.MultipleObjectsReturned:
            # Si por error hay dos usuarios con el mismo email, retorna el primero
            user = User.objects.filter(Q(username__iexact=username) | Q(email__iexact=username)).order_by('id').first()

        if user and user.check_password(password) and self.user_can_authenticate(user):
            return user
        return None