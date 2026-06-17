"""Tasks do solver (Sprint 08 item 3.9) e camada de sugestões (Sprint 09 §3.4).

Funções puras, chamáveis diretamente ou via Celery (quando disponível).
Pipeline: run_3_variants → run_variant (A, B, C sequenciais).
Pipeline sugestões: run_suggestions_layer (após solver_run com buracos > 0).
Fila futura: `scheduler-long`, `scheduler-medium`.
"""
from __future__ import annotations

import logging
import time
import traceback
from copy import copy
from datetime import timedelta
from typing import Any

from django.db import transaction
from django.utils import timezone

from apps.scheduling.models import SolverRun, SolverVariant
from apps.scheduling.services.solver import (
    DEFAULT_VARIANT_DEADLINE,
    VARIANT_REGISTRY,
    Timetable,
    transient_retry,
)
from apps.schools.models import SchoolYear

logger = logging.getLogger(__name__)


def build_timetable_from_run(solver_run: SolverRun) -> Timetable:
    """Carrega o `Timetable` a partir de um `SolverRun`.

    No MVP, retorna um Timetable vazio. Sprint futura vai popular
    com WorkloadItem/TimetableSlot/etc.
    """
    return Timetable(
        id=solver_run.school_year_id,
        tenant_id=solver_run.tenant_id,
        school_year_id=solver_run.school_year_id,
        aulas=(),
        slots=(),
    )


@transient_retry
def run_variant(solver_run_id: str) -> dict[str, Any]:
    """Roda uma variante específica, persistindo métricas."""
    solver_run = SolverRun.objects.select_related("variant", "school_year").get(
        id=solver_run_id
    )
    variant_cls = VARIANT_REGISTRY.get(solver_run.variant.nome)
    if variant_cls is None:
        solver_run.status = SolverRun.StatusChoices.FAILED
        solver_run.error_message = f"Variante desconhecida: {solver_run.variant.nome}"
        solver_run.save()
        return {"status": "failed", "error": solver_run.error_message}

    solver_run.status = SolverRun.StatusChoices.RUNNING
    solver_run.started_at = timezone.now()
    solver_run.save(update_fields=["status", "started_at"])

    timetable = build_timetable_from_run(solver_run)
    timetable_with_params = copy(timetable)
    object.__setattr__(timetable_with_params, "_params", solver_run.variant.parametros or {})

    solver_instance = variant_cls()
    start = time.monotonic()
    try:
        solution = solver_instance.solve(timetable_with_params, DEFAULT_VARIANT_DEADLINE)
    except Exception as exc:
        solver_run.status = SolverRun.StatusChoices.FAILED
        solver_run.error_message = f"{type(exc).__name__}: {exc}"
        solver_run.criterio_parada = SolverRun.CriterioParadaChoices.ERRO
        solver_run.finished_at = timezone.now()
        solver_run.tempo_total = timedelta(seconds=time.monotonic() - start)
        solver_run.save()
        logger.exception("run_variant: solver explodiu")
        return {"status": "failed", "error": str(exc)}

    elapsed = timedelta(seconds=time.monotonic() - start)
    solver_run.status = SolverRun.StatusChoices.SUCCESS
    solver_run.finished_at = timezone.now()
    solver_run.tempo_total = elapsed
    solver_run.buracos = solution.total_buracos
    solver_run.completude = solution.completude
    solver_run.iteracoes = solution.iteracoes
    solver_run.restarts = solution.restarts
    solver_run.criterio_parada = _map_criterio(solution.criterio_parada)
    solver_run.solution_json = solution.to_dict()
    if solution.iteracoes > 0 and solution.criterio_parada.value == "zero_buracos":
        solver_run.tempo_ate_1a_solucao = elapsed
    solver_run.save()

    return {
        "status": "success",
        "buracos": solution.total_buracos,
        "completude": solution.completude,
        "tempo_total": elapsed.total_seconds(),
    }


def run_3_variants(
    school_year_id: str,
    disparado_por: str = "user",
    user_id: str | None = None,
) -> list[str]:
    """Encadeia as 3 variantes A → B → C.

    Returns:
        Lista de IDs dos SolverRun criados.
    """
    school_year = SchoolYear.objects.select_related("tenant").get(id=school_year_id)
    variantes = SolverVariant.objects.filter(
        tenant=school_year.tenant,
        is_active=True,
        school_year__isnull=True,
    ).order_by("nome")

    if not variantes.exists():
        raise ValueError(f"Nenhuma variante ativa encontrada para tenant {school_year.tenant_id}")

    run_ids: list[str] = []
    for variante in variantes:
        with transaction.atomic():
            run = SolverRun.objects.create(
                tenant=school_year.tenant,
                variant=variante,
                school_year=school_year,
                disparado_por=disparado_por,
                disparado_por_user_id=user_id,
                seed=timezone.now().microsecond,
            )
            run_ids.append(str(run.id))
            school_year.last_solver_run_at = timezone.now()
            school_year.save(update_fields=["last_solver_run_at"])

    for run_id in run_ids:
        run_variant(run_id)

    return run_ids


