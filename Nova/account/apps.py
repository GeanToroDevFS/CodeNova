from django.apps import AppConfig


class AccountConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'account'
    
    def ready(self):
        import account.signals  # Importa signals aquí, después de que las apps estén listas
