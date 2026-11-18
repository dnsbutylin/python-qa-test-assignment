"""Единственный класс каркаса.

Он сразу делает две вещи, которые раньше расходились по модели и по
проверкам в тестах:

- валидирует вход (чернила, размер буквы, цвет);
- описывает контракт результата: какой текст обязана вернуть ручка,
  сколько чернил останется, готова ли она писать и что печатает.

Отдельной модели «запрос» и отдельной модели «ответ» нет.
Тест создаёт Contract, получает у него и объект Pen, и ожидаемый итог.
"""

from pydantic import BaseModel, ConfigDict, Field

from Pen import Pen


class Contract(BaseModel):
    """Контракт ручки: допустимые данные и ожидаемое поведение."""

    model_config = ConfigDict(extra="forbid")

    ink_container_value: float = Field(default=1000, ge=0)
    size_letter: float = Field(default=1.0, gt=0)
    color: str = Field(default="blue", min_length=1)

    def pen(self) -> Pen:
        """Экземпляр тестируемого класса с уже проверенными полями."""
        return Pen(**self.model_dump())

    def written(self, word: str) -> str:
        """Текст, который ручка обязана вернуть, не меняя этот контракт."""
        ink = self.ink_container_value
        if ink <= 0:
            return ""
        if len(word) * self.size_letter <= ink:
            return word
        letters = int(ink // self.size_letter)
        return word[:letters]

    def ink_after(self, word: str) -> float:
        """Остаток чернил после записи. Хвост меньше одной буквы сохраняется."""
        if self.ink_container_value <= 0:
            return self.ink_container_value
        return self.ink_container_value - len(self.written(word)) * self.size_letter

    def after(self, word: str) -> "Contract":
        """Контракт следующего шага: те же ручка и цвет, новый остаток чернил."""
        return self.model_copy(update={"ink_container_value": self.ink_after(word)})

    def ready(self) -> bool:
        """Ручка может писать, только когда чернил больше нуля."""
        return self.ink_container_value > 0

    def printed(self) -> str:
        """Строка, которую do_something_else обязана отправить в stdout."""
        return f"{self.color}\n"
