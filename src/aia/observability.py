"""Helpers opcionais de observabilidade com LangSmith."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any, TypeVar


F = TypeVar("F", bound=Callable[..., Any])

try:
    from langsmith import traceable as _langsmith_traceable
    from langsmith.wrappers import wrap_openai as _langsmith_wrap_openai
except ImportError:  # pragma: no cover
    _langsmith_traceable = None
    _langsmith_wrap_openai = None


def traceable(*args: Any, **kwargs: Any) -> Callable[[F], F]:
    """Retorna o decorator do LangSmith ou um no-op quando ele nao esta instalado."""
    if _langsmith_traceable is None:
        return _noop_decorator
    return _langsmith_traceable(*args, **kwargs)


def wrap_openai_client(client: Any) -> Any:
    """Instrumenta clientes OpenAI quando o LangSmith esta disponivel."""
    if _langsmith_wrap_openai is None:
        return client
    return _langsmith_wrap_openai(client)


def drop_self(inputs: dict[str, Any]) -> dict[str, Any]:
    """Remove a instancia de metodos para manter traces menores e serializaveis."""
    data = dict(inputs)
    data.pop("self", None)
    return data


def _noop_decorator(func: F) -> F:
    return func
