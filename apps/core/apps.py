from django.apps import AppConfig


class CoreConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.core'
    verbose_name = 'Configuración'

    def ready(self):
        pass  # registra las tareas Huey al arrancar la app
