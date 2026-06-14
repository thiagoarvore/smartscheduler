"""Testes da geração de relatórios .md (Sprint 08 item 3.14)."""
from __future__ import annotations

import uuid
from datetime import timedelta

import pytest

from apps.scheduling.models import SolverRun, SolverVariant
from apps.scheduling.services.report import (
    LocalUploader,
    filenames_for,
    generate_grade_md,
    generate_solver_report_md,
    upload_reports,
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
        assert "-03" in content or "-02" in content  # offset numérico do America/Sao_Paulo (BRT/AMT)

    def test_marca_vencedor_menor_buracos(self, school_year, runs) -> None:
        content = generate_solver_report_md(school_year, runs)
        # Vencedor é B (3 buracos)
        assert "B - Hill Climbing" in content
        assert "## 🏆 Variante Vencedora" in content
        # Tem a tabela comparativa
        assert "| Variante | Buracos | Completude |" in content
        assert all(
            f"| {n} " in content
            for n in ("A - Restart", "B - Hill Climbing", "C - Híbrido")
        )

    def test_ordenado_por_buracos(self, school_year, runs) -> None:
        content = generate_solver_report_md(school_year, runs)
        # Verifica que a tabela está ordenada: B (3) antes de C (4) antes de A (5).
        # Pegamos só a parte da tabela (depois de "Comparativo").
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


class TestFilenames:
    def test_formato_correto(self, school_year) -> None:
        f = filenames_for(school_year)
        assert f.relatorio.startswith("relatorio-solver-")
        assert f.relatorio.endswith(".md")
        assert f.grade.startswith("grade-")
        assert f.grade.endswith(".md")


class TestLocalUploader:
    def test_upload_cria_arquivo(self, tmp_path) -> None:
        uploader = LocalUploader(base_dir=str(tmp_path))
        url = uploader.upload("foo/bar.md", "# Hello")
        assert "file://" in url
        assert (tmp_path / "foo" / "bar.md").exists()
        assert (tmp_path / "foo" / "bar.md").read_text() == "# Hello"


class TestUploadReports:
    def test_gera_e_faz_upload(self, school_year, runs, tmp_path) -> None:
        uploader = LocalUploader(base_dir=str(tmp_path))
        filenames = upload_reports(
            school_year, runs, winning_run=runs[1], uploader=uploader
        )
        assert (tmp_path / filenames.relatorio).exists() or any(
            (tmp_path).rglob(filenames.relatorio)
        )
        # Pelo menos 1 arquivo com nome similar existe
        found = list(tmp_path.rglob(filenames.relatorio))
        assert len(found) == 1

    def test_falha_upload_nao_propaga(self, school_year, runs) -> None:
        class BrokenUploader:
            def upload(self, path, content) -> str:
                raise RuntimeError("Drive offline")

        # Não deve levantar
        filenames = upload_reports(
            school_year, runs, winning_run=runs[1], uploader=BrokenUploader()
        )
        assert filenames.relatorio.endswith(".md")
