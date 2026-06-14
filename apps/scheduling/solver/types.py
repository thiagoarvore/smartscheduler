"""Contratos e tipos de domínio do solver.

Estes tipos são a interface entre o solver e o resto do sistema.
São intencionalmente puros Python (sem dependência de Django) para
que o solver possa ser testado isoladamente e potencialmente
movido para um processo separado no futuro.

Decisões de design (ver SDD §22.1, §22.2.1):
- `Solver.solve(timetable, deadline) -> Solution` é a interface comum
- `Solution.completude` é fração 0.0–1.0 de aulas alocadas
- `Buraco` é qualquer slot sem aula, sem distinguir causa (§20.3)
- `Restricao` separa rígida (invalida grade) de flexível (reduz qualidade)
"""
from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import timedelta
from enum import StrEnum
from typing import Protocol


class RestricaoTipo(StrEnum):
    """Tipo de restrição de domínio."""

    RIGIDA = "rigida"
    FLEXIVEL = "flexivel"


@dataclass(frozen=True)
class Slot:
    """Um slot de tempo no qual uma aula pode acontecer.

    Identifica um (class_group, weekday, order) e metadados
    relevantes para o solver (se aceita dobradinha, etc).
    """

    id: uuid.UUID
    class_group_id: uuid.UUID
    weekday: str  # "monday".."saturday" — alinha com TimetableSlot.WeekdayChoices
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
    """Uma aula que precisa ser alocada (input do solver).

    Representa uma `WorkloadItem` materializada: a demanda
    de X aulas de (turma, disciplina) por semana. Pode ter
    `is_double_lesson=True` para exigir alocação em slots
    consecutivos do mesmo dia (§22 — Conceitual, decisão 4).
    """

    id: uuid.UUID
    class_group_id: uuid.UUID
    subject_id: uuid.UUID
    teacher_id: uuid.UUID | None  # pode ser None se múltiplos professores podem lecionar
    weekly_hours: int  # quantas vezes por semana
    is_double_lesson: bool = False

    def __post_init__(self) -> None:
        if self.id is None:
            raise ValueError("Aula.id é obrigatório")
        if self.weekly_hours < 0:
            raise ValueError("Aula.weekly_hours deve ser >= 0")


@dataclass(frozen=True)
class Disponibilidade:
    """Janela de disponibilidade de um professor (TeacherAvailability).

    Se o professor tem registros, o solver **só** pode alocar
    aulas para ele dentro de uma dessas janelas. Se o professor
    não tem registros, é considerado sempre disponível.
    """

    teacher_id: uuid.UUID
    weekday: str
    start_order: int  # primeira aula que o professor pode dar
    end_order: int  # última aula (inclusiva)


@dataclass(frozen=True)
class Restricao:
    """Restrição de domínio (rígida ou flexível).

    O solver deve respeitar RIGIDA inviolavelmente; FLEXIVEL é
    objetivo de otimização mas pode ser violada.
    """

    tipo: RestricaoTipo
    descricao: str
    # Avalia se uma alocação parcial a satisfaz
    avaliador: str = ""  # nome do callable no registry (não usado no MVP)


@dataclass(frozen=True)
class Timetable:
    """Input do solver — descrição completa do problema.

    Carregado de `Timetable`/`TimetableSlot`/`WorkloadItem`/`Teacher`/
    `TeacherAvailability` antes de chamar `Solver.solve()`.
    """

    id: uuid.UUID
    tenant_id: uuid.UUID
    school_year_id: uuid.UUID
    aulas: tuple[Aula, ...]
    slots: tuple[Slot, ...]
    disponibilidades: tuple[Disponibilidade, ...] = field(default_factory=tuple)
    restricoes: tuple[Restricao, ...] = field(default_factory=tuple)

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
    """Um slot (dia × número da aula) que ficou sem aula (§20.3).

    O solver **não distingue** a causa do buraco — apenas registra
    que o slot ficou vazio. A camada de sugestões (§20.4, Sprint 09)
    é que investiga a causa.
    """

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
    teacher_id: uuid.UUID | None


@dataclass
class Solution:
    """Output do solver — uma grade (possivelmente parcial).

    Campos:
    - `assignments`: aulas alocadas (1 entrada por aula-por-semana)
    - `buracos`: slots que ficaram vazios
    - `completude`: fração 0.0–1.0 de aulas alocadas
    - `iteracoes`: contador pra telemetria
    - `restarts`: contador (relevante pra Variante A)
    - `criterio_parada`: como o solver encerrou
    """

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
    """Erro genérico do solver (bug, config inválida, etc)."""


class UnsatisfiableError(SolverError):
    """O problema é insolúvel dentro das restrições — não adianta tentar mais."""


class Solver(Protocol):
    """Interface comum das 3 variantes (SDD §22.1).

    Cada variante implementa esta interface do zero (§22.1,
    decisão sobre compartilhamento de código). A interface é
    mínima: recebe um `Timetable` e um `deadline`, retorna
    uma `Solution`.
    """

    def solve(self, timetable: Timetable, deadline: timedelta) -> Solution:
        ...
