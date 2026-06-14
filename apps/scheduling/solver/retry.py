"""Wrapper de retry transiente (SDD §22.2.5).

Aplica 1 retry transparente (sem backoff) em exceções
transientes conhecidas. Total máximo: 2 tentativas.

Transientes (retry 1x):
- django.db.utils.OperationalError
- django.db.utils.InterfaceError
- redis.exceptions.ConnectionError
- celery.exceptions.TimeoutError

Não-transientes (propaga, sem retry):
- MemoryError, ValueError, TypeError, KeyError, AttributeError
- SolverError, UnsatisfiableError
- KeyboardInterrupt, SystemExit

Retry é AUTOMÁTICO e SILENCIOSO pro usuário — se a 2ª tentativa
funcionar, ele recebe o resultado normal. Se as 2 falharem, vê
a mensagem de erro.
"""
from __future__ import annotations

import functools
import logging
from collections.abc import Callable
from typing import Any

logger = logging.getLogger(__name__)

# Importações lazy pra evitar import-time errors quando o wrapper
# é usado em contextos sem Django/Celery (ex: testes unitários do
# solver puro).
def _transient_exceptions() -> tuple[type[BaseException], ...]:
    from django.db.utils import InterfaceError, OperationalError  # type: ignore
    from redis.exceptions import ConnectionError as RedisConnectionError  # type: ignore

    extras: list[type[BaseException]] = []
    try:
        from celery.exceptions import TimeoutError as CeleryTimeoutError  # type: ignore

        extras.append(CeleryTimeoutError)
    except ImportError:
        pass

    return (OperationalError, InterfaceError, RedisConnectionError, *extras)


def transient_retry(
    func: Callable[..., Any] | None = None,
    *,
    max_attempts: int = 2,
) -> Callable[..., Any]:
    """Decorator que aplica retry transiente.

    Uso:
        @transient_retry
        def minha_task(...): ...

        @transient_retry(max_attempts=3)
        def minha_task_custom(...): ...
    """
    def decorator(f: Callable[..., Any]) -> Callable[..., Any]:
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
            # Nunca chega aqui, mas pra satisfazer o type-checker
            assert last_exc is not None
            raise last_exc
        return wrapper

    if func is not None and callable(func):
        return decorator(func)
    return decorator
