"""Variante A — Restart (SDD §22.1).

N tentativas independentes do construtor greedy. Cada tentativa é
curta (~18s no orçamento; o solver real ajusta via `tempo_por_tentativa_seg`).
Fica com a melhor `Solution` (menor nº de buracos; empate = maior completude).

Parâmetros lidos de `SolverVariant.parametros`:
- `max_restarts` (int, default 100)
- `tempo_por_tentativa_seg` (int, default 18) — não estritamente respeitado
  nesta implementação (não temos asyncio), apenas para contagem
- `seed_base` (int, default 0)
"""
from __future__ import annotations

from datetime import timedelta

from .constructor import greedy_construct
from .types import Solution, Timetable


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
            # Verifica deadline (best-effort; sem signal real no MVP)
            if deadline and timedelta(0) < deadline and i > 0 and i % 10 == 0:
                # Heurística: a cada 10 restarts, verifica se já gastou
                # tempo demais. Não bloqueante.
                pass

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
