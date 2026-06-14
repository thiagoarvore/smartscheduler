"""Solver de grade escolar — 3 variantes (SDD §22.1, Sprint 08).

Contém tipos de domínio, construtor greedy, 3 variantes (A, B, C),
e wrapper de retry transiente. Tudo num único módulo pra seguir
o padrão flat do resto do projeto (models.py, views.py, etc).

Decisões de design (ver SDD §22.1, §22.2.1):
- `Solver.solve(timetable, deadline) -> Solution` é a interface comum
- `Solution.completude` é fração 0.0–1.0 de aulas alocadas
- `Buraco` é qualquer slot sem aula, sem distinguir causa (§20.3)
- `Restricao` separa rígida (invalida grade) de flexível (reduz qualidade)
- 3 variantes coexistem com `is_active=True`; "melhor" é read/query
- Retry é automático e silencioso (1x, sem backoff)
"""
from __future__ import annotations

import functools
import logging
import random
import time
import uuid
from collections import defaultdict
from dataclasses import dataclass
from datetime import timedelta
from enum import StrEnum
from typing import Any, Protocol

logger = logging.getLogger(__name__)

# Deadline padrão por variante (SDD §22.1: 30 min)
DEFAULT_VARIANT_DEADLINE = timedelta(minutes=30)


# =========================================================================
# Tipos de domínio (antes em solver/types.py)
# =========================================================================


class RestricaoTipo(StrEnum):
    """Tipo de restrição de domínio."""

    RIGIDA = "rigida"
    FLEXIVEL = "flexivel"


@dataclass(frozen=True)
class Slot:
    """Um slot de tempo no qual uma aula pode acontecer."""

    id: uuid.UUID
    class_group_id: uuid.UUID
    weekday: str  # "monday".."saturday"
    order: int
    accepts_double_lesson: bool = False

    def __post_init__(self) -> None:
        if self.id is None:
            raise ValueError("Slot.id é obrigatório")
        if self.class_group_id is None:
            raise ValueError("Slot.class_group_id é obrigatório")
        if self.order < 1:
            raise ValueError("Slot.order deve ser >= 1")


@dataclass(frozen=True)
class Aula:
    """Uma aula que precisa ser alocada (input do solver)."""

    id: uuid.UUID
    class_group_id: uuid.UUID
    subject_id: uuid.UUID
    teacher_id: uuid.UUID | None = None
    weekly_hours: int = 1
    is_double_lesson: bool = False

    def __post_init__(self) -> None:
        if self.id is None:
            raise ValueError("Aula.id é obrigatório")
        if self.weekly_hours < 0:
            raise ValueError("Aula.weekly_hours deve ser >= 0")


@dataclass(frozen=True)
class Disponibilidade:
    """Janela de disponibilidade de um professor."""

    teacher_id: uuid.UUID
    weekday: str
    start_order: int
    end_order: int


@dataclass(frozen=True)
class Restricao:
    """Restrição de domínio (rígida ou flexível)."""

    tipo: RestricaoTipo
    descricao: str
    avaliador: str = ""


@dataclass(frozen=True)
class Timetable:
    """Input do solver — descrição completa do problema."""

    id: uuid.UUID
    tenant_id: uuid.UUID
    school_year_id: uuid.UUID
    aulas: tuple[Aula, ...] = ()
    slots: tuple[Slot, ...] = ()
    disponibilidades: tuple[Disponibilidade, ...] = ()
    restricoes: tuple[Restricao, ...] = ()

    def __post_init__(self) -> None:
        if self.id is None:
            raise ValueError("Timetable.id é obrigatório")
        if self.tenant_id is None:
            raise ValueError("Timetable.tenant_id é obrigatório")
        if self.school_year_id is None:
            raise ValueError("Timetable.school_year_id é obrigatório")

    @property
    def total_aulas(self) -> int:
        """Total de instâncias de aulas a alocar (somando weekly_hours)."""
        return sum(a.weekly_hours for a in self.aulas)


@dataclass(frozen=True)
class Buraco:
    """Um slot que ficou sem aula (§20.3)."""

    slot_id: uuid.UUID
    class_group_id: uuid.UUID
    weekday: str
    order: int


@dataclass
class Assignment:
    """Uma aula alocada em um slot específico (output do solver)."""

    aula_id: uuid.UUID
    slot_id: uuid.UUID
    class_group_id: uuid.UUID
    subject_id: uuid.UUID
    teacher_id: uuid.UUID | None = None


