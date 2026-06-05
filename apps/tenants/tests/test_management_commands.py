from types import SimpleNamespace
from unittest.mock import Mock

import pytest
from django.core.management import call_command
from django.test import override_settings

from apps.tenants.management.commands import bootstrap_demo_tenant as command_module


@pytest.mark.django_db(transaction=False)
class TestBootstrapDemoTenantCommand:
    def test_skips_when_disabled(self, monkeypatch):
        ensure_demo_tenant = Mock()
        monkeypatch.setattr(command_module, "ensure_demo_tenant", ensure_demo_tenant)

        with override_settings(DEMO_TENANT_ENABLED=False):
            call_command("bootstrap_demo_tenant")

        ensure_demo_tenant.assert_not_called()

    def test_creates_demo_tenant_and_domain(self, monkeypatch):
        result = SimpleNamespace(
            tenant_created=False,
            domain_created=False,
            tenant=SimpleNamespace(schema_name="colegioobjetivo"),
            domain=SimpleNamespace(domain="localhost"),
        )
        ensure_demo_tenant = Mock(return_value=result)
        monkeypatch.setattr(command_module, "ensure_demo_tenant", ensure_demo_tenant)

        with override_settings(DEMO_TENANT_ENABLED=True):
            call_command("bootstrap_demo_tenant")

        ensure_demo_tenant.assert_called_once_with()

    def test_returns_warning_when_helper_is_disabled(self, monkeypatch):
        ensure_demo_tenant = Mock(return_value=None)
        monkeypatch.setattr(command_module, "ensure_demo_tenant", ensure_demo_tenant)

        with override_settings(DEMO_TENANT_ENABLED=True):
            call_command("bootstrap_demo_tenant")

        ensure_demo_tenant.assert_called_once_with()
