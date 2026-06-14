"""Testes das views do solver (Sprint 08 itens 3.11, 3.12, 3.13)."""
from __future__ import annotations

from datetime import timedelta

import pytest
from django.contrib.auth import get_user_model
from django.test import Client
from django.urls import reverse
from django.utils import timezone

from apps.scheduling.models import SolverRun, SolverVariant
from apps.scheduling.services.cooldown import check_cooldown


@pytest.fixture
def tenant(db):
    from apps.tenants.models import Tenant

    return Tenant.objects.create(schema_name="t1", name="Tenant 1")


@pytest.fixture
def user(db):
    user_model = get_user_model()
    return user_model.objects.create_user(username="alice", email="[email protected]", password="x")


@pytest.fixture
def school_year(tenant, db):
    from apps.schools.models import SchoolYear

    return SchoolYear.objects.create(
        tenant=tenant,
        name="2026",
        year=2026,
        start_date="2026-02-01",
        end_date="2026-12-15",
    )


@pytest.fixture(autouse=True)
def set_request_tenant(tenant):
    """Anexa `tenant` ao request automaticamente em todos os testes.

    O `TenantMixin` original do projeto (`apps.scheduling.views`) lê
    `self.request.tenant`, que só é setado pelo middleware do
    `django-tenants` em produção. Em test, sem o middleware rodando,
    precisamos setar manualmente.
    """

    # Hack: monkey-patch TenantMixin.get_tenant pra usar nossa fixture
    from apps.scheduling.views import TenantMixin

    original = TenantMixin.get_tenant

    def patched_get_tenant(self):
        return tenant

    TenantMixin.get_tenant = patched_get_tenant
    yield
    TenantMixin.get_tenant = original


@pytest.fixture
def variantes_ativas(tenant, db):
    return SolverVariant.objects.bulk_create(
        [
            SolverVariant(
                tenant=tenant,
                nome=SolverVariant.NomeChoices.A_RESTART,
                is_active=True,
            ),
            SolverVariant(
                tenant=tenant,
                nome=SolverVariant.NomeChoices.B_HILL_CLIMBING,
                is_active=True,
            ),
            SolverVariant(
                tenant=tenant,
                nome=SolverVariant.NomeChoices.C_HYBRID,
                is_active=True,
            ),
        ]
    )


# Cooldown service --------------------------------------------------------


class TestCheckCooldown:
    def test_primeira_execucao_pode_rodar(self, school_year) -> None:
        # Em test, ENVIRONMENT=local → cooldown desativado por default
        result = check_cooldown(school_year)
        assert result.pode_rodar is True

    def test_em_cooldown_quando_forcado(self, school_year, settings) -> None:
        settings.GRADE_CERTA_COOLDOWN_DISABLED = False
        school_year.last_solver_run_at = timezone.now() - timedelta(minutes=10)
        school_year.save()
        result = check_cooldown(school_year)
        assert result.pode_rodar is False
        assert result.em_cooldown is True
        assert "1x por hora" in result.mensagem
        assert "Asia/Tokyo" in result.mensagem

    def test_apos_1h_pode_rodar(self, school_year, settings) -> None:
        settings.GRADE_CERTA_COOLDOWN_DISABLED = False
        school_year.last_solver_run_at = timezone.now() - timedelta(hours=2)
        school_year.save()
        result = check_cooldown(school_year)
        assert result.pode_rodar is True

    def test_cooldown_desativado_em_dev(self, school_year, settings) -> None:
        # Forçar produção pra ver que bloquearia
        settings.GRADE_CERTA_COOLDOWN_DISABLED = False
        school_year.last_solver_run_at = timezone.now() - timedelta(minutes=5)
        school_year.save()
        result_prod = check_cooldown(school_year)
        assert result_prod.pode_rodar is False

        # Agora desativar
        settings.GRADE_CERTA_COOLDOWN_DISABLED = True
        result_dev = check_cooldown(school_year)
        assert result_dev.pode_rodar is True


# Views ------------------------------------------------------------------


class TestRunTimetableView:
    @pytest.fixture
    def client(self, user):
        c = Client()
        c.force_login(user)
        return c

    def test_post_dispara_3_runs(
        self, client, school_year, variantes_ativas
    ) -> None:
        url = reverse("scheduling:run-timetable", args=[school_year.id])
        response = client.post(url)
        assert response.status_code == 302
        # 3 runs criados
        assert SolverRun.objects.filter(school_year=school_year).count() == 3

    def test_post_com_cooldown_bloqueia_429(
        self, client, school_year, variantes_ativas, settings
    ) -> None:
        settings.GRADE_CERTA_COOLDOWN_DISABLED = False
        school_year.last_solver_run_at = timezone.now() - timedelta(minutes=10)
        school_year.save()
        url = reverse("scheduling:run-timetable", args=[school_year.id])
        response = client.post(url)
        assert response.status_code == 429  # Too Many Requests

    def test_post_sem_variantes_ativas_retorna_erro(
        self, client, school_year
    ) -> None:
        url = reverse("scheduling:run-timetable", args=[school_year.id])
        response = client.post(url)
        # Erro (não redirect)
        assert response.status_code != 302

    def test_get_nao_suportado(self, client, school_year) -> None:
        url = reverse("scheduling:run-timetable", args=[school_year.id])
        response = client.get(url)
        # View é POST-only, GET deve dar 405
        assert response.status_code == 405


class TestRunProgressView:
    @pytest.fixture
    def client(self, user):
        c = Client()
        c.force_login(user)
        return c

    def test_renderiza_com_runs(
        self, client, school_year, variantes_ativas
    ) -> None:
        # Dispara primeiro
        client.post(reverse("scheduling:run-timetable", args=[school_year.id]))
        # Acessa progresso
        url = reverse("scheduling:run-progress", args=[school_year.id])
        response = client.get(url)
        assert response.status_code == 200
        assert b"Rodando solver" in response.content


class TestRunResultView:
    @pytest.fixture
    def client(self, user):
        c = Client()
        c.force_login(user)
        return c

    def test_renderiza_sem_runs(self, client, school_year) -> None:
        url = reverse("scheduling:run-result", args=[school_year.id])
        response = client.get(url)
        assert response.status_code == 200
        assert b"Nenhuma execu" in response.content  # nenhuma execução ainda

    def test_marca_vencedor_menor_buracos(
        self, client, school_year, variantes_ativas, tenant
    ) -> None:
        # 3 runs: 5, 3, 10 buracos — vencedor é o de 3
        for variante, buracos in zip(
            variantes_ativas, [5, 3, 10], strict=True
        ):
            SolverRun.objects.create(
                tenant=tenant,
                variant=variante,
                school_year=school_year,
                status=SolverRun.StatusChoices.SUCCESS,
                buracos=buracos,
                completude=0.9,
                tempo_total=timedelta(seconds=10),
            )
        url = reverse("scheduling:run-result", args=[school_year.id])
        response = client.get(url)
        assert response.status_code == 200
        assert b"winner" in response.content
        # O vencedor é a variante B (3 buracos)
        assert b"B - Hill Climbing" in response.content
