"""Шаги и карточки тестов в Allure.

Тот же приём, что в каркасе back_autotest_pydantic: декоратор case
и контекстный менеджер step. Слой задаётся явно, потому что здесь
есть и модульные тесты Pen, и проверки SQL.
"""

from contextlib import nullcontext
from typing import Any

import allure
from allure_commons._allure import StepContext


def _parameters(**kwargs: Any) -> dict[str, str]:
    """Приводит аргументы шага к строкам для отчёта Allure."""
    return {str(key): str(value) for key, value in kwargs.items()}


def step(
    _title: str | None,
    _params: dict[Any, Any] | None = None,
    _empty: bool = False,
    **kwargs: Any,
) -> StepContext | nullcontext:
    """Контекстный менеджер шага.

    Пустой заголовок или _empty=True не попадает в отчёт.
    """
    if _empty or _title is None:
        return nullcontext()
    params = _parameters(**(_params or {}), **kwargs)
    return StepContext(title=_title, params=params)


def case(*, id: int, title: str, layer: str = "unit") -> Any:  # noqa: A002
    """Вешает на тест id, название, слой и docstring как description."""

    def _wrap(func: Any) -> Any:
        func = allure.id(str(id))(func)
        func = allure.title(title)(func)
        func = allure.label("layer", layer)(func)
        if func.__doc__:
            func = allure.description(func.__doc__)(func)
        return func

    return _wrap


__all__ = ["case", "step"]
