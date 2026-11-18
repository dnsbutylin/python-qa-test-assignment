"""Проверка четырёх выборок на данных из задания НПФ «Беркут».

Строка результата читается в Response через from_db_tuple, как в каркасе.
Текущей считается запись истории с датой окончания 31.12.2999.
"""

import sqlite3
from typing import TypeVar

import allure
from pydantic import BaseModel

from src.billing_queries import (
    AIBOLIT_CURRENT_NUMBER,
    AIBOLIT_PREVIOUS_NUMBER,
    CURRENT_SUBSCRIBER_NUMBERS,
    SUBSCRIBERS_WITH_ORDINARY_NUMBER,
)
from src.cases import case, step
from src.models import OrdinarySubscriberResponse, PhoneNumberResponse, SubscriberNumberResponse

ResponseT = TypeVar("ResponseT", bound=BaseModel)


def _responses(
    connection: sqlite3.Connection,
    query: str,
    model: type[ResponseT],
) -> list[ResponseT]:
    rows = [model.from_db_tuple(row) for row in connection.execute(query)]
    return sorted(rows, key=lambda item: tuple(item.model_dump().values()))


@allure.feature("Биллинг. Абоненты и номера")
@case(id=101, title="Имена абонентов и их текущие номера", layer="db")
def test_current_subscriber_numbers(billing_db: sqlite3.Connection) -> None:
    """Открытый период истории. Закрытые номера Петрова и Коржикова в выборку не входят."""
    with step("Выбрать абонентов с действующей привязкой номера"):
        rows = _responses(billing_db, CURRENT_SUBSCRIBER_NUMBERS, SubscriberNumberResponse)
    with step("Сверить три действующие пары имя-номер"):
        assert rows == [
            SubscriberNumberResponse(name="Айболитов Айболит Айболитович", msisdn="9087531425"),
            SubscriberNumberResponse(name="Бармалеев Бармалей Бармалеевич", msisdn="9087416677"),
            SubscriberNumberResponse(name="Иванов Иван Иванович", msisdn="9081594512"),
        ]


@allure.feature("Биллинг. Абоненты и номера")
@case(id=102, title="Абоненты с текущим номером типа Обычный", layer="db")
def test_subscribers_with_ordinary_number(billing_db: sqlite3.Connection) -> None:
    """Бармалеев отсекается: его действующий номер серебряный."""
    with step("Оставить только действующие номера типа Обычный"):
        rows = _responses(billing_db, SUBSCRIBERS_WITH_ORDINARY_NUMBER, OrdinarySubscriberResponse)
    with step("Сверить Иванова и Айболитова"):
        assert rows == [
            OrdinarySubscriberResponse(subs_id=1, name="Иванов Иван Иванович"),
            OrdinarySubscriberResponse(subs_id=3, name="Айболитов Айболит Айболитович"),
        ]


@allure.feature("Биллинг. Абоненты и номера")
@case(id=103, title="Текущий номер Айболитова", layer="db")
def test_aibolit_current_number(billing_db: sqlite3.Connection) -> None:
    """С 21.08.2014 у него номер 9087531425, период открыт до 31.12.2999."""
    with step("Найти открытый период Айболитова"):
        rows = _responses(billing_db, AIBOLIT_CURRENT_NUMBER, PhoneNumberResponse)
    with step("Сверить MSISDN"):
        assert rows == [PhoneNumberResponse(msisdn="9087531425")]


@allure.feature("Биллинг. Абоненты и номера")
@case(id=104, title="Предыдущий номер Айболитова", layer="db")
def test_aibolit_previous_number(billing_db: sqlite3.Connection) -> None:
    """Предыдущий закрытый период: золотой номер 9081112233 до 21.08.2014."""
    with step("Взять закрытый период с максимальной датой окончания"):
        rows = _responses(billing_db, AIBOLIT_PREVIOUS_NUMBER, PhoneNumberResponse)
    with step("Сверить предыдущий MSISDN и убедиться, что это не текущий номер"):
        assert rows == [PhoneNumberResponse(msisdn="9081112233")]
        current = _responses(billing_db, AIBOLIT_CURRENT_NUMBER, PhoneNumberResponse)
        assert rows != current
