from django.apps import AppConfig


class GestionConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'gestion'

    def ready(self):
        """Registra los signals cuando la app está lista."""
        import gestion.signals  # noqa: F401
