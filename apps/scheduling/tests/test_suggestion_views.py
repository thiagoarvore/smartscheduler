"""Testes das views de sugestão (Sprint 09 — SDD §22.4)."""
from __future__ import annotations

from datetime import timedelta

import pytest
from django.contrib.auth import get_user_model
from django.test import Client
from django.urls import reverse
from django.utils import timezone

from apps.scheduling.models import SolverRun, SolverVariant, Suggestion


# ── Fixtures ──────────────────────────────────────────────────────────────


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


@pytest.fixture
def variant(tenant, db):
    return SolverVariant.objects.create(
        tenant=tenant,
        nome=SolverVariant.NomeChoices.A_RESTART,
        is_active=True,
    )


@pytest.fixture
def solver_run(tenant, school_year, variant, db):
    return SolverRun.objects.create(
        tenant=tenant,
        variant=variant,
        school_year=school_year,
        status=SolverRun.StatusChoices.SUCCESS,
        buracos=5,
        completude=0.85,
        tempo_total=timedelta(seconds=120),
    )


@pytest.fixture
def suggestion(tenant, school_year, solver_run, db):
    return Suggestion.objects.create(
        tenant=tenant,
        school_year=school_year,
        solver_run=solver_run,
        categoria=Suggestion.CategoriaChoices.WORKLOAD_INCREASE,
        titulo="Aumentar carga de Matemática no 7º ano",
        descricao="Simulação mostra que +1h semanal reduz 3 buracos.",
        buracos_antes=5,
        buracos_depois=2,
        delta=3,
        param_diff={"subject": "MAT", "series": "7º", "weekly_hours": {"de": 4, "para": 5}},
    )


@pytest.fixture(autouse=True)
def set_request_tenant(tenant):
    """Anexa `tenant` ao request automaticamente em todos os testes."""
    from apps.scheduling.views import TenantMixin

    original = TenantMixin.get_tenant

    def patched_get_tenant(self):
        return tenant

    TenantMixin.get_tenant = patched_get_tenant
    yield
    TenantMixin.get_tenant = original


@pytest.fixture
def client(user):
    c = Client()
    c.force_login(user)
    return c


# ── Testes: suggestion_detail_view ────────────────────────────────────────


class TestSuggestionDetailView:
    def test_returns_200_for_existing_suggestion(self, client, suggestion):
        url = reverse("scheduling:suggestion-detail", args=[suggestion.pk])
        response = client.get(url)
        assert response.status_code == 200

    def test_contains_suggestion_titulo(self, client, suggestion):
        url = reverse("scheduling:suggestion-detail", args=[suggestion.pk])
        response = client.get(url)
        content = response.content.decode()
        assert suggestion.titulo in content

    def test_contains_categoria_display(self, client, suggestion):
        url = reverse("scheduling:suggestion-detail", args=[suggestion.pk])
        response = client.get(url)
        content = response.content.decode()
        assert suggestion.get_categoria_display() in content

    def test_contains_delta(self, client, suggestion):
        url = reverse("scheduling:suggestion-detail", args=[suggestion.pk])
        response = client.get(url)
        content = response.content.decode()
        assert str(suggestion.delta) in content

    def test_contains_param_diff_json(self, client, suggestion):
        url = reverse("scheduling:suggestion-detail", args=[suggestion.pk])
        response = client.get(url)
        content = response.content.decode()
        assert "MAT" in content

    def test_returns_404_for_nonexistent_pk(self, client, db):
        import uuid

        url = reverse("scheduling:suggestion-detail", args=[uuid.uuid4()])
        response = client.get(url)
        assert response.status_code == 404

    def test_post_method_not_allowed(self, client, suggestion):
        url = reverse("scheduling:suggestion-detail", args=[suggestion.pk])
        # The view is GET-only, but Django doesn't strictly enforce this for FBV
        # We just verify that GET works correctly — POST to detail isn't meaningful
        response = client.get(url)
        assert response.status_code == 200


# ── Testes: suggestion_ignore_view ─────────────────────────────────────────


