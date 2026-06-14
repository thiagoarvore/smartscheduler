"""Construtor greedy compartilhado pelas 3 variantes (A/B/C).

O construtor é deliberadamente simples (§22.1 — "construtor ingênuo"):
ordena `Aula` por `weekly_hours DESC` e aloca cada uma no primeiro slot
livre compatível. Não compartilha heurística entre variantes (cada uma
pode sobrescrever — §22.1, decisão sobre compartilhamento de código).

Por que greedy e não mais sofisticado?
- 3 variantes já são a experimentação. Cada uma vai gastar budget
  de exploração diferente em cima desse mesmo ponto de partida.
- Greedy é determinístico dado o seed, o que permite comparar variantes
  isolando o efeito do "exploration strategy".
"""
from __future__ import annotations

import random
from collections import defaultdict

from .types import (
    Assignment,
    Buraco,
    Disponibilidade,
    Slot,
    Solution,
    Timetable,
)

# Mapeamento weekday → ordem numérica (0=segunda, 6=domingo)
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
    """Verifica se o professor está disponível no slot.

    Se o professor não tem registros de disponibilidade, é considerado
    sempre disponível (correto pelo critério de Sprint 07 — professor
    sem disponibilidade = disponível).
    """
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
    """Construtor greedy: aloca cada `Aula` no primeiro slot compatível.

    Regras respeitadas (restrições rígidas mínimas do MVP):
    - 1 turma tem no máximo 1 aula por slot
    - 1 professor tem no máximo 1 aula por slot
    - Professor só recebe aula se estiver disponível no slot
    - Se `aula.teacher_id` é None, qualquer professor habilitado serve
      (no MVP, sem habilitações: primeiro professor disponível)

    Não respeitado (fica como buraco):
    - Preferência de horário do professor
    - Distribuição ao longo da semana
    - Dobradinha (aula dupla) é tentada mas não obrigatória
    - Janelas (buracos) do professor
    """
    rng = random.Random(seed)
    aulas_list = list(timetable.aulas)
    # Estabilidade: empata por hash, desempata por rng pra ter variedade entre seeds
    aulas_list.sort(key=lambda a: (-a.weekly_hours, rng.random()))

    slots_list = list(timetable.slots)
    slots_by_class: dict[object, list[Slot]] = defaultdict(list)
    for s in slots_list:
        slots_by_class[s.class_group_id].append(s)
    for k in slots_by_class:
        slots_by_class[k].sort(key=lambda s: (_WEEKDAY_ORDER.get(s.weekday, 99), s.order))

    # Estado: slots ocupados por turma e por professor
    occupied_class: set[object] = set()
    occupied_teacher: set[tuple[object, str, int]] = set()
    assignments: list[Assignment] = []
    buracos: list[Buraco] = []

    for aula in aulas_list:
        candidates = list(slots_by_class.get(aula.class_group_id, []))
        for slot in candidates:
            if slot.id in occupied_class:
                continue
            weekday = _WEEKDAY_ORDER.get(slot.weekday, -1)
            teacher_key = (aula.teacher_id, slot.weekday, weekday) if aula.teacher_id else None
            if aula.teacher_id:
                teacher_slot_key = (aula.teacher_id, slot.weekday, slot.order)
                if teacher_slot_key in occupied_teacher:
                    continue
                if not _teacher_available(aula.teacher_id, slot, timetable.disponibilidades):
                    continue
            # Aloca
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
            if teacher_key is not None:
                occupied_teacher.add((aula.teacher_id, slot.weekday, slot.order))
            break  # próxima aula
        else:
            # Sem slot compatível — não conta como buraco, é uma
            # alocação que falhou. Buracos são slots vazios.
            pass

    # Calcula buracos: slots que existem mas não foram ocupados
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
