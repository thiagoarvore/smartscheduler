"""Testes dos novos models Sprint 08: SolverVariant, SolverRun, SchoolYear.last_solver_run_at.

Como o settings_test.py usa SQLite sem django-tenants, montamos
um schema isolado com `Tenant`/`Domain` via `tenant_context_manager`
quando necessário. Quando não precisamos de tenant, usamos `Tenant.objects.create`
diretamente (o test runner aceita isso com SQLite).
"""
from __future__ import annotations

from datetime import timedelta

import pytest
from django.core.exceptions import ValidationError
from django.db import IntegrityError
from django.utils import timezone

from apps.scheduling.models import SolverRun, SolverVariant
from apps.schools.models import SchoolYear

# Multi-tenant: settings_test.py desabilita django-tenants, então
# os models multi-tenant funcionam como models normais. Tenant
# precisa ser criado para satisfazer FKs.


@pytest.fixture
def tenant(db):
    from apps.tenants.models import Tenant

    return Tenant.objects.create(
        schema_name="test_schema",
        name="Test Tenant",
    )


@pytest.fixture
def school_year(tenant, db):
    return SchoolYear.objects.create(
        tenant=tenant,
        name="2026",
        year=2026,
        start_date="2026-02-01",
        end_date="2026-12-15",
    )


# SolverVariant ----------------------------------------------------------


class TestSolverVariant:
    def test_cria_variante_global(self, tenant, db) -> None:
        v = SolverVariant.objects.create(
            tenant=tenant,
            nome=SolverVariant.NomeChoices.A_RESTART,
            descricao="N tentativas",
            parametros={"max_restarts": 100},
        )
        assert v.is_active is True
        assert v.school_year_id is None
        assert "global" in str(v)

    def test_cria_variante_de_school_year(self, tenant, school_year, db) -> None:
        v = SolverVariant.objects.create(
            tenant=tenant,
            school_year=school_year,
            nome=SolverVariant.NomeChoices.B_HILL_CLIMBING,
        )
        assert v.school_year_id == school_year.id
        assert school_year.name in str(v)

    def test_unica_por_escopo(self, tenant, school_year, db) -> None:
        SolverVariant.objects.create(
            tenant=tenant,
            school_year=school_year,
            nome=SolverVariant.NomeChoices.A_RESTART,
        )
        with pytest.raises(IntegrityError):
            SolverVariant.objects.create(
                tenant=tenant,
                school_year=school_year,
                nome=SolverVariant.NomeChoices.A_RESTART,
            )

    def test_permite_mesmo_nome_em_escopos_diferentes(
        self, tenant, school_year, db
    ) -> None:
        # A-Restart em global E em school_year deve coexistir
        v_global = SolverVariant.objects.create(
            tenant=tenant,
            school_year=None,
            nome=SolverVariant.NomeChoices.A_RESTART,
        )
        v_sy = SolverVariant.objects.create(
            tenant=tenant,
            school_year=school_year,
            nome=SolverVariant.NomeChoices.A_RESTART,
        )
        assert v_global.id != v_sy.id
        assert SolverVariant.objects.count() == 2

    def test_parametros_como_json(self, tenant, db) -> None:
        v = SolverVariant.objects.create(
            tenant=tenant,
            nome=SolverVariant.NomeChoices.C_HYBRID,
            parametros={"max_construcoes": 5, "tempo_por_construcao_seg": 120},
        )
        v.refresh_from_db()
        assert v.parametros == {"max_construcoes": 5, "tempo_por_construcao_seg": 120}

    def test_clean_rejeita_school_year_de_outro_tenant(self, tenant, db) -> None:
        from apps.tenants.models import Tenant

        other = Tenant.objects.create(schema_name="other", name="Other")
        other_sy = SchoolYear.objects.create(
            tenant=other,
            name="2026",
            year=2026,
            start_date="2026-02-01",
            end_date="2026-12-15",
        )
        v = SolverVariant(
            tenant=tenant,
            school_year=other_sy,
            nome=SolverVariant.NomeChoices.A_RESTART,
        )
        with pytest.raises(ValidationError, match="school_year"):
            v.clean()


# SolverRun --------------------------------------------------------------


