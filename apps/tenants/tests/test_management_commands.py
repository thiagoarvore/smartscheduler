from contextlib import contextmanager
from datetime import date
from types import SimpleNamespace
from unittest.mock import Mock

import pytest
from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import override_settings

from apps.tenants.management.commands import bootstrap_demo_tenant as command_module


@contextmanager
def noop_schema_context(*args, **kwargs):
    yield


@pytest.mark.django_db(transaction=False)
class TestBootstrapDemoTenantCommand:
    def test_skips_when_disabled(self, monkeypatch):
        monkeypatch.setattr(command_module, "schema_context", noop_schema_context)
        tenant_get_or_create = Mock()
        domain_get_or_create = Mock()
        monkeypatch.setattr(
            command_module.Tenant.objects,
            "get_or_create",
            tenant_get_or_create,
        )
        monkeypatch.setattr(
            command_module.Domain.objects,
            "get_or_create",
            domain_get_or_create,
        )

        with override_settings(DEMO_TENANT_ENABLED=False):
            call_command("bootstrap_demo_tenant")

        tenant_get_or_create.assert_not_called()
        domain_get_or_create.assert_not_called()

    def test_creates_demo_tenant_and_domain(self, monkeypatch):
        monkeypatch.setattr(command_module, "schema_context", noop_schema_context)

        tenant = SimpleNamespace(
            id=7,
            schema_name="colegioobjetivo",
            name="Old Name",
            paid_until=date(2026, 1, 1),
            on_trial=False,
            save=Mock(),
        )
        domain = SimpleNamespace(
            tenant_id=7,
            is_primary=False,
            save=Mock(),
        )

        tenant_get_or_create = Mock(return_value=(tenant, False))
        domain_get_or_create = Mock(return_value=(domain, False))
        monkeypatch.setattr(
            command_module.Tenant.objects,
            "get_or_create",
            tenant_get_or_create,
        )
        monkeypatch.setattr(
            command_module.Domain.objects,
            "get_or_create",
            domain_get_or_create,
        )

        with override_settings(
            DEMO_TENANT_ENABLED=True,
            DEMO_TENANT_NAME="Colegio Objetivo",
            DEMO_TENANT_SCHEMA_NAME="colegioobjetivo",
            DEMO_TENANT_DOMAIN="localhost",
        ):
            call_command("bootstrap_demo_tenant")

        tenant_get_or_create.assert_called_once_with(
            schema_name="colegioobjetivo",
            defaults={
                "name": "Colegio Objetivo",
                "paid_until": None,
                "on_trial": True,
            },
        )
        domain_get_or_create.assert_called_once_with(
            domain="localhost",
            defaults={"tenant": tenant, "is_primary": True},
        )
        tenant.save.assert_called_once_with(update_fields=["name", "paid_until", "on_trial"])
        domain.save.assert_called_once_with(update_fields=["is_primary"])

    def test_raises_if_domain_is_owned_by_other_tenant(self, monkeypatch):
        monkeypatch.setattr(command_module, "schema_context", noop_schema_context)

        tenant = SimpleNamespace(
            id=7,
            schema_name="colegioobjetivo",
            name="Colegio Objetivo",
            paid_until=None,
            on_trial=True,
            save=Mock(),
        )
        other_tenant_domain = SimpleNamespace(
            tenant_id=99,
            is_primary=True,
            save=Mock(),
        )

        monkeypatch.setattr(
            command_module.Tenant.objects,
            "get_or_create",
            Mock(return_value=(tenant, True)),
        )
        monkeypatch.setattr(
            command_module.Domain.objects,
            "get_or_create",
            Mock(return_value=(other_tenant_domain, False)),
        )

        with override_settings(DEMO_TENANT_ENABLED=True), pytest.raises(
            CommandError,
            match="already belongs to another tenant",
        ):
            call_command("bootstrap_demo_tenant")
