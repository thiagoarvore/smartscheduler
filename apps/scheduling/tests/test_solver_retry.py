"""Testes do wrapper de retry transiente (Sprint 08 item 3.10)."""
from __future__ import annotations

import pytest
from django.db.utils import OperationalError

from apps.scheduling.solver.retry import transient_retry


def test_sucesso_na_primeira_tentativa() -> None:
    calls: list[int] = []

    @transient_retry
    def func() -> str:
        calls.append(1)
        return "ok"

    assert func() == "ok"
    assert len(calls) == 1


def test_retry_1x_em_transiente() -> None:
    calls: list[int] = []

    @transient_retry
    def func() -> str:
        calls.append(1)
        if len(calls) == 1:
            raise OperationalError("connection lost")
        return "ok"

    assert func() == "ok"
    assert len(calls) == 2


def test_nao_retenta_excecao_nao_transiente() -> None:
    calls: list[int] = []

    @transient_retry
    def func() -> str:
        calls.append(1)
        raise ValueError("bug no código")

    with pytest.raises(ValueError, match="bug"):
        func()
    assert len(calls) == 1  # não retentou


def test_esgota_2_tentativas_e_re_propaga() -> None:
    calls: list[int] = []

    @transient_retry
    def func() -> str:
        calls.append(1)
        raise OperationalError(f"falha {len(calls)}")

    with pytest.raises(OperationalError, match="falha 2"):
        func()
    assert len(calls) == 2  # exatamente 2 tentativas


def test_max_attempts_customizado() -> None:
    calls: list[int] = []

    @transient_retry(max_attempts=3)
    def func() -> str:
        calls.append(1)
        raise OperationalError(f"falha {len(calls)}")

    with pytest.raises(OperationalError, match="falha 3"):
        func()
    assert len(calls) == 3


def test_retry_redis_connection_error() -> None:
    """redis.ConnectionError também é transiente."""
    from redis.exceptions import ConnectionError as RedisConnectionError

    calls: list[int] = []

    @transient_retry
    def func() -> str:
        calls.append(1)
        if len(calls) < 2:
            raise RedisConnectionError("redis caiu")
        return "ok"

    assert func() == "ok"
    assert len(calls) == 2
