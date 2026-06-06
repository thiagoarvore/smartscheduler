from django.apps import AppConfig


class SchedulingConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.scheduling"
    verbose_name = "Scheduling"

    def ready(self):
        from . import signals  # noqa: F401
