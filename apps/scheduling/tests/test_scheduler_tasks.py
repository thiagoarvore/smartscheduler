"""Testes das tasks assíncronas (Sprint 08 item 3.9).

Como o projeto não tem Celery configurado, as tasks são funções
puras — testamos elas chamando diretamente, sem `apply_async`.
"""
from __future__ import annotations

import pytest

from apps.scheduling.models import SolverRun, SolverVariant
from apps.scheduling.tasks import run_3_variants, run_variant


@pytest.fixture
def tenant(db):
    from apps.tenants.models import Tenant

    return Tenant.objects.create(schema_name="t1", name="Tenant 1")


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
def variantes_ativas(tenant, db) -> tuple[SolverVariant, SolverVariant, SolverVariant]:
    return (
        SolverVariant.objects.create(
            tenant=tenant,
            nome=SolverVariant.NomeChoices.A_RESTART,
            is_active=True,
            parametros={"max_restarts": 5},
        ),
        SolverVariant.objects.create(
            tenant=tenant,
            nome=SolverVariant.NomeChoices.B_HILL_CLIMBING,
            is_active=True,
            parametros={},
        ),
        SolverVariant.objects.create(
            tenant=tenant,
            nome=SolverVariant.NomeChoices.C_HYBRID,
            is_active=True,
            parametros={"max_construcoes": 2},
        ),
    )


# run_variant -------------------------------------------------------------


class TestRunVariant:
    def test_roda_com_sucesso(
        self, tenant, school_year, variantes_ativas, db
    ) -> None:
        variant = variantes_ativas[0]
        run = SolverRun.objects.create(
            tenant=tenant,
            variant=variant,
            school_year=school_year,
        )
        result = run_variant(str(run.id))
        assert result["status"] == "success"
        run.refresh_from_db()
        assert run.status == SolverRun.StatusChoices.SUCCESS
        assert run.buracos == 0  # Timetable vazio = 0 buracos
        assert run.completude == 1.0
        assert run.finished_at is not None
        assert run.tempo_total is not None

    def test_falha_quando_variante_desconhecida(
        self, tenant, school_year, db
    ) -> None:
        # Cria variante com nome que não está no registry
        bad = SolverVariant.objects.create(
            tenant=tenant,
            nome="Z-NOPE",  # não está em VARIANT_REGISTRY
            is_active=True,
        )
        run = SolverRun.objects.create(
            tenant=tenant,
            variant=bad,
            school_year=school_year,
        )
        result = run_variant(str(run.id))
        assert result["status"] == "failed"
        run.refresh_from_db()
        assert run.status == SolverRun.StatusChoices.FAILED
        assert "Variante desconhecida" in run.error_message

    def test_metricas_persistidas(
        self, tenant, school_year, variantes_ativas, db
    ) -> None:
        run = SolverRun.objects.create(
            tenant=tenant,
            variant=variantes_ativas[0],
            school_year=school_year,
        )
        run_variant(str(run.id))
        run.refresh_from_db()
        assert run.tempo_total is not None
        assert run.criterio_parada in [
            SolverRun.CriterioParadaChoices.ZERO_BURACOS,
            SolverRun.CriterioParadaChoices.TIMEOUT,
        ]
        assert run.solution_json is not None
        assert "assignments" in run.solution_json


# run_3_variants ----------------------------------------------------------


class TestRun3Variants:
    def test_encadeia_3_variantes(
        self, tenant, school_year, variantes_ativas, db
    ) -> None:
        run_ids = run_3_variants(str(school_year.id), disparado_por="user")
        assert len(run_ids) == 3
        runs = SolverRun.objects.filter(id__in=run_ids)
        assert runs.count() == 3
        nomes = sorted(runs.values_list("variant__nome", flat=True))
        assert nomes == ["A-Restart", "B-HillClimbing", "C-Hybrid"]
        # Todos devem ter terminado com sucesso
        for run in runs:
            assert run.status == SolverRun.StatusChoices.SUCCESS

    def test_atualiza_cooldown_da_school_year(
        self, tenant, school_year, variantes_ativas, db
    ) -> None:
        antes = school_year.last_solver_run_at
        run_3_variants(str(school_year.id))
        school_year.refresh_from_db()
        assert school_year.last_solver_run_at is not None
        if antes is not None:
            assert school_year.last_solver_run_at >= antes

    def test_erro_se_sem_variantes_ativas(
        self, tenant, school_year, db
    ) -> None:
        with pytest.raises(ValueError, match="Nenhuma variante ativa"):
            run_3_variants(str(school_year.id))

    def test_salva_user_id_no_run(
        self, tenant, school_year, variantes_ativas, db
    ) -> None:
        from django.contrib.auth import get_user_model

        user_model = get_user_model()
        user = user_model.objects.create_user(
            username="alice",
            email="[email protected]",
            password="x",
        )
        run_ids = run_3_variants(
            str(school_year.id),
            disparado_por="user",
            user_id=str(user.id),
        )
        for run_id in run_ids:
            run = SolverRun.objects.get(id=run_id)
            assert run.disparado_por_user_id == user.id
