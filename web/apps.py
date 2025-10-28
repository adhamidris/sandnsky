from django.apps import AppConfig
from django.utils.module_loading import autodiscover_modules


class WebConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'web'

    def ready(self):
        # Ensure signals are imported once the app registry is ready.
        autodiscover_modules("signals")
