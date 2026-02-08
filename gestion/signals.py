"""
Signals de Django para el sistema PEVI.
Captura eventos de autenticación para logging.
"""

from django.contrib.auth.signals import user_logged_in, user_logged_out, user_login_failed
from django.dispatch import receiver


@receiver(user_logged_in)
def on_user_logged_in(sender, request, user, **kwargs):
    """Se ejecuta cuando un usuario inicia sesión exitosamente."""
    from .logger import log_login
    log_login(request, user)


@receiver(user_logged_out)
def on_user_logged_out(sender, request, user, **kwargs):
    """Se ejecuta cuando un usuario cierra sesión."""
    from .logger import log_logout
    if user:
        log_logout(request, user)


@receiver(user_login_failed)
def on_user_login_failed(sender, credentials, request, **kwargs):
    """Se ejecuta cuando un intento de login falla."""
    from .logger import log_login_fallido
    username = credentials.get('username', 'desconocido')
    log_login_fallido(request, username)