def _map_criterio(sol_criterio) -> str:
    """Mapeia Solution.CriterioParada para SolverRun.CriterioParadaChoices."""
    mapping = {
        "timeout": SolverRun.CriterioParadaChoices.TIMEOUT,
        "zero_buracos": SolverRun.CriterioParadaChoices.ZERO_BURACOS,
        "erro": SolverRun.CriterioParadaChoices.ERRO,
        "interrupted": SolverRun.CriterioParadaChoices.INTERRUPTED,
    }
    return mapping.get(sol_criterio.value, SolverRun.CriterioParadaChoices.ERRO)


# ---------------------------------------------------------------------------
# Camada de sugestões (Sprint 09 §3.4)
# ---------------------------------------------------------------------------

# Timeout para a camada de sugestões (§22.4.3: 10 min)
SUGGESTIONS_TIMEOUT_SECONDS = 600


def run_suggestions_layer(solver_run_id: str) -> dict[str, Any]:
    """Executa a camada de sugestões para um SolverRun.

    Steps:
    1. Carrega o SolverRun (com select_related school_year)
    2. Se buracos == 0 ou suggestions_enabled == False: marca disabled, retorna
    3. Marca suggestions_status='running'
    4. Roda SuggestionsService(solver_run).run_all_categories() com timeout de 10 min
    5. Sucesso: suggestions_status='done', suggestions_count=len(result)
    6. Timeout: suggestions_status='timeout'
    7. Exceção: suggestions_status='failed', log, NÃO propaga

    Função pura — pode ser chamada diretamente ou via Celery (quando disponível).
    """
    from apps.scheduling.services.suggestions import SuggestionsService

    try:
        solver_run = SolverRun.objects.select_related("school_year").get(
            id=solver_run_id
        )
    except SolverRun.DoesNotExist:
        logger.error("run_suggestions_layer: SolverRun %s não encontrado", solver_run_id)
        return {"status": "error", "error": "SolverRun não encontrado"}

    school_year = solver_run.school_year

    # Pré-condições (§22.4.3)
    if solver_run.buracos is None or solver_run.buracos == 0 or not school_year.suggestions_enabled:
        solver_run.suggestions_status = SolverRun.SuggestionsStatusChoices.DISABLED
        solver_run.save(update_fields=["suggestions_status"])
        logger.info(
            "run_suggestions_layer: SolverRun %s desativado (buracos=%s, suggestions_enabled=%s)",
            solver_run_id,
            solver_run.buracos,
            school_year.suggestions_enabled,
        )
        return {"status": "disabled", "suggestions_count": 0}

    # Marca como running
    solver_run.suggestions_status = SolverRun.SuggestionsStatusChoices.RUNNING
    solver_run.save(update_fields=["suggestions_status"])

    try:
        # Timeout guard: 10 minutos (§22.4.3)
        service = SuggestionsService(solver_run)
        start = time.monotonic()
        suggestions = service.run_all_categories()
        elapsed = time.monotonic() - start

        if elapsed > SUGGESTIONS_TIMEOUT_SECONDS:
            solver_run.suggestions_status = SolverRun.SuggestionsStatusChoices.TIMEOUT
            solver_run.suggestions_count = len(suggestions)
            solver_run.save(update_fields=["suggestions_status", "suggestions_count"])
            logger.warning(
                "run_suggestions_layer: SolverRun %s timeout após %.1fs (%d sugestões)",
                solver_run_id,
                elapsed,
                len(suggestions),
            )
            return {
                "status": "timeout",
                "suggestions_count": len(suggestions),
                "elapsed_seconds": elapsed,
            }

        solver_run.suggestions_status = SolverRun.SuggestionsStatusChoices.DONE
        solver_run.suggestions_count = len(suggestions)
        solver_run.save(update_fields=["suggestions_status", "suggestions_count"])
        logger.info(
            "run_suggestions_layer: SolverRun %s concluída com %d sugestões (%.1fs)",
            solver_run_id,
            len(suggestions),
            elapsed,
        )
        return {
            "status": "done",
            "suggestions_count": len(suggestions),
            "elapsed_seconds": elapsed,
        }

    except Exception:
        solver_run.suggestions_status = SolverRun.SuggestionsStatusChoices.FAILED
        solver_run.save(update_fields=["suggestions_status"])
        logger.exception(
            "run_suggestions_layer: SolverRun %s falhou", solver_run_id
        )
        # NÃO propaga a exceção (§22.4.5)
        return {
            "status": "failed",
            "error": traceback.format_exc(),
        }