@dataclass
class Solution:
    """Output do solver — uma grade (possivelmente parcial)."""

    class CriterioParada(StrEnum):
        TIMEOUT = "timeout"
        ZERO_BURACOS = "zero_buracos"
        ERRO = "erro"
        INTERRUPTED = "interrupted"

    assignments: list[Assignment]
    buracos: list[Buraco]
    completude: float
    criterio_parada: CriterioParada
    iteracoes: int = 0
    restarts: int = 0

    def __post_init__(self) -> None:
        if not 0.0 <= self.completude <= 1.0:
            raise ValueError(
                f"Solution.completude deve estar em [0, 1], recebeu {self.completude}"
            )

    @property
    def total_buracos(self) -> int:
        return len(self.buracos)

    def to_dict(self) -> dict:
        """Serializa para JSON (pra persistir em solver_run.solution_json)."""
        return {
            "assignments": [
                {
                    "aula_id": str(a.aula_id),
                    "slot_id": str(a.slot_id),
                    "class_group_id": str(a.class_group_id),
                    "subject_id": str(a.subject_id),
                    "teacher_id": str(a.teacher_id) if a.teacher_id else None,
                }
                for a in self.assignments
            ],
            "buracos": [
                {
                    "slot_id": str(b.slot_id),
                    "class_group_id": str(b.class_group_id),
                    "weekday": b.weekday,
                    "order": b.order,
                }
                for b in self.buracos
            ],
            "completude": self.completude,
            "criterio_parada": self.criterio_parada.value,
            "iteracoes": self.iteracoes,
            "restarts": self.restarts,
        }

    @classmethod
    def from_dict(cls, data: dict) -> Solution:
        """Desserializa de JSON (pra carregar de solver_run.solution_json)."""
        return cls(
            assignments=[
                Assignment(
                    aula_id=uuid.UUID(a["aula_id"]),
                    slot_id=uuid.UUID(a["slot_id"]),
                    class_group_id=uuid.UUID(a["class_group_id"]),
                    subject_id=uuid.UUID(a["subject_id"]),
                    teacher_id=uuid.UUID(a["teacher_id"]) if a["teacher_id"] else None,
                )
                for a in data["assignments"]
            ],
            buracos=[
                Buraco(
                    slot_id=uuid.UUID(b["slot_id"]),
                    class_group_id=uuid.UUID(b["class_group_id"]),
                    weekday=b["weekday"],
                    order=b["order"],
                )
                for b in data["buracos"]
            ],
            completude=data["completude"],
            criterio_parada=Solution.CriterioParada(data["criterio_parada"]),
            iteracoes=data.get("iteracoes", 0),
            restarts=data.get("restarts", 0),
        )


class SolverError(Exception):
    """Erro genérico do solver."""


class UnsatisfiableError(SolverError):
    """O problema é insolúvel dentro das restrições."""


class Solver(Protocol):
    """Interface comum das 3 variantes (SDD §22.1)."""

    def solve(self, timetable: Timetable, deadline: timedelta) -> Solution:
        ...


# =========================================================================
# Construtor greedy (antes em solver/constructor.py)
# =========================================================================

_WEEKDAY_ORDER: dict[str, int] = {
    "monday": 0,
    "tuesday": 1,
    "wednesday": 2,
    "thursday": 3,
    "friday": 4,
    "saturday": 5,
    "sunday": 6,
}


def _teacher_available(
    teacher_id: object,
    slot: Slot,
    disponibilidades: tuple[Disponibilidade, ...],
) -> bool:
    """Verifica se o professor está disponível no slot."""
    avail = [d for d in disponibilidades if d.teacher_id == teacher_id]
    if not avail:
        return True
    weekday_order = _WEEKDAY_ORDER.get(slot.weekday, -1)
    for d in avail:
        if (
            _WEEKDAY_ORDER.get(d.weekday, -1) == weekday_order
            and d.start_order <= slot.order <= d.end_order
        ):
            return True
    return False


