"""Pydantic-модели ответов, в том же виде, что UserResponse в каркасе.

Один класс и проверяет данные, и описывает ответ. Отдельной модели
«на создание» нет: generate собирает вход, payload отдаёт его в Pen,
after_write описывает, что ручка обязана вернуть.
"""

from typing import Self, Sequence

from pydantic import BaseModel, ConfigDict, Field

from Pen import Pen


class PenResponse(BaseModel):
    """Ручка: входные данные и ответ методов write / get_color / check_pen_state."""

    model_config = ConfigDict(extra="forbid")

    ink_container_value: float = Field(default=1000, ge=0)
    size_letter: float = Field(default=1.0, gt=0)
    color: str = Field(default="blue", min_length=1)
    text: str = ""

    @classmethod
    def generate(
        cls,
        *,
        ink_container_value: float = 1000,
        size_letter: float = 1.0,
        color: str = "blue",
    ) -> Self:
        """Собрать ответ-ожидание для новой ручки."""
        return cls(
            ink_container_value=ink_container_value,
            size_letter=size_letter,
            color=color,
        )

    def payload(self) -> dict:
        """Аргументы конструктора Pen. Текст ответа в конструктор не входит."""
        return self.model_dump(exclude={"text"})

    def pen(self) -> Pen:
        """Экземпляр тестируемого класса из уже проверенных полей."""
        return Pen(**self.payload())

    def after_write(self, word: str) -> Self:
        """Ответ после write: текст и остаток чернил. Этот объект не меняется."""
        ink = self.ink_container_value
        if ink <= 0:
            return self.model_copy(update={"text": ""})
        if len(word) * self.size_letter <= ink:
            return self.model_copy(
                update={
                    "text": word,
                    "ink_container_value": ink - len(word) * self.size_letter,
                },
            )
        letters = int(ink // self.size_letter)
        text = word[:letters]
        return self.model_copy(
            update={
                "text": text,
                "ink_container_value": ink - len(text) * self.size_letter,
            },
        )

    def ready(self) -> bool:
        """Ручка может писать, только когда чернил больше нуля."""
        return self.ink_container_value > 0

    def printed(self) -> str:
        """Строка, которую do_something_else обязана отправить в stdout."""
        return f"{self.color}\n"


class SubscriberNumberResponse(BaseModel):
    """Текущая пара «абонент — номер»."""

    name: str
    msisdn: str

    @classmethod
    def from_db_tuple(cls, db_tuple: Sequence) -> Self:
        keys = tuple(cls.model_fields)
        return cls.model_validate(dict(zip(keys, db_tuple)))


class OrdinarySubscriberResponse(BaseModel):
    """Абонент с действующим номером типа «Обычный»."""

    subs_id: int
    name: str

    @classmethod
    def from_db_tuple(cls, db_tuple: Sequence) -> Self:
        keys = tuple(cls.model_fields)
        return cls.model_validate(dict(zip(keys, db_tuple)))


class PhoneNumberResponse(BaseModel):
    """Один MSISDN."""

    msisdn: str

    @classmethod
    def from_db_tuple(cls, db_tuple: Sequence) -> Self:
        keys = tuple(cls.model_fields)
        return cls.model_validate(dict(zip(keys, db_tuple)))
