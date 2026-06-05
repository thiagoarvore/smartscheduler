from django.conf import settings
from django.core.management.base import BaseCommand

from apps.tenants.bootstrap import ensure_demo_tenant


class Command(BaseCommand):
    help = "Create or update the demo tenant used in local deployments."

    def handle(self, *args, **options):
        if not settings.DEMO_TENANT_ENABLED:
            self.stdout.write(self.style.WARNING("Demo tenant bootstrap is disabled."))
            return

        result = ensure_demo_tenant()
        if result is None:
            self.stdout.write(self.style.WARNING("Demo tenant bootstrap is disabled."))
            return

        action = "created" if result.tenant_created else "updated"
        domain_action = "created" if result.domain_created else "updated"
        self.stdout.write(
            self.style.SUCCESS(
                f"Demo tenant '{result.tenant.schema_name}' {action}; domain '{result.domain.domain}' {domain_action}."
            )
        )
