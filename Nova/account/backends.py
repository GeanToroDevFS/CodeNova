# account/backends.py
from django.contrib.auth.backends import ModelBackend
from django.contrib.auth import get_user_model
from django.db.models import Q

Usuario = get_user_model()

class CustomAuthBackend(ModelBackend):
    """
    Permite login por username o email, siempre que el usuario esté activo (estado=True).
    """

    def authenticate(self, request, username=None, password=None, **kwargs):
        if not username or not password:
            return None

        username = username.strip()  # quita espacios
        try:
            user = Usuario.objects.get(
                Q(username__iexact=username) | Q(email__iexact=username)
            )
        except Usuario.DoesNotExist:
            return None
        except Usuario.MultipleObjectsReturned:
            return None

        # Verifica que el usuario esté activo y que la contraseña coincida
        if user.estado and user.is_active and user.check_password(password):
            return user
        return None

    def get_user(self, user_id):
        try:
            user = Usuario.objects.get(pk=user_id)
            return user if user.estado and user.is_active else None
        except Usuario.DoesNotExist:
            return None
