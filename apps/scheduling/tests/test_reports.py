"""Testes da geração de relatórios .md (Sprint 08 item 3.14)."""
from __future__ import annotations

import uuid
from datetime import timedelta
from pathlib import Path

import pytest

from apps.scheduling.models import SolverRun, SolverVariant
from apps.scheduling.services.report import (
    generate_grade_md,
    generate_solver_report_md,
    save_reports,
)


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
def runs(tenant, school_year, db) -> list[SolverRun]:
    variantes = [
        SolverVariant.objects.create(
            tenant=tenant, nome=SolverVariant.NomeChoices.A_RESTART
        ),
        SolverVariant.objects.create(
            tenant=tenant, nome=SolverVariant.NomeChoices.B_HILL_CLIMBING
        ),
        SolverVariant.objects.create(
            tenant=tenant, nome=SolverVariant.NomeChoices.C_HYBRID
        ),
    ]
    return [
        SolverRun.objects.create(
            tenant=tenant,
            variant=variantes[0],
            school_year=school_year,
            status=SolverRun.StatusChoices.SUCCESS,
            buracos=5,
            completude=0.95,
            tempo_total=timedelta(minutes=14, seconds=22),
            iteracoes=100,
            restarts=47,
            criterio_parada=SolverRun.CriterioParadaChoices.TIMEOUT,
            seed=42,
        ),
        SolverRun.objects.create(
            tenant=tenant,
            variant=variantes[1],
            school_year=school_year,
            status=SolverRun.StatusChoices.SUCCESS,
            buracos=3,  # vencedor
            completude=0.98,
            tempo_total=timedelta(minutes=10),
            iteracoes=200,
            restarts=0,
            criterio_parada=SolverRun.CriterioParadaChoices.TIMEOUT,
            seed=42,
        ),
        SolverRun.objects.create(
            tenant=tenant,
            variant=variantes[2],
            school_year=school_year,
            status=SolverRun.StatusChoices.SUCCESS,
            buracos=4,
            completude=0.96,
            tempo_total=timedelta(minutes=20),
            iteracoes=300,
            restarts=12,
            criterio_parada=SolverRun.CriterioParadaChoices.TIMEOUT,
            seed=42,
        ),
    ]


class TestGenerateSolverReportMd:
    def test_contem_cabecalho(self, school_year, runs) -> None:
        content = generate_solver_report_md(school_year, runs)
        assert "# Relatório de Execução do Solver" in content
        assert school_year.name in content
        assert "-03" in content or "-02" in content  # offset numérico do America/Sao_Paulo

    def test_marca_vencedor_menor_buracos(self, school_year, runs) -> None:
        content = generate_solver_report_md(school_year, runs)
        assert "B - Hill Climbing" in content
        assert "## 🏆 Variante Vencedora" in content
        assert "| Variante | Buracos | Completude |" in content

    def test_ordenado_por_buracos(self, school_year, runs) -> None:
        content = generate_solver_report_md(school_year, runs)
        tabela_start = content.index("Comparativo das 3 Variantes")
        tabela = content[tabela_start:]
        idx_b = tabela.index("B - Hill Climbing")
        idx_c = tabela.index("C - Híbrido")
        idx_a = tabela.index("A - Restart")
        assert idx_b < idx_c < idx_a


class TestGenerateGradeMd:
    def test_cabecalho_com_buracos(self, school_year, runs) -> None:
        winner = runs[1]
        winner.solution_json = {
            "assignments": [
                {
                    "aula_id": str(uuid.uuid4()),
                    "slot_id": str(uuid.uuid4()),
                    "class_group_id": str(uuid.uuid4()),
                    "subject_id": "MAT",
                    "teacher_id": None,
                    "weekday": "monday",
                    "order": 1,
                }
            ],
            "buracos": [],
            "completude": 1.0,
            "criterio_parada": "zero_buracos",
        }
        winner.save()
        content = generate_grade_md(school_year, winner)
        assert "# Grade" in content
        assert "**Total de buracos**: 3" in content

    def test_sem_solution_json(self, school_year, runs) -> None:
        winner = runs[1]
        winner.solution_json = None
        winner.save()
        content = generate_grade_md(school_year, winner)
        assert "Sem dados" in content

    def test_sem_assignments(self, school_year, runs) -> None:
        winner = runs[1]
        winner.solution_json = {
            "assignments": [],
            "buracos": [],
            "completude": 1.0,
            "criterio_parada": "zero_buracos",
        }
        winner.save()
        content = generate_grade_md(school_year, winner)
        assert "Nenhuma aula" in content


class TestSaveReports:
    def test_gera_e_salva(self, school_year, runs, tmp_path) -> None:
        """save_reports gera os 2 arquivos .md em disco."""
        from apps.scheduling.services import report as report_mod

        # Monkey-patch REPORTS_DIR pro tmp_path
        original_dir = report_mod.REPORTS_DIR
        report_mod.REPORTS_DIR = tmp_path
        try:
            relatorio_path, grade_path = save_reports(school_year, runs, winning_run=runs[1])
        finally:
            report_mod.REPORTS_DIR = original_dir

        assert Path(relatorio_path).exists()
        assert Path(grade_path).exists()
        assert "relatorio-solver" in relatorio_path
        assert "grade-" in grade_path

    def test_falha_nao_propaga(self, school_year, runs, tmp_path) -> None:
        """Se o disco estiver inacessível, save_reports não levanta."""
        from apps.scheduling.services import report as report_mod

        report_mod.REPORTS_DIR = Path("/nonexistent/path/that/cannot/be/created")
        try:
            # Não deve levantar exceção
            relatorio_path, grade_path = save_reports(school_year, runs, winning_run=runs[1])
        finally:
            report_mod.REPORTS_DIR = tmp_path

        # Retorna caminhos mesmo que não salvou
        assert "relatorio-solver" in relatorio_path
