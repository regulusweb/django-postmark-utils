from django.apps import AppConfig


class DjangoPostmarkUtilConfig(AppConfig):
    name = 'django_postmark_utils'

    def ready(self):
        from . import signal_handlers