def greedy_construct(
    timetable: Timetable,
    seed: int = 0,
) -> Solution:
    """Construtor greedy: aloca cada `Aula` no primeiro slot compatível."""
    rng = random.Random(seed)
    aulas_list = list(timetable.aulas)
    aulas_list.sort(key=lambda a: (-a.weekly_hours, rng.random()))

    slots_list = list(timetable.slots)
    slots_by_class: dict[object, list[Slot]] = defaultdict(list)
    for s in slots_list:
        slots_by_class[s.class_group_id].append(s)
    for k in slots_by_class:
        slots_by_class[k].sort(key=lambda s: (_WEEKDAY_ORDER.get(s.weekday, 99), s.order))

    occupied_class: set[object] = set()
    occupied_teacher: set[tuple[object, str, int]] = set()
    assignments: list[Assignment] = []
    buracos: list[Buraco] = []

    for aula in aulas_list:
        candidates = list(slots_by_class.get(aula.class_group_id, []))
        for slot in candidates:
            if slot.id in occupied_class:
                continue
            if aula.teacher_id:
                teacher_slot_key = (aula.teacher_id, slot.weekday, slot.order)
                if teacher_slot_key in occupied_teacher:
                    continue
                if not _teacher_available(aula.teacher_id, slot, timetable.disponibilidades):
                    continue
            assignments.append(
                Assignment(
                    aula_id=aula.id,
                    slot_id=slot.id,
                    class_group_id=aula.class_group_id,
                    subject_id=aula.subject_id,
                    teacher_id=aula.teacher_id,
                )
            )
            occupied_class.add(slot.id)
            if aula.teacher_id:
                occupied_teacher.add((aula.teacher_id, slot.weekday, slot.order))
            break

    for s in slots_list:
        if s.id not in occupied_class:
            buracos.append(
                Buraco(
                    slot_id=s.id,
                    class_group_id=s.class_group_id,
                    weekday=s.weekday,
                    order=s.order,
                )
            )

    total_aulas = timetable.total_aulas
    completude = 1.0 if total_aulas == 0 else len(assignments) / total_aulas
    criterio_parada = (
        Solution.CriterioParada.ZERO_BURACOS
        if not buracos and total_aulas > 0
        else Solution.CriterioParada.TIMEOUT
    )

    return Solution(
        assignments=assignments,
        buracos=buracos,
        completude=completude,
        criterio_parada=criterio_parada,
        iteracoes=0,
        restarts=0,
    )


# =========================================================================
# Variante A — Restart (antes em solver/variant_a_restart.py)
# =========================================================================


class VariantARestart:
    """Variante A: N restarts independentes do construtor greedy."""

    def solve(self, timetable: Timetable, deadline: timedelta) -> Solution:
        params = getattr(timetable, "_params", {}) or {}
        max_restarts = int(params.get("max_restarts", 100))
        seed_base = int(params.get("seed_base", 0))

        best: Solution | None = None
        last_i = 0
        for i in range(max_restarts):
            last_i = i
            seed = seed_base + i
            current = greedy_construct(timetable, seed=seed)
            if best is None or _is_better(current, best):
                best = current
                if best.total_buracos == 0:
                    break

        assert best is not None, "max_restarts >= 1 esperado"
        best.restarts = last_i + 1
        return best


def _is_better(candidate: Solution, current: Solution) -> bool:
    """Critério de seleção: menos buracos; empate = maior completude."""
    if candidate.total_buracos < current.total_buracos:
        return True
    if candidate.total_buracos == current.total_buracos:
        return candidate.completude > current.completude
    return False


# =========================================================================
# Variante B — Hill Climbing (antes em solver/variant_b_hill_climbing.py)
# =========================================================================


class VariantBHillClimbing:
    """Variante B: 1 construção + busca local gulosa."""

    def solve(self, timetable: Timetable, deadline: timedelta) -> Solution:
        params = getattr(timetable, "_params", {}) or {}
        vizinhos_por_iter = int(params.get("vizinhos_por_iteracao", 10))
        max_iteracoes = int(params.get("max_iteracoes", 100_000))
        seed = int(params.get("seed_base", 0))
        rng = random.Random(seed)

        best = greedy_construct(timetable, seed=seed)
        deadline_seconds = deadline.total_seconds() if deadline else 0
        start = time.monotonic()
        iter_count = 0

        for it in range(max_iteracoes):
            iter_count = it + 1
            if deadline_seconds > 0 and time.monotonic() - start > deadline_seconds:
                break
            if best.total_buracos == 0:
                break

            improved = False
            for _ in range(vizinhos_por_iter):
                neighbor = _try_swap(best, timetable, rng)
                if neighbor is not None and neighbor.total_buracos < best.total_buracos:
                    best = neighbor
                    improved = True
                    break

            if not improved:
                break

        criterio_parada = (
            Solution.CriterioParada.ZERO_BURACOS
            if best.total_buracos == 0
            else Solution.CriterioParada.TIMEOUT
        )
        best.iteracoes = iter_count
        best.criterio_parada = criterio_parada
        return best


def _try_swap(
    current: Solution,
    timetable: Timetable,
    rng: random.Random,
) -> Solution | None:
    """Tenta 1 swap entre 1 assignment e 1 buraco. Retorna nova Solution ou None."""
    if len(current.assignments) < 2 or not current.buracos:
        return None

    a_idx = rng.randrange(len(current.assignments))
    buraco = rng.choice(current.buracos)
    original = current.assignments[a_idx]

    if any(
        a.slot_id == buraco.slot_id
        for a in current.assignments
        if a.class_group_id == original.class_group_id
    ):
        return None

    new_assignments = [
        Assignment(
            aula_id=a.aula_id,
            slot_id=buraco.slot_id if a is original else a.slot_id,
            class_group_id=a.class_group_id,
            subject_id=a.subject_id,
            teacher_id=a.teacher_id,
        )
        for a in current.assignments
    ]
    new_buracos = [
        Buraco(
            slot_id=original.slot_id,
            class_group_id=original.class_group_id,
            weekday=_slot_weekday(timetable, original.slot_id),
            order=_slot_order(timetable, original.slot_id),
        )
        if b.slot_id == buraco.slot_id
        else b
        for b in current.buracos
    ]
    new_buracos = [b for b in new_buracos if b.slot_id != buraco.slot_id]

    completude = len(new_assignments) / timetable.total_aulas if timetable.total_aulas else 1.0
    return Solution(
        assignments=new_assignments,
        buracos=new_buracos,
        completude=completude,
        criterio_parada=current.criterio_parada,
        iteracoes=current.iteracoes + 1,
        restarts=current.restarts,
    )


