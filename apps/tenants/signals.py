from django.conf import settings
from django.db import connection
from django.db.models.signals import post_migrate
from django.dispatch import receiver

from apps.tenants.bootstrap import ensure_demo_tenant


@receiver(post_migrate)
def create_demo_tenant_on_post_migrate(sender, app_config, **kwargs):
    if app_config.name != "apps.tenants":
        return
    if not settings.DEMO_TENANT_ENABLED:
        return
    if not hasattr(connection, "tenant"):
        return

    ensure_demo_tenant()