class TestSolverRun:
    @pytest.fixture
    def variant(self, tenant, school_year, db) -> SolverVariant:
        return SolverVariant.objects.create(
            tenant=tenant,
            school_year=school_year,
            nome=SolverVariant.NomeChoices.A_RESTART,
        )

    def test_cria_run_em_estado_running(
        self, tenant, school_year, variant, db
    ) -> None:
        run = SolverRun.objects.create(
            tenant=tenant,
            variant=variant,
            school_year=school_year,
        )
        assert run.status == SolverRun.StatusChoices.RUNNING
        assert run.is_running is True
        assert run.is_terminal is False
        assert run.suggestions_status == SolverRun.SuggestionsStatusChoices.NOT_RUN
        assert run.report_upload_status == SolverRun.ReportUploadStatusChoices.PENDING
        assert run.buracos is None
        assert run.completude is None

    def test_run_termina_com_sucesso(
        self, tenant, school_year, variant, db
    ) -> None:
        run = SolverRun.objects.create(
            tenant=tenant,
            variant=variant,
            school_year=school_year,
        )
        run.status = SolverRun.StatusChoices.SUCCESS
        run.buracos = 5
        run.completude = 0.95
        run.tempo_total = timedelta(minutes=14, seconds=22)
        run.criterio_parada = SolverRun.CriterioParadaChoices.TIMEOUT
        run.finished_at = timezone.now()
        run.save()
        run.refresh_from_db()
        assert run.is_terminal is True
        assert run.buracos == 5
        assert run.completude == 0.95

    def test_completude_validada_no_clean(
        self, tenant, school_year, variant, db
    ) -> None:
        run = SolverRun(
            tenant=tenant,
            variant=variant,
            school_year=school_year,
            completude=1.5,  # inválido
        )
        with pytest.raises(ValidationError, match="completude"):
            run.clean()

    def test_completude_negativa_rejeitada(
        self, tenant, school_year, variant, db
    ) -> None:
        run = SolverRun(
            tenant=tenant,
            variant=variant,
            school_year=school_year,
            completude=-0.1,
        )
        with pytest.raises(ValidationError, match="completude"):
            run.clean()

    def test_solution_json_round_trip(
        self, tenant, school_year, variant, db
    ) -> None:
        payload = {
            "assignments": [],
            "buracos": [],
            "completude": 1.0,
            "criterio_parada": "zero_buracos",
            "iteracoes": 0,
            "restarts": 0,
        }
        run = SolverRun.objects.create(
            tenant=tenant,
            variant=variant,
            school_year=school_year,
            status=SolverRun.StatusChoices.SUCCESS,
            solution_json=payload,
        )
        run.refresh_from_db()
        assert run.solution_json == payload
        assert run.solution_json["criterio_parada"] == "zero_buracos"

    def test_run_de_outro_tenant_rejeitado_no_clean(
        self, tenant, school_year, variant, db
    ) -> None:
        from apps.tenants.models import Tenant

        other = Tenant.objects.create(schema_name="other", name="Other")
        run = SolverRun(
            tenant=other,
            variant=variant,  # pertence a `tenant`, não `other`
            school_year=school_year,
        )
        with pytest.raises(ValidationError, match="variant"):
            run.clean()

    def test_suggestions_e_report_defaults(
        self, tenant, school_year, variant, db
    ) -> None:
        run = SolverRun.objects.create(
            tenant=tenant,
            variant=variant,
            school_year=school_year,
        )
        assert run.suggestions_count == 0
        assert run.suggestions_status == "not_run"
        assert run.report_upload_status == "pending"


# SchoolYear.last_solver_run_at -----------------------------------------


class TestSchoolYearCooldown:
    def test_campo_existe_e_nullable(self, school_year) -> None:
        assert hasattr(school_year, "last_solver_run_at")
        assert school_year.last_solver_run_at is None

    def test_setar_last_solver_run_at(self, school_year, db) -> None:
        now = timezone.now()
        school_year.last_solver_run_at = now
        school_year.save()
        school_year.refresh_from_db()
        assert school_year.last_solver_run_at is not None
        # comparar com tolerância de 1s por causa de truncamento do SQLite
        delta = abs((school_year.last_solver_run_at - now).total_seconds())
        assert delta < 1.0
