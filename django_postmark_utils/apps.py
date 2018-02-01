from django.apps import AppConfig
from django.utils.translation import ugettext_lazy as _


class DjangoPostmarkUtilsConfig(AppConfig):
    name = 'django_postmark_utils'
    verbose_name = _("Django Postmark Utils")

    def ready(self):
        from . import signal_handlers  # noqa: F401
