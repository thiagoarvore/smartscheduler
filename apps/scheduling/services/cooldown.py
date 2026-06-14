"""Service de cooldown do solver (Sprint 08 item 3.11, SDD §22.2.4).

Centraliza a lógica de "o usuário pode disparar o solver agora?"
pra ser reusada por views e tasks.

Regras:
- Cooldown: 1x/hora por SchoolYear
- Se `GRADE_CERTA_COOLDOWN_DISABLED` (em local/dev/test): cooldown desativado
- Mensagem de bloqueio: "última execução: HH:MM (TZ), próxima: HH:MM (TZ)"
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import timedelta
from zoneinfo import ZoneInfo

from django.conf import settings
from django.utils import timezone

from apps.schools.models import SchoolYear

# 1 hora
COOLDOWN_SECONDS = 3600


@dataclass(frozen=True)
class CooldownStatus:
    """Resultado da checagem de cooldown."""

    pode_rodar: bool
    ultima_execucao: timezone.datetime | None
    proxima_janela: timezone.datetime | None
    mensagem: str

    @property
    def em_cooldown(self) -> bool:
        return not self.pode_rodar


def check_cooldown(school_year: SchoolYear) -> CooldownStatus:
    """Verifica se o solver pode ser disparado pra essa SchoolYear.

    - Em ambiente não-produção: sempre pode rodar
    - Em produção: só pode se passou 1h desde `last_solver_run_at`
    """
    if settings.GRADE_CERTA_COOLDOWN_DISABLED:
        return CooldownStatus(
            pode_rodar=True,
            ultima_execucao=school_year.last_solver_run_at,
            proxima_janela=None,
            mensagem="Cooldown desativado (ambiente não-produção).",
        )

    if school_year.last_solver_run_at is None:
        return CooldownStatus(
            pode_rodar=True,
            ultima_execucao=None,
            proxima_janela=None,
            mensagem="Primeira execução — sem cooldown.",
        )

    agora = timezone.now()
    elapsed = agora - school_year.last_solver_run_at
    if elapsed >= timedelta(seconds=COOLDOWN_SECONDS):
        return CooldownStatus(
            pode_rodar=True,
            ultima_execucao=school_year.last_solver_run_at,
            proxima_janela=None,
            mensagem="Janela de cooldown aberta.",
        )

    proxima = school_year.last_solver_run_at + timedelta(seconds=COOLDOWN_SECONDS)
    tz = ZoneInfo(settings.TIME_ZONE)
    mensagem = (
        f"⚠️ A geração da grade só pode ser rodada 1x por hora. "
        f"Última execução: {school_year.last_solver_run_at.astimezone(tz).strftime('%H:%M')} "
        f"({settings.TIME_ZONE}). "
        f"Próxima janela: {proxima.astimezone(tz).strftime('%H:%M')} "
        f"({settings.TIME_ZONE})."
    )
    return CooldownStatus(
        pode_rodar=False,
        ultima_execucao=school_year.last_solver_run_at,
        proxima_janela=proxima,
        mensagem=mensagem,
    )
