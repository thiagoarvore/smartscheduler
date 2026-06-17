"""Testes do model Suggestion (Sprint 09 — SDD §22.4).

Como o settings_test.py usa SQLite sem django-tenants, montamos
um schema isolado com `Tenant`/`Domain` via `tenant_context_manager`
quando necessário. Quando não precisamos de tenant, usamos `Tenant.objects.create`
diretamente (o test runner aceita isso com SQLite).
"""
from __future__ import annotations

import pytest
from django.core.exceptions import ValidationError
from django.utils import timezone

from apps.scheduling.models import SolverRun, SolverVariant, Suggestion
from apps.schools.models import SchoolYear
from apps.tenants.models import Tenant


@pytest.fixture
def tenant(db):
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


@pytest.fixture
def variant(tenant, school_year, db):
    return SolverVariant.objects.create(
        tenant=tenant,
        school_year=school_year,
        nome=SolverVariant.NomeChoices.A_RESTART,
    )


@pytest.fixture
def solver_run(tenant, school_year, variant, db):
    return SolverRun.objects.create(
        tenant=tenant,
        variant=variant,
        school_year=school_year,
    )


# Suggestion --------------------------------------------------------------


class TestSuggestion:
    def test_cria_suggestion_com_defaults(self, tenant, school_year, solver_run, db) -> None:
        s = Suggestion.objects.create(
            tenant=tenant,
            school_year=school_year,
            solver_run=solver_run,
            categoria=Suggestion.CategoriaChoices.WORKLOAD_INCREASE,
            titulo="Aumentar carga de Matemática",
        )
        assert s.status == Suggestion.StatusChoices.PENDING
        assert s.buracos_antes == 0
        assert s.buracos_depois == 0
        assert s.delta == 0
        assert s.param_diff == {}
        assert s.descricao == ""
        assert s.aplicado_em is None

    def test_str(self, tenant, school_year, solver_run, db) -> None:
        s = Suggestion.objects.create(
            tenant=tenant,
            school_year=school_year,
            solver_run=solver_run,
            categoria=Suggestion.CategoriaChoices.TEACHER_ADD,
            titulo="Adicionar professor de Física",
        )
        assert "Adicionar professor" in str(s)
        assert "Adicionar professor de Física" in str(s)

    def test_categoria_choices(self, tenant, school_year, solver_run, db) -> None:
        categorias = [
            Suggestion.CategoriaChoices.WORKLOAD_INCREASE,
            Suggestion.CategoriaChoices.TEACHER_ADD,
            Suggestion.CategoriaChoices.TEACHER_AVAILABILITY,
            Suggestion.CategoriaChoices.SUBJECT_RULE_RELAX,
        ]
        for cat in categorias:
            s = Suggestion.objects.create(
                tenant=tenant,
                school_year=school_year,
                solver_run=solver_run,
                categoria=cat,
                titulo=f"Sugestão {cat}",
            )
            assert s.categoria == cat

    def test_status_choices(self, tenant, school_year, solver_run, db) -> None:
        s = Suggestion.objects.create(
            tenant=tenant,
            school_year=school_year,
            solver_run=solver_run,
            categoria=Suggestion.CategoriaChoices.WORKLOAD_INCREASE,
            titulo="Teste",
            status=Suggestion.StatusChoices.APPLIED,
        )
        assert s.status == Suggestion.StatusChoices.APPLIED

        s2 = Suggestion.objects.create(
            tenant=tenant,
            school_year=school_year,
            solver_run=solver_run,
            categoria=Suggestion.CategoriaChoices.TEACHER_AVAILABILITY,
            titulo="Teste 2",
            status=Suggestion.StatusChoices.IGNORED,
        )
        assert s2.status == Suggestion.StatusChoices.IGNORED

    def test_delta_e_buracos(self, tenant, school_year, solver_run, db) -> None:
        s = Suggestion.objects.create(
            tenant=tenant,
            school_year=school_year,
            solver_run=solver_run,
            categoria=Suggestion.CategoriaChoices.SUBJECT_RULE_RELAX,
            titulo="Relaxar regra de Geografia",
            buracos_antes=10,
            buracos_depois=3,
            delta=7,
        )
        assert s.buracos_antes == 10
        assert s.buracos_depois == 3
        assert s.delta == 7

    def test_param_diff_json_round_trip(self, tenant, school_year, solver_run, db) -> None:
        params = {
            "workload_increase": True,
            "subject": "Matemática",
            "hours": 4,
        }
        s = Suggestion.objects.create(
            tenant=tenant,
            school_year=school_year,
            solver_run=solver_run,
            categoria=Suggestion.CategoriaChoices.WORKLOAD_INCREASE,
            titulo="Teste JSON",
            param_diff=params,
        )
        s.refresh_from_db()
        assert s.param_diff == params
        assert s.param_diff["subject"] == "Matemática"

    def test_aplicado_em_set(self, tenant, school_year, solver_run, db) -> None:
        now = timezone.now()
        s = Suggestion.objects.create(
            tenant=tenant,
            school_year=school_year,
            solver_run=solver_run,
            categoria=Suggestion.CategoriaChoices.WORKLOAD_INCREASE,
            titulo="Teste aplicado_em",
            status=Suggestion.StatusChoices.APPLIED,
            aplicado_em=now,
        )
        s.refresh_from_db()
        assert s.aplicado_em is not None
        delta = abs((s.aplicado_em - now).total_seconds())
        assert delta < 1.0

    def test_ordering_por_delta(self, tenant, school_year, solver_run, db) -> None:
        Suggestion.objects.create(
            tenant=tenant,
            school_year=school_year,
            solver_run=solver_run,
            categoria=Suggestion.CategoriaChoices.WORKLOAD_INCREASE,
            titulo="Sugestão delta=2",
            delta=2,
        )
        Suggestion.objects.create(
            tenant=tenant,
            school_year=school_year,
            solver_run=solver_run,
            categoria=Suggestion.CategoriaChoices.WORKLOAD_INCREASE,
            titulo="Sugestão delta=5",
            delta=5,
        )
        Suggestion.objects.create(
            tenant=tenant,
            school_year=school_year,
            solver_run=solver_run,
            categoria=Suggestion.CategoriaChoices.WORKLOAD_INCREASE,
            titulo="Sugestão delta=1",
            delta=1,
        )
        sugestoes = list(Suggestion.objects.all())
        assert sugestoes[0].delta == 5
        assert sugestoes[1].delta == 2
        assert sugestoes[2].delta == 1

    def test_related_name_sugestoes_do_solver_run(
        self, tenant, school_year, solver_run, db
    ) -> None:
        s = Suggestion.objects.create(
            tenant=tenant,
            school_year=school_year,
            solver_run=solver_run,
            categoria=Suggestion.CategoriaChoices.TEACHER_ADD,
            titulo="Teste related_name",
        )
        assert s in solver_run.suggestions.all()

    def test_related_name_sugestoes_do_school_year(
        self, tenant, school_year, solver_run, db
    ) -> None:
        s = Suggestion.objects.create(
            tenant=tenant,
            school_year=school_year,
            solver_run=solver_run,
            categoria=Suggestion.CategoriaChoices.TEACHER_ADD,
            titulo="Teste related_name sy",
        )
        assert s in school_year.suggestions.all()

    def test_descricao_longa(self, tenant, school_year, solver_run, db) -> None:
        texto = "Uma descrição detalhada da sugestão. " * 20
        s = Suggestion.objects.create(
            tenant=tenant,
            school_year=school_year,
            solver_run=solver_run,
            categoria=Suggestion.CategoriaChoices.TEACHER_AVAILABILITY,
            titulo="Teste descrição",
            descricao=texto,
        )
        s.refresh_from_db()
        assert s.descricao == texto