import pytest

from apps.tenants.models import Tenant


@pytest.fixture
def user_password():
    return "testpass12345"


@pytest.fixture
def user_email():
    return "test@gradecerta.com"


@pytest.fixture
def tenant(db):
    return Tenant.objects.create(name="Escola Teste", schema_name="escola_teste")


class SetTenantMiddleware:
    """Middleware de teste que injeta request.tenant para simular django-tenants.

    Em produção, o django-tenants middleware faz isso automaticamente.
    Em testes com SQLite (sem schemas), injetamos o tenant manualmente
    pegando o primeiro Tenant do banco (criado pela fixture ``tenant``).
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if not hasattr(request, "tenant") or request.tenant is None:
            request.tenant = Tenant.objects.first()
        return self.get_response(request)


@pytest.fixture(autouse=True)
def inject_tenant_middleware(settings):
    """Adiciona SetTenantMiddleware ao MIDDLEWARE em testes."""
    settings.MIDDLEWARE = [
        "conftest.SetTenantMiddleware",
    ] + list(settings.MIDDLEWARE)