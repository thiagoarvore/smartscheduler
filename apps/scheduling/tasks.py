"""Tasks assíncronas do solver (Sprint 08 item 3.9).

Implementação: o projeto não tem Celery configurado (sem `celery` em
`pyproject.toml`). Pra deixar testável, as tasks são funções Python
puras que podem ser chamadas diretamente OU via `apply_async` quando
Celery for adicionado. O decorator `@shared_task` (de celery.contrib)
só é aplicado se Celery estiver disponível — caso contrário, a função
é exposta diretamente.

Pipeline (Sprint 08, §22.2.5):
1. `run_3_variants` — encadeia A → B → C
2. Cada variante roda em `run_variant_X` com retry transiente
3. Após as 3, atualiza `SchoolYear.last_solver_run_at`
4. Stub pra Sprint 09: dispara `run_suggestions_layer` (não implementada)

Fila: `scheduler-long` (configurável via `TASK_ROUTES` no Celery).
"""
from __future__ import annotations

import logging
import time
from copy import copy
from datetime import timedelta
from typing import Any

from django.db import transaction
from django.utils import timezone

from apps.scheduling.models import SolverRun, SolverVariant
from apps.scheduling.solver.retry import transient_retry
from apps.scheduling.solver.types import (
    Solver,
    Timetable,
)
from apps.scheduling.solver.variant_a_restart import VariantARestart
from apps.scheduling.solver.variant_b_hill_climbing import VariantBHillClimbing
from apps.scheduling.solver.variant_c_hybrid import VariantCHybrid

logger = logging.getLogger(__name__)

# Variantes disponíveis (registry; chave = SolverVariant.NomeChoices)
VARIANT_REGISTRY: dict[str, type[Solver]] = {
    SolverVariant.NomeChoices.A_RESTART: VariantARestart,
    SolverVariant.NomeChoices.B_HILL_CLIMBING: VariantBHillClimbing,
    SolverVariant.NomeChoices.C_HYBRID: VariantCHybrid,
}

# Variante → deadline (SDD §22.1: 30 min por variante)
DEFAULT_VARIANT_DEADLINE = timedelta(minutes=30)


def build_timetable_from_run(solver_run: SolverRun) -> Timetable:
    """Carrega o `Timetable` a partir de um `SolverRun`.

    No MVP, este é um stub que retorna um Timetable vazio. Sprint
    futura vai popular com `WorkloadItem`/`TimetableSlot`/etc.
    Por enquanto, a UI/view pode chamar as tasks mas o solver
    roda sem dados reais — só pra exercitar o pipeline.
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
    """Roda uma variante específica, persistindo métricas.

    Args:
        solver_run_id: UUID do `SolverRun` (string para serialização Celery).

    Returns:
        Dict com status final e métricas pra inspeção.
    """
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

    deadline = DEFAULT_VARIANT_DEADLINE
    timetable = build_timetable_from_run(solver_run)
    # Injeta parâmetros da variante no timetable
    timetable_with_params = copy(timetable)
    object.__setattr__(timetable_with_params, "_params", solver_run.variant.parametros or {})

    solver_instance = variant_cls()
    start = time.monotonic()
    try:
        solution = solver_instance.solve(timetable_with_params, deadline)
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
        # Aproximação: tempo até 1ª solução válida ≈ tempo_total / iteracoes
        # (no MVP, sem telemetria fina). Pode refinar no futuro.
        solver_run.tempo_ate_1a_solucao = elapsed
    solver_run.save()

    return {
        "status": "success",
        "buracos": solution.total_buracos,
        "completude": solution.completude,
        "tempo_total": elapsed.total_seconds(),
    }


def run_3_variants(school_year_id: str, disparado_por: str = "user", user_id: str | None = None) -> list[str]:
    """Encadeia as 3 variantes A → B → C.

    Args:
        school_year_id: UUID do SchoolYear.
        disparado_por: 'user' | 'cron' | 'api'.
        user_id: UUID do usuário que disparou (nullable).

    Returns:
        Lista de IDs dos `SolverRun` criados (1 por variante).
    """
    from apps.schools.models import SchoolYear

    school_year = SchoolYear.objects.select_related("tenant").get(id=school_year_id)
    variantes = SolverVariant.objects.filter(
        tenant=school_year.tenant,
        is_active=True,
        school_year__isnull=True,  # só variantes globais
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
            # Atualiza cooldown
            school_year.last_solver_run_at = timezone.now()
            school_year.save(update_fields=["last_solver_run_at"])

    # Executa sequencialmente
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


# Quando Celery for adicionado, descomentar:
#
# from celery import shared_task
#
# @shared_task(queue="scheduler-long", bind=True)
# def run_variant_task(self, solver_run_id: str) -> dict:
#     return run_variant(solver_run_id)
#
# @shared_task(queue="scheduler-long", bind=True)
# def run_3_variants_task(self, school_year_id: str, **kwargs) -> list[str]:
#     return run_3_variants(school_year_id, **kwargs)