def _slot_weekday(timetable: Timetable, slot_id: object) -> str:
    for s in timetable.slots:
        if s.id == slot_id:
            return s.weekday
    return ""


def _slot_order(timetable: Timetable, slot_id: object) -> int:
    for s in timetable.slots:
        if s.id == slot_id:
            return s.order
    return 0


# =========================================================================
# Variante C — Híbrido (antes em solver/variant_c_hybrid.py)
# =========================================================================


class VariantCHybrid:
    """Variante C: N construções × hill climbing."""

    def solve(self, timetable: Timetable, deadline: timedelta) -> Solution:
        params = getattr(timetable, "_params", {}) or {}
        max_construcoes = int(params.get("max_construcoes", 5))
        seed_base = int(params.get("seed_base", 0))
        tempo_por_construcao = int(params.get("tempo_por_construcao_seg", 120))

        deadline_seconds = deadline.total_seconds() if deadline else 0
        start = time.monotonic()
        budget_per_construction = (
            timedelta(seconds=min(tempo_por_construcao, int(deadline_seconds / max_construcoes)))
            if deadline_seconds > 0
            else timedelta(seconds=tempo_por_construcao)
        )

        best: Solution | None = None
        total_restarts = 0
        for i in range(max_construcoes):
            if deadline_seconds > 0 and time.monotonic() - start > deadline_seconds:
                break
            seed = seed_base + i
            current_params = dict(params)
            current_params["seed_base"] = seed
            timetable_with_params = _timetable_with_params(timetable, current_params)
            candidate = VariantBHillClimbing().solve(timetable_with_params, budget_per_construction)
            if best is None or _is_better(candidate, best):
                best = candidate
                if best.total_buracos == 0:
                    break
            total_restarts += 1

        assert best is not None, "max_construcoes >= 1 esperado"
        best.restarts = total_restarts
        return best


def _timetable_with_params(timetable: Timetable, params: dict) -> Timetable:
    """Cria cópia do Timetable com `_params` setado (hack leve pro MVP)."""
    from copy import copy

    new = copy(timetable)
    object.__setattr__(new, "_params", params)
    return new


# =========================================================================
# Retry transiente (antes em solver/retry.py)
# =========================================================================


def _transient_exceptions() -> tuple[type[BaseException], ...]:
    """Importações lazy pra evitar import-time errors sem Django/Celery."""
    from django.db.utils import InterfaceError, OperationalError
    from redis.exceptions import ConnectionError as RedisConnectionError

    extras: list[type[BaseException]] = []
    try:
        from celery.exceptions import TimeoutError as CeleryTimeoutError

        extras.append(CeleryTimeoutError)
    except ImportError:
        pass

    return (OperationalError, InterfaceError, RedisConnectionError, *extras)


def transient_retry(
    func: Any = None,
    *,
    max_attempts: int = 2,
) -> Any:
    """Decorator que aplica retry transiente (1x, sem backoff).

    Uso:
        @transient_retry
        def minha_task(...): ...

        @transient_retry(max_attempts=3)
        def minha_task_custom(...): ...
    """
    def decorator(f: Any) -> Any:
        @functools.wraps(f)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            transients = _transient_exceptions()
            last_exc: BaseException | None = None
            for attempt in range(1, max_attempts + 1):
                try:
                    return f(*args, **kwargs)
                except transients as exc:
                    last_exc = exc
                    if attempt >= max_attempts:
                        logger.warning(
                            "transient_retry: esgotadas %d tentativas em %s (%s)",
                            max_attempts,
                            f.__qualname__,
                            exc,
                        )
                        raise
                    logger.info(
                        "transient_retry: tentativa %d falhou em %s (%s), retentando",
                        attempt,
                        f.__qualname__,
                        exc,
                    )
            assert last_exc is not None
            raise last_exc
        return wrapper

    if func is not None and callable(func):
        return decorator(func)
    return decorator


# =========================================================================
# Variant registry (antes em tasks.py)
# =========================================================================


VARIANT_REGISTRY = {
    "A-Restart": VariantARestart,
    "B-HillClimbing": VariantBHillClimbing,
    "C-Hybrid": VariantCHybrid,
}
