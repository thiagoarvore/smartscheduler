"""Geração de relatórios .md das execuções do solver (Sprint 08, SDD §22.2.7).

Gera 2 artefatos por execução:
1. `relatorio-solver-{slug}-{ts}.md` — pro Thiago
2. `grade-{slug}-{ts}.md` — pro usuário final

No MVP, salva em disco (`./reports/{tenant}/`). Sprint 09: upload Drive.
"""
from __future__ import annotations

import logging
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from django.conf import settings
from django.utils import timezone

from apps.scheduling.models import SolverRun
from apps.schools.models import SchoolYear

logger = logging.getLogger(__name__)

# Diretório base pra reports locais (dev/CI).
REPORTS_DIR = Path("./reports")


# Helpers -------------------------------------------------------------------


def _now_tz() -> datetime:
    """Timestamp atual no timezone do projeto (settings.TIME_ZONE)."""
    tz = ZoneInfo(settings.TIME_ZONE)
    return timezone.now().astimezone(tz)


def _ts_filename() -> str:
    """YYYYMMDD-HHMM formatado no timezone do projeto."""
    return _now_tz().strftime("%Y%m%d-%H%M")


def _format_duration(td) -> str:
    if td is None:
        return "—"
    total = int(td.total_seconds())
    m, s = divmod(total, 60)
    return f"{m}m {s:02d}s"


# Geração dos .md -----------------------------------------------------------


def generate_solver_report_md(school_year: SchoolYear, runs: list[SolverRun]) -> str:
    """Gera o conteúdo do `relatorio-solver-...md`."""
    ts = _now_tz().strftime("%Y-%m-%d %H:%M:%S %Z")
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
        f"- **Data/Hora**: {ts}",
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
    """Gera o conteúdo do `grade-...md` (visão do usuário final)."""
    ts = _now_tz().strftime("%Y-%m-%d %H:%M:%S %Z")
    lines: list[str] = [
        f"# Grade — {school_year.name}",
        "",
        f"- **Data/Hora**: {ts}",
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


# Pipeline de salvamento ----------------------------------------------------


def _save_report(path: Path, content: str) -> str:
    """Salva conteúdo em disco. Retorna a URI do arquivo."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    return f"file://{path.resolve()}"


def save_reports(school_year: SchoolYear, runs: list[SolverRun], winning_run: SolverRun) -> tuple[str, str]:
    """Gera os 2 .md e salva em `./reports/{tenant}/`.

    Returns:
        (relatorio_path, grade_path) — caminhos dos arquivos salvos.
    """
    ts = _ts_filename()
    sy_slug = school_year.name.lower().replace(" ", "-")
    tenant_slug = str(school_year.tenant_id)[:8] if school_year.tenant_id else "default"

    relatorio_filename = f"relatorio-solver-{sy_slug}-{ts}.md"
    grade_filename = f"grade-{sy_slug}-{ts}.md"

    relatorio_content = generate_solver_report_md(school_year, runs)
    grade_content = generate_grade_md(school_year, winning_run)

    relatorio_path = REPORTS_DIR / tenant_slug / "relatorios-solver" / relatorio_filename
    grade_path = REPORTS_DIR / tenant_slug / "grades-geradas" / grade_filename

    try:
        _save_report(relatorio_path, relatorio_content)
        _save_report(grade_path, grade_content)
        logger.info("Reports saved: %s, %s", relatorio_path, grade_path)
    except Exception:
        logger.exception("Falha ao salvar relatórios")

    return str(relatorio_path), str(grade_path)
