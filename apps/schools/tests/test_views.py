import pytest
from django.urls import reverse

from apps.accounts.models import User
from apps.schools.models import Unit
from apps.tenants.models import Tenant


@pytest.fixture
def authenticated_user(db):
    return User.objects.create_user(
        username="coord",
        email="coord@gradecerta.com",
        password="testpass12345",
    )


@pytest.fixture
def tenant(db):
    return Tenant.objects.create(name="Escola Teste", schema_name="escola_teste")


@pytest.mark.django_db
class TestSchoolsViews:
    def test_index_page_is_available_for_authenticated_users(self, client, authenticated_user):
        client.force_login(authenticated_user)

        response = client.get(reverse("schools:index"))

        assert response.status_code == 200
        assert "Estrutura escolar" in response.content.decode()

    def test_unit_list_shows_created_units(self, client, authenticated_user, tenant):
        client.force_login(authenticated_user)
        Unit.objects.create(
            tenant=tenant,
            name="Unidade Centro",
            status=Unit.StatusChoices.ACTIVE,
            default_settings={},
        )

        response = client.get(reverse("schools:unit-list"))

        assert response.status_code == 200
        assert "Unidade Centro" in response.content.decode()

    def test_unit_create_persists_object(self, client, authenticated_user, tenant):
        client.force_login(authenticated_user)

        response = client.post(
            reverse("schools:unit-create"),
            data={
                "tenant": tenant.pk,
                "code": "UN-02",
                "name": "Unidade Sul",
                "status": Unit.StatusChoices.ACTIVE,
                "timezone": "America/Sao_Paulo",
                "default_settings": "{}",
            },
        )

        assert response.status_code == 302
        assert Unit.objects.filter(name="Unidade Sul").exists()
