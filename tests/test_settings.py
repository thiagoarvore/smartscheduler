import pytest


@pytest.mark.django_db
class TestSettings:
    """Sanity checks for project settings."""

    def test_auth_user_model(self, settings):
        assert settings.AUTH_USER_MODEL == "accounts.User"

    def test_tenant_model(self, settings):
        assert settings.TENANT_MODEL == "tenants.Tenant"

    def test_tenant_domain_model(self, settings):
        assert settings.TENANT_DOMAIN_MODEL == "tenants.Domain"

    def test_language_code(self, settings):
        assert settings.LANGUAGE_CODE == "pt-br"

    def test_timezone(self, settings):
        assert settings.TIME_ZONE == "America/Sao_Paulo"

    def test_shared_apps_contains_tenants_and_accounts(self, settings):
        assert "apps.tenants.apps.TenantsConfig" in settings.SHARED_APPS
        assert "apps.accounts.apps.AccountsConfig" in settings.SHARED_APPS


class TestProductionSettings:
    """Tests that only pass in production (PostgreSQL) settings."""

    def test_database_router_is_tenant(self):
        """
        When using PostgreSQL with django-tenants, the router must be present.
        This test checks the production settings, not the test override.
        """
        from config.settings import DATABASE_ROUTERS as PROD_ROUTERS  # noqa: N811

        assert "django_tenants.routers.TenantSyncRouter" in PROD_ROUTERS
