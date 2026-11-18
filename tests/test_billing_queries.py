"""Проверка четырёх выборок на данных из задания НПФ «Беркут».

Текущей считается запись истории с датой окончания 31.12.2999.
У Петрова и Коржикова такой записи нет: их номера уже закрыты.
"""

import sqlite3

import allure

from src.billing_queries import (
    AIBOLIT_CURRENT_NUMBER,
    AIBOLIT_PREVIOUS_NUMBER,
    CURRENT_SUBSCRIBER_NUMBERS,
    SUBSCRIBERS_WITH_ORDINARY_NUMBER,
)
from src.cases import case, step


def _rows(connection: sqlite3.Connection, query: str) -> list[tuple]:
    return sorted(connection.execute(query).fetchall())


@allure.feature("Биллинг. Абоненты и номера")
@case(id=101, title="Имена абонентов и их текущие номера", layer="db")
def test_current_subscriber_numbers(billing_db: sqlite3.Connection) -> None:
    """Открытый период истории. Закрытые номера Петрова и Коржикова в выборку не входят."""
    with step("Выбрать абонентов с действующей привязкой номера"):
        rows = _rows(billing_db, CURRENT_SUBSCRIBER_NUMBERS)
    with step("Сверить три действующие пары имя-номер"):
        assert rows == [
            ("Айболитов Айболит Айболитович", "9087531425"),
            ("Бармалеев Бармалей Бармалеевич", "9087416677"),
            ("Иванов Иван Иванович", "9081594512"),
        ]


@allure.feature("Биллинг. Абоненты и номера")
@case(id=102, title="Абоненты с текущим номером типа Обычный", layer="db")
def test_subscribers_with_ordinary_number(billing_db: sqlite3.Connection) -> None:
    """Бармалеев отсекается: его действующий номер серебряный."""
    with step("Оставить только действующие номера типа Обычный"):
        rows = _rows(billing_db, SUBSCRIBERS_WITH_ORDINARY_NUMBER)
    with step("Сверить Иванова и Айболитова"):
        assert rows == [
            (1, "Иванов Иван Иванович"),
            (3, "Айболитов Айболит Айболитович"),
        ]


@allure.feature("Биллинг. Абоненты и номера")
@case(id=103, title="Текущий номер Айболитова", layer="db")
def test_aibolit_current_number(billing_db: sqlite3.Connection) -> None:
    """С 21.08.2014 у него номер 9087531425, период открыт до 31.12.2999."""
    with step("Найти открытый период Айболитова"):
        rows = _rows(billing_db, AIBOLIT_CURRENT_NUMBER)
    with step("Сверить MSISDN"):
        assert rows == [("9087531425",)]


@allure.feature("Биллинг. Абоненты и номера")
@case(id=104, title="Предыдущий номер Айболитова", layer="db")
def test_aibolit_previous_number(billing_db: sqlite3.Connection) -> None:
    """Предыдущий закрытый период: золотой номер 9081112233 до 21.08.2014."""
    with step("Взять закрытый период с максимальной датой окончания"):
        rows = _rows(billing_db, AIBOLIT_PREVIOUS_NUMBER)
    with step("Сверить предыдущий MSISDN и убедиться, что это не текущий номер"):
        assert rows == [("9081112233",)]
        current = _rows(billing_db, AIBOLIT_CURRENT_NUMBER)
        assert rows != current
