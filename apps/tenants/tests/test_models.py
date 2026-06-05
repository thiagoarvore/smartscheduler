import pytest

from apps.tenants.models import Domain, Tenant


@pytest.mark.django_db
class TestTenantModel:
    """Tests for the Tenant model."""

    def test_create_tenant(self):
        tenant = Tenant.objects.create(
            name="Escola Teste",
            schema_name="escola_teste",
        )
        assert tenant.pk is not None
        assert tenant.name == "Escola Teste"
        assert tenant.on_trial is True

    def test_tenant_str(self):
        tenant = Tenant.objects.create(
            name="Escola Beta",
            schema_name="escola_beta",
        )
        assert str(tenant) == "Escola Beta"

    def test_tenant_defaults(self):
        tenant = Tenant.objects.create(
            name="Escola Gamma",
            schema_name="escola_gamma",
        )
        assert tenant.on_trial is True
        assert tenant.paid_until is None
        assert tenant.auto_create_schema is True


class TestDomainModel:
    """Tests for the Domain model (non-schema, unit tests only)."""

    def test_domain_str(self):
        domain = Domain(domain="escola.localhost", tenant=None, is_primary=True)
        assert str(domain) == "escola.localhost"
