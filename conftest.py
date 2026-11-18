"""Общие фикстуры прогона."""

import sqlite3
from collections.abc import Iterator
from pathlib import Path

import pytest

from src.billing_queries import SEED_SQL

PROJECT_ROOT = Path(__file__).parent
ALLURE_RESULTS_DIR = PROJECT_ROOT / "allure-results"


@pytest.hookimpl(tryfirst=True)
def pytest_configure(config: pytest.Config) -> None:
    """Кладёт allure-results в корень проекта, откуда бы ни запустили pytest."""
    ALLURE_RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    config.option.allure_report_dir = str(ALLURE_RESULTS_DIR)


@pytest.fixture(scope="module")
def billing_db() -> Iterator[sqlite3.Connection]:
    """Память SQLite с таблицами и строками из задания по биллингу."""
    connection = sqlite3.connect(":memory:")
    connection.executescript(SEED_SQL)
    yield connection
    connection.close()
