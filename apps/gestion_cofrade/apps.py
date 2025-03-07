from django.apps import AppConfig


class GestionCofradeConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.gestion_cofrade'

    def ready(self):
        import apps.gestion_cofrade.signals  # Importa las señales al iniciar la aplicación
