"""14 тестов на класс Pen.

Ожидание каждый раз берётся из Contract: тот же объект валидирует вход
и говорит, что ручка обязана вернуть. Пять тестов помечены defect —
они падают на дефектах класса. Pen.py специально не исправлен.
"""

import io
import unittest
from contextlib import redirect_stdout

import allure
import pytest

from src.cases import case, step
from src.contract import Contract


@allure.feature("Pen")
class TestPen(unittest.TestCase):
    """Каждый тест получает свой контракт в setUp и отпускает ручку в tearDown."""

    def setUp(self) -> None:
        self.contract = Contract()
        self.pen = self.contract.pen()

    def tearDown(self) -> None:
        self.pen = None
        self.contract = None

    @case(id=1, title="Ручка по умолчанию готова писать синим")
    def test_init_default_values(self) -> None:
        """Ветки значений по умолчанию: 1000, 1.0, blue, ручка не пустая."""
        contract = self.contract
        pen = self.pen
        with step("Сверить ручку с контрактом по умолчанию"):
            assert pen.ink_container_value == contract.ink_container_value
            assert pen.size_letter == contract.size_letter
            assert pen.color == contract.color
            assert pen.get_color() == contract.color
            assert pen.check_pen_state() is contract.ready()

    @case(id=2, title="Конструктор сохраняет переданные чернила, размер и цвет")
    def test_init_custom_values(self) -> None:
        """Две ручки не делят состояние. Цвет лежит в атрибуте color."""
        with step("Собрать два контракта"):
            red = Contract(ink_container_value=10, size_letter=1.5, color="red")
            green = Contract(ink_container_value=20, size_letter=1, color="green")
            red_pen = red.pen()
            green_pen = green.pen()
        with step("Списать чернила только у первой", word="a"):
            assert red_pen.write("a") == red.written("a")
            assert red_pen.ink_container_value == red.ink_after("a")
        with step("Проверить, что вторая ручка осталась на своём контракте"):
            assert red_pen.color == red.color
            assert red_pen.size_letter == red.size_letter
            assert green_pen.ink_container_value == green.ink_container_value
            assert green_pen.color == green.color
            assert green_pen.check_pen_state() is green.ready()

    @pytest.mark.defect
    @case(id=3, title="Дробный объём чернил не обрезается при создании")
    def test_init_keeps_fractional_ink(self) -> None:
        """BUG-05. int() в конструкторе отрезает дробную часть."""
        with step("Заключить контракт на 10.9 чернил"):
            contract = Contract(ink_container_value=10.9)
            pen = contract.pen()
        with step("Сверить объём ручки с контрактом"):
            assert pen.ink_container_value == contract.ink_container_value, (
                "BUG-05: конструктор делает int(ink_container_value) и теряет дробную часть. "
                f"Контракт требует {contract.ink_container_value}, в ручке {pen.ink_container_value!r}."
            )

    @case(id=4, title="Слово, на которое хватает чернил, пишется целиком")
    def test_write_spends_ink_for_full_word(self) -> None:
        """Успешная ветка write: стоимость = длина * размер буквы."""
        word = "ab"
        with step("Взять контракт, которому хватает на две буквы размера 2"):
            contract = Contract(ink_container_value=10, size_letter=2)
            pen = contract.pen()
        with step("Записать слово и сверить с контрактом", word=word):
            assert pen.write(word) == contract.written(word)
            assert pen.ink_container_value == contract.ink_after(word)
            assert pen.check_pen_state() is contract.after(word).ready()

    @case(id=5, title="Слово ровно по остатку чернил опустошает ручку")
    def test_write_exact_fit_sets_empty_state(self) -> None:
        """Граница size_of_word == ink: слово возвращается, состояние становится пустым."""
        word = "abcd"
        with step("Взять контракт ровно на 4 символа размера 1"):
            contract = Contract(ink_container_value=4, size_letter=1)
            pen = contract.pen()
        with step("Записать слово на весь остаток", word=word):
            assert pen.write(word) == contract.written(word)
            assert pen.ink_container_value == contract.ink_after(word)
            assert pen.check_pen_state() is contract.after(word).ready()

    @case(id=6, title="Пустая строка не расходует чернила")
    def test_write_empty_string_keeps_ink(self) -> None:
        """len('') * size_letter == 0, ручка остаётся рабочей."""
        contract = self.contract
        pen = self.pen
        word = ""
        with step("Записать пустую строку"):
            written = pen.write(word)
        with step("Сверить текст и остаток с контрактом"):
            assert written == contract.written(word)
            assert pen.ink_container_value == contract.ink_after(word)
            assert pen.check_pen_state() is contract.after(word).ready()

    @case(id=7, title="Пустая ручка ничего не пишет")
    def test_write_on_empty_pen_returns_blank(self) -> None:
        """Ветка check_pen_state == False."""
        word = "слово"
        with step("Взять контракт без чернил"):
            contract = Contract(ink_container_value=0)
            pen = contract.pen()
        with step("Попытаться записать слово", word=word):
            assert pen.check_pen_state() is contract.ready()
            assert pen.write(word) == contract.written(word)
            assert pen.ink_container_value == contract.ink_after(word)

    @case(id=8, title="Частичная запись при размере буквы 1 отрезает слово по остатку")
    def test_partial_write_unit_size_on_fresh_pen(self) -> None:
        """Иначе-ветка write на целых чернилах и size_letter = 1 ещё корректна."""
        word = "hello!!"
        with step("Взять свежий контракт на 5 чернил"):
            contract = Contract(ink_container_value=5, size_letter=1)
            pen = contract.pen()
        with step("Записать слово длиннее остатка", word=word):
            assert pen.write(word) == contract.written(word)
            assert pen.ink_container_value == contract.ink_after(word)
            assert pen.check_pen_state() is contract.after(word).ready()

    @pytest.mark.defect
    @case(id=9, title="Длина частичной записи зависит от размера буквы")
    def test_partial_write_length_depends_on_letter_size(self) -> None:
        """BUG-02. Срез берёт ink символов вместо floor(ink / size_letter)."""
        word = "abcdef"
        with step("Взять 5 чернил и букву стоимостью 2"):
            contract = Contract(ink_container_value=5, size_letter=2)
            pen = contract.pen()
        with step("Записать слово длиннее того, на что хватает чернил", word=word):
            written = pen.write(word)
        with step("Сверить фрагмент с контрактом"):
            assert written == contract.written(word), (
                "BUG-02: при нехватке чернил длина фрагмента считается как "
                "floor(чернила / size_letter). "
                f"Контракт требует {contract.written(word)!r}, ручка вернула {written!r}."
            )

    @pytest.mark.defect
    @case(id=10, title="Частичная запись оставляет остаток меньше одной буквы")
    def test_partial_write_leaves_remainder_ink(self) -> None:
        """BUG-03. Ветка нехватки чернил присваивает остатку 0."""
        word = "abcdef"
        with step("Взять 5 чернил и букву стоимостью 2"):
            contract = Contract(ink_container_value=5, size_letter=2)
            pen = contract.pen()
        with step("Записать слово, которое не помещается целиком", word=word):
            pen.write(word)
        with step("Сверить остаток с контрактом"):
            assert pen.ink_container_value == contract.ink_after(word), (
                "BUG-03: после частичной записи должен сохраниться остаток меньше одной буквы. "
                f"Контракт требует {contract.ink_after(word)}, в ручке {pen.ink_container_value!r}, "
                f"check_pen_state={pen.check_pen_state()!r}, по контракту ready={contract.after(word).ready()!r}."
            )

    @pytest.mark.defect
    @case(id=11, title="Повторная запись длинного слова не падает после дробного остатка")
    def test_partial_write_after_success_does_not_raise(self) -> None:
        """BUG-04. Успешная запись превращает чернила в float, срез затем падает."""
        contract = self.contract
        pen = self.pen
        first = "ok"
        with step("Записать короткое слово по контракту", word=first):
            assert pen.write(first) == contract.written(first)
            assert pen.ink_container_value == contract.ink_after(first)
        rest = contract.after(first)
        word = "x" * 2000
        with step("Записать слово длиннее нового остатка", ink=rest.ink_container_value):
            try:
                written = pen.write(word)
            except TypeError as exc:
                pytest.fail(
                    "BUG-04: size_letter имеет тип float, поэтому после первой записи "
                    f"остаток становится float ({pen.ink_container_value!r}). "
                    "Следующая частичная запись делает word[0:остаток] и падает: "
                    f"{exc}. Контракт следующего шага требует префикс длиной "
                    f"{len(rest.written(word))} и остаток {rest.ink_after(word)}."
                )
        with step("Сверить префикс и остаток со вторым контрактом"):
            assert written == rest.written(word)
            assert pen.ink_container_value == rest.ink_after(word)

    @pytest.mark.defect
    @case(id=12, title="get_color возвращает цвет этой ручки")
    def test_get_color_returns_pen_color(self) -> None:
        """BUG-01. get_color зашит на 'blue', хотя self.color хранит переданный цвет."""
        with step("Заключить контракт на красную ручку"):
            contract = Contract(color="red")
            pen = contract.pen()
        with step("Сверить атрибут и get_color с цветом контракта"):
            assert pen.color == contract.color
            assert pen.get_color() == contract.color, (
                "BUG-01: get_color() должен вернуть цвет контракта. "
                f"Контракт и атрибут color={contract.color!r}, метод вернул {pen.get_color()!r}."
            )

    @case(id=13, title="Состояние ручки истинно только при положительном остатке")
    def test_check_pen_state_true_only_with_ink(self) -> None:
        """check_pen_state совпадает с Contract.ready до записи и после неё."""
        with step("Проверить ручку по умолчанию и ручку без чернил"):
            full = Contract()
            empty = Contract(ink_container_value=0)
            assert full.pen().check_pen_state() is full.ready()
            assert empty.pen().check_pen_state() is empty.ready()
        word = "a"
        with step("Списать единственный символ", word=word):
            one = Contract(ink_container_value=1, size_letter=1)
            pen = one.pen()
            assert pen.write(word) == one.written(word)
        with step("Убедиться, что готовность совпала с контрактом после записи"):
            assert pen.check_pen_state() is one.after(word).ready()

    @case(id=14, title="do_something_else печатает цвет ручки")
    def test_do_something_else_prints_color(self) -> None:
        """Метод печатает цвет контракта, а не результат get_color."""
        with step("Заключить контракт на зелёную ручку"):
            contract = Contract(color="green")
            pen = contract.pen()
        with step("Перехватить stdout"):
            output = io.StringIO()
            with redirect_stdout(output):
                pen.do_something_else()
        with step("Сверить вывод с контрактом"):
            assert output.getvalue() == contract.printed()
