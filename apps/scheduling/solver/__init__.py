"""Pacote do solver.

Re-exporta os tipos públicos para que o resto do sistema
possa fazer `from apps.scheduling.solver import Timetable, Solution, ...`
em vez de importar submódulos.
"""
from .types import (
    Assignment,
    Aula,
    Buraco,
    Disponibilidade,
    Restricao,
    RestricaoTipo,
    Slot,
    Solution,
    Solver,
    SolverError,
    Timetable,
    UnsatisfiableError,
)

__all__ = [
    "Assignment",
    "Aula",
    "Buraco",
    "Disponibilidade",
    "Restricao",
    "RestricaoTipo",
    "Slot",
    "Solution",
    "Solver",
    "SolverError",
    "Timetable",
    "UnsatisfiableError",
]
