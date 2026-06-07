from types import SimpleNamespace
from unittest.mock import Mock

import pytest

from apps.tenants import signals


@pytest.mark.django_db(transaction=False)
class TestDemoTenantPostMigrateSignal:
    def test_ignores_other_apps(self, monkeypatch):
        ensure_demo_tenant = Mock(return_value=None)
        monkeypatch.setattr(signals, "ensure_demo_tenant", ensure_demo_tenant)
        monkeypatch.setattr(signals, "connection", SimpleNamespace(tenant=object()))

        signals.create_demo_tenant_on_post_migrate(
            sender=object(),
            app_config=SimpleNamespace(name="apps.accounts"),
            verbosity=1,
            interactive=False,
            using="default",
            plan=[],
        )

        ensure_demo_tenant.assert_not_called()

    def test_bootstraps_demo_tenant_for_tenants_app(self, monkeypatch):
        ensure_demo_tenant = Mock(return_value=None)
        monkeypatch.setattr(signals, "ensure_demo_tenant", ensure_demo_tenant)
        monkeypatch.setattr(signals, "connection", SimpleNamespace(schema_name="public"))

        signals.create_demo_tenant_on_post_migrate(
            sender=object(),
            app_config=SimpleNamespace(name="apps.tenants"),
            verbosity=1,
            interactive=False,
            using="default",
            plan=[],
        )

        ensure_demo_tenant.assert_called_once_with()

    def test_ignores_non_public_schema(self, monkeypatch):
        ensure_demo_tenant = Mock(return_value=None)
        monkeypatch.setattr(signals, "ensure_demo_tenant", ensure_demo_tenant)
        monkeypatch.setattr(signals, "connection", SimpleNamespace(schema_name="tenant1"))

        signals.create_demo_tenant_on_post_migrate(
            sender=object(),
            app_config=SimpleNamespace(name="apps.tenants"),
            verbosity=1,
            interactive=False,
            using="default",
            plan=[],
        )

        ensure_demo_tenant.assert_not_called()
