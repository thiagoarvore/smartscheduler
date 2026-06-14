"""Variante B — Hill Climbing (SDD §22.1, §22.1 nota sobre terminologia).

1 construção inicial (greedy) + hill climbing até bater timeout ou
0 buracos. Só aceita swaps que **melhoram** a função objetivo
(nº de buracos). Sem temperatura — não é simulated annealing.

Parâmetros lidos de `SolverVariant.parametros`:
- `vizinhos_por_iteracao` (int, default 10) — quantos swaps candidatos gerar
- `max_iteracoes` (int, default 100000)
"""
from __future__ import annotations

import random
import time
from datetime import timedelta

from .constructor import greedy_construct
from .types import Assignment, Buraco, Solution, Timetable


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
        first_valid_iter: int | None = None
        iter_count = 0

        for it in range(max_iteracoes):
            iter_count = it + 1
            if deadline_seconds > 0 and time.monotonic() - start > deadline_seconds:
                break
            if best.total_buracos == 0:
                if first_valid_iter is None:
                    first_valid_iter = it
                break

            # Gera `vizinhos_por_iter` candidatos (swap de 2 assignments)
            # e aplica o primeiro que melhora
            improved = False
            for _ in range(vizinhos_por_iter):
                neighbor = _try_swap(best, timetable, rng)
                if neighbor is not None and neighbor.total_buracos < best.total_buracos:
                    best = neighbor
                    improved = True
                    if first_valid_iter is None:
                        first_valid_iter = it
                    break

            if not improved:
                # Sem melhora por uma rodada: provavelmente ótimo local
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
    """Tenta 1 swap entre 2 assignments. Retorna nova Solution ou None.

    Swap = pega 2 assignments e troca os slots deles. Se ambos os
    slots são compatíveis (mesmo weekday/order ou já não conflitam),
    a nova grade é válida.

    No MVP, simplificamos: pega 2 assignments e troca o `slot_id`
    de um pelo slot (vago) do outro. Verifica que o slot vaga
    realmente estava vaga (i.e., o outro assignment **não** ocupava
    aquele slot, mas sim algum outro slot que esteja vago).
    """
    if len(current.assignments) < 2 or not current.buracos:
        return None

    # Pega 1 assignment aleatório e 1 buraco aleatório
    a_idx = rng.randrange(len(current.assignments))
    buraco = rng.choice(current.buracos)
    original = current.assignments[a_idx]

    # Não vamos trocar pra slot conflitante com outro assignment
    # da mesma turma. Verificação rápida:
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
            weekday=timetable_slot_weekday(timetable, original.slot_id),
            order=timetable_slot_order(timetable, original.slot_id),
        )
        if b.slot_id == buraco.slot_id
        else b
        for b in current.buracos
    ]
    # Remove o buraco que foi preenchido
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


def timetable_slot_weekday(timetable: Timetable, slot_id: object) -> str:
    for s in timetable.slots:
        if s.id == slot_id:
            return s.weekday
    return ""


def timetable_slot_order(timetable: Timetable, slot_id: object) -> int:
    for s in timetable.slots:
        if s.id == slot_id:
            return s.order
    return 0
