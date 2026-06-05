from dataclasses import dataclass

from django.conf import settings
from django.core.management.base import CommandError
from django_tenants.utils import schema_context

from apps.tenants.models import Domain, Tenant


@dataclass(frozen=True)
class DemoTenantBootstrapResult:
    tenant: Tenant
    tenant_created: bool
    domain: Domain
    domain_created: bool


def ensure_demo_tenant() -> DemoTenantBootstrapResult | None:
    if not settings.DEMO_TENANT_ENABLED:
        return None

    tenant_schema = settings.DEMO_TENANT_SCHEMA_NAME
    tenant_name = settings.DEMO_TENANT_NAME
    tenant_domain = settings.DEMO_TENANT_DOMAIN

    with schema_context("public"):
        tenant, tenant_created = Tenant.objects.get_or_create(
            schema_name=tenant_schema,
            defaults={
                "name": tenant_name,
                "paid_until": None,
                "on_trial": True,
            },
        )

        updated_fields = []
        if tenant.name != tenant_name:
            tenant.name = tenant_name
            updated_fields.append("name")
        if tenant.paid_until is not None:
            tenant.paid_until = None
            updated_fields.append("paid_until")
        if tenant.on_trial is not True:
            tenant.on_trial = True
            updated_fields.append("on_trial")
        if updated_fields:
            tenant.save(update_fields=updated_fields)

        domain, domain_created = Domain.objects.get_or_create(
            domain=tenant_domain,
            defaults={
                "tenant": tenant,
                "is_primary": True,
            },
        )

        if domain.tenant_id != tenant.id:
            raise CommandError(
                f"Domain '{tenant_domain}' already belongs to another tenant."
            )

        domain_updates = []
        if domain.is_primary is not True:
            domain.is_primary = True
            domain_updates.append("is_primary")
        if domain_updates:
            domain.save(update_fields=domain_updates)

    return DemoTenantBootstrapResult(
        tenant=tenant,
        tenant_created=tenant_created,
        domain=domain,
        domain_created=domain_created,
    )
