"""Geração de relatórios .md das execuções do solver (Sprint 08 item 3.14, SDD §22.2.7).

Gera 2 artefatos por execução:
1. `relatorio-solver-{SchoolYear.slug}-{YYYYMMDD-HHMM}.md` — pro Thiago
2. `grade-{SchoolYear.slug}-{YYYYMMDD-HHMM}.md` — pro usuário final

A interface de upload pro Drive é plugável (ver `DriveUploader`).
A implementação default (`LocalUploader`) salva em
`./reports/{tenant_slug}/` — útil pra dev/CI. A implementação real
de Drive fica como stub documentado pra Sprint 09.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Protocol
from zoneinfo import ZoneInfo

from django.conf import settings
from django.utils import timezone

from apps.scheduling.models import SolverRun
from apps.schools.models import SchoolYear

logger = logging.getLogger(__name__)


# Uploaders --------------------------------------------------------------


class DriveUploader(Protocol):
    """Interface para upload de relatórios.

    Implementações:
    - `LocalUploader` (default, dev): salva em `./reports/{tenant_slug}/`
    - `GoogleDriveUploader` (Sprint 09): sobe pro Drive
    """

    def upload(self, path: str, content: str) -> str:
        """Faz upload de `content` e retorna uma URL/identificador."""
        ...


class LocalUploader:
    """Uploader que salva em disco. Útil pra dev/CI."""

    def __init__(self, base_dir: str = "./reports") -> None:
        self.base_dir = Path(base_dir)

    def upload(self, path: str, content: str) -> str:
        full = self.base_dir / path
        full.parent.mkdir(parents=True, exist_ok=True)
        full.write_text(content, encoding="utf-8")
        return f"file://{full.resolve()}"


# Helpers de formatação -------------------------------------------------


def _ts_jst() -> datetime:
    """Timestamp atual em JST (Asia/Tokyo)."""
    tz = ZoneInfo(settings.TIME_ZONE)
    return timezone.now().astimezone(tz)


def _ts_filename() -> str:
    """YYYYMMDD-HHMM formatado em JST."""
    return _ts_jst().strftime("%Y%m%d-%H%M")


def _format_duration(td) -> str:
    if td is None:
        return "—"
    total = int(td.total_seconds())
    m, s = divmod(total, 60)
    return f"{m}m {s:02d}s"


# Geração dos .md -------------------------------------------------------


def generate_solver_report_md(school_year: SchoolYear, runs: list[SolverRun]) -> str:
    """Gera o conteúdo do `relatorio-solver-...md`.

    Estrutura (SDD §22.2.7):
    1. Cabeçalho: escola, ano, timestamp, tenant, total de aulas
    2. Variante Vencedora (vencedor pelo critério §22.2.10)
    3. Tabela comparativa das 3 variantes
    """
    ts = _ts_jst().strftime("%Y-%m-%d %H:%M:%S %Z")
    runs_sorted = sorted(
        runs,
        key=lambda r: (
            r.buracos if r.buracos is not None else 999_999,
            r.tempo_total.total_seconds() if r.tempo_total else 999_999,
        ),
    )
    winner = runs_sorted[0] if runs_sorted else None

    lines: list[str] = [
        f"# Relatório de Execução do Solver — {school_year.name}",
        "",
        f"- **Escola/Ano letivo**: {school_year.name} ({school_year.year})",
        f"- **Data/Hora (JST)**: {ts}",
        f"- **Tenant ID**: {school_year.tenant_id}",
        f"- **Total de execuções**: {len(runs)}",
        "",
    ]

    if winner:
        lines.extend(
            [
                "## 🏆 Variante Vencedora",
                "",
                f"- **Nome**: {winner.variant.get_nome_display()}",
                f"- **Buracos**: {winner.buracos}",
                f"- **Completude**: {winner.completude:.2f}" if winner.completude is not None else "- **Completude**: —",
                f"- **Tempo total**: {_format_duration(winner.tempo_total)}",
                f"- **Iterações**: {winner.iteracoes}",
                f"- **Restarts**: {winner.restarts}",
                f"- **Critério de parada**: {winner.get_criterio_parada_display() or '—'}",
                f"- **Seed**: {winner.seed}",
                "",
            ]
        )

    lines.extend(
        [
            "## Comparativo das 3 Variantes",
            "",
            "| Variante | Buracos | Completude | Tempo | Iterações | Restarts | Critério de Parada |",
            "|----------|---------|------------|-------|-----------|----------|--------------------|",
        ]
    )
    for run in runs_sorted:
        completude = f"{run.completude:.2f}" if run.completude is not None else "—"
        lines.append(
            f"| {run.variant.get_nome_display()} "
            f"| {run.buracos if run.buracos is not None else '—'} "
            f"| {completude} "
            f"| {_format_duration(run.tempo_total)} "
            f"| {run.iteracoes} "
            f"| {run.restarts} "
            f"| {run.get_criterio_parada_display() or '—'} |"
        )

    return "\n".join(lines) + "\n"


def generate_grade_md(school_year: SchoolYear, winning_run: SolverRun) -> str:
    """Gera o conteúdo do `grade-...md` (visão do usuário final).

    Estrutura: cabeçalho + grade visual semanal por turma.
    No MVP, renderiza a grade do `solution_json` (assignments) agrupada
    por turma × dia × ordem.
    """
    ts = _ts_jst().strftime("%Y-%m-%d %H:%M:%S %Z")
    lines: list[str] = [
        f"# Grade — {school_year.name}",
        "",
        f"- **Data/Hora (JST)**: {ts}",
        f"- **Total de buracos**: {winning_run.buracos}",
        f"- **Completude**: {winning_run.completude:.2f}" if winning_run.completude is not None else "- **Completude**: —",
        "",
    ]

    if not winning_run.solution_json:
        lines.append("_Sem dados de solução._")
        return "\n".join(lines) + "\n"

    assignments = winning_run.solution_json.get("assignments", [])
    if not assignments:
        lines.append("_Nenhuma aula alocada._")
        return "\n".join(lines) + "\n"

    # Agrupa por (class_group_id, weekday, order)
    by_class: dict[str, dict[str, dict[int, str]]] = {}
    for a in assignments:
        cg = a["class_group_id"]
        wd = a.get("weekday", "?")
        order = a.get("order", 0)
        by_class.setdefault(cg, {}).setdefault(wd, {})[order] = a.get("subject_id", "?")

    for cg, weekdays in by_class.items():
        lines.append(f"## Turma `{cg[:8]}`")
        lines.append("")
        lines.append("| # | Seg | Ter | Qua | Qui | Sex |")
        lines.append("|---|-----|-----|-----|-----|-----|")
        max_order = max(
            (o for wd in weekdays.values() for o in wd),
            default=0,
        )
        for order in range(1, max_order + 1):
            cells = [
                weekdays.get(wd, {}).get(order, "—")[:8]
                for wd in ("monday", "tuesday", "wednesday", "thursday", "friday")
            ]
            lines.append(f"| {order} | " + " | ".join(cells) + " |")
        lines.append("")

    return "\n".join(lines) + "\n"


# Pipeline de upload ----------------------------------------------------


@dataclass(frozen=True)
class ReportFilenames:
    """Nomes dos arquivos gerados para uma execução."""

    relatorio: str
    grade: str


def filenames_for(school_year: SchoolYear) -> ReportFilenames:
    """Gera os nomes dos 2 .md pra uma execução."""
    ts = _ts_filename()
    sy_slug = school_year.name.lower().replace(" ", "-")
    return ReportFilenames(
        relatorio=f"relatorio-solver-{sy_slug}-{ts}.md",
        grade=f"grade-{sy_slug}-{ts}.md",
    )


def upload_reports(
    school_year: SchoolYear,
    runs: list[SolverRun],
    winning_run: SolverRun,
    uploader: DriveUploader | None = None,
) -> ReportFilenames:
    """Gera os 2 .md e faz upload via `uploader`.

    Args:
        uploader: Implementação de `DriveUploader`. Se None, usa `LocalUploader`.

    Returns:
        Nomes dos arquivos gerados.
    """
    if uploader is None:
        uploader = LocalUploader()

    filenames = filenames_for(school_year)
    tenant_slug = (
        str(school_year.tenant_id)[:8]
        if school_year.tenant_id
        else "default"
    )

    relatorio_content = generate_solver_report_md(school_year, runs)
    grade_content = generate_grade_md(school_year, winning_run)

    relatorio_path = f"{tenant_slug}/relatorios-solver/{filenames.relatorio}"
    grade_path = f"{tenant_slug}/grades-geradas/{filenames.grade}"

    try:
        uploader.upload(relatorio_path, relatorio_content)
        uploader.upload(grade_path, grade_content)
        logger.info("Reports uploaded: %s, %s", filenames.relatorio, filenames.grade)
    except Exception as exc:
        # Falha de upload não derruba o pipeline (§22.2.7)
        logger.exception("Falha no upload de relatórios: %s", exc)

    return filenames