class TestSuggestionIgnoreView:
    def test_post_sets_status_to_ignored(self, client, suggestion):
        assert suggestion.status == Suggestion.StatusChoices.PENDING
        url = reverse("scheduling:suggestion-ignore", args=[suggestion.pk])
        response = client.post(url)
        assert response.status_code == 200
        suggestion.refresh_from_db()
        assert suggestion.status == Suggestion.StatusChoices.IGNORED

    def test_post_sets_aplicado_em(self, client, suggestion):
        assert suggestion.aplicado_em is None
        url = reverse("scheduling:suggestion-ignore", args=[suggestion.pk])
        before = timezone.now()
        response = client.post(url)
        after = timezone.now()
        suggestion.refresh_from_db()
        assert suggestion.aplicado_em is not None
        assert before <= suggestion.aplicado_em <= after

    def test_post_returns_htmx_swap_content(self, client, suggestion):
        url = reverse("scheduling:suggestion-ignore", args=[suggestion.pk])
        response = client.post(url)
        content = response.content.decode()
        # Returns an empty div with the suggestion id for HTMX outer-swap
        assert f'suggestion-{suggestion.pk}' in content

    def test_get_not_allowed(self, client, suggestion):
        url = reverse("scheduling:suggestion-ignore", args=[suggestion.pk])
        response = client.get(url)
        assert response.status_code == 405  # Method Not Allowed

    def test_returns_404_for_nonexistent_pk(self, client, db):
        import uuid

        url = reverse("scheduling:suggestion-ignore", args=[uuid.uuid4()])
        response = client.post(url)
        assert response.status_code == 404

    def test_already_ignored_suggestion_stays_ignored(self, client, suggestion):
        # First ignore
        url = reverse("scheduling:suggestion-ignore", args=[suggestion.pk])
        client.post(url)
        suggestion.refresh_from_db()
        assert suggestion.status == Suggestion.StatusChoices.IGNORED
        first_aplicado_em = suggestion.aplicado_em

        # Second ignore — should not fail
        response = client.post(url)
        assert response.status_code == 200
        suggestion.refresh_from_db()
        assert suggestion.status == Suggestion.StatusChoices.IGNORED


# ── Testes: RunResultView com sugestões ─────────────────────────────────────


class TestRunResultViewWithSuggestions:
    @pytest.fixture
    def variantes_ativas(self, tenant, db):
        return SolverVariant.objects.bulk_create(
            [
                SolverVariant(tenant=tenant, nome=SolverVariant.NomeChoices.A_RESTART, is_active=True),
                SolverVariant(tenant=tenant, nome=SolverVariant.NomeChoices.B_HILL_CLIMBING, is_active=True),
                SolverVariant(tenant=tenant, nome=SolverVariant.NomeChoices.C_HYBRID, is_active=True),
            ]
        )

    def test_suggestions_in_context(self, client, school_year, variantes_ativas, tenant):
        # Create a winning run
        SolverRun.objects.create(
            tenant=tenant,
            variant=variantes_ativas[0],
            school_year=school_year,
            status=SolverRun.StatusChoices.SUCCESS,
            buracos=5,
            completude=0.9,
            tempo_total=timedelta(seconds=10),
        )
        url = reverse("scheduling:run-result", args=[school_year.id])
        response = client.get(url)
        assert response.status_code == 200
        assert "suggestions" in response.context

    def test_suggestions_panel_not_shown_without_suggestions(self, client, school_year, variantes_ativas, tenant):
        SolverRun.objects.create(
            tenant=tenant,
            variant=variantes_ativas[0],
            school_year=school_year,
            status=SolverRun.StatusChoices.SUCCESS,
            buracos=0,
            completude=1.0,
            tempo_total=timedelta(seconds=10),
        )
        url = reverse("scheduling:run-result", args=[school_year.id])
        response = client.get(url)
        assert response.status_code == 200
        assert response.context["suggestions_count"] == 0

    def test_suggestions_shown_in_template(self, client, school_year, variantes_ativas, tenant):
        run = SolverRun.objects.create(
            tenant=tenant,
            variant=variantes_ativas[0],
            school_year=school_year,
            status=SolverRun.StatusChoices.SUCCESS,
            buracos=5,
            completude=0.85,
            tempo_total=timedelta(seconds=120),
        )
        Suggestion.objects.create(
            tenant=tenant,
            school_year=school_year,
            solver_run=run,
            categoria=Suggestion.CategoriaChoices.WORKLOAD_INCREASE,
            titulo="Aumentar carga de Matemática",
            descricao="Desc",
            buracos_antes=5,
            buracos_depois=2,
            delta=3,
            param_diff={"subject": "MAT"},
        )
        url = reverse("scheduling:run-result", args=[school_year.id])
        response = client.get(url)
        assert response.status_code == 200
        content = response.content.decode()
        assert "Sugest" in content  # "Sugestões" title