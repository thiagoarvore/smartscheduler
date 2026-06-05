from django.apps import AppConfig


class SchoolsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.schools"
    verbose_name = "Estrutura escolar"

    def ready(self):
        from . import signals  # noqa: F401
