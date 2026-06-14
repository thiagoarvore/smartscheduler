"""Variante C — Híbrido (SDD §22.1).

Várias construções (cada uma com seed diferente) + hill climbing
em cada. Fica com a melhor `Solution` global.

Parâmetros lidos de `SolverVariant.parametros`:
- `max_construcoes` (int, default 5)
- `vizinhos_por_iteracao` (int, default 10) — passada pra hill climbing
- `tempo_por_construcao_seg` (int, default 120)
"""
from __future__ import annotations

import time
from datetime import timedelta

from .types import Solution, Timetable
from .variant_a_restart import _is_better
from .variant_b_hill_climbing import VariantBHillClimbing


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
            # Verifica deadline global
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
