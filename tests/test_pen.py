"""14 тестов на класс Pen.

Ожидание каждый раз — PenResponse: тот же класс валидирует вход
и описывает ответ методов. Пять тестов помечены defect: они падают
на дефектах класса. Pen.py специально не исправлен.
"""

import io
import unittest
from contextlib import redirect_stdout

import allure
import pytest

from src.cases import case, step
from src.models import PenResponse


@allure.feature("Pen")
class TestPen(unittest.TestCase):
    """Каждый тест получает свой PenResponse в setUp и отпускает ручку в tearDown."""

    def setUp(self) -> None:
        self.response = PenResponse.generate()
        self.pen = self.response.pen()

    def tearDown(self) -> None:
        self.pen = None
        self.response = None

    @case(id=1, title="Ручка по умолчанию готова писать синим")
    def test_init_default_values(self) -> None:
        """Ветки значений по умолчанию: 1000, 1.0, blue, ручка не пустая."""
        response = self.response
        pen = self.pen
        with step("Сверить ручку с ответом по умолчанию"):
            assert pen.ink_container_value == response.ink_container_value
            assert pen.size_letter == response.size_letter
            assert pen.color == response.color
            assert pen.get_color() == response.color
            assert pen.check_pen_state() is response.ready()

    @case(id=2, title="Конструктор сохраняет переданные чернила, размер и цвет")
    def test_init_custom_values(self) -> None:
        """Две ручки не делят состояние. Цвет лежит в атрибуте color."""
        with step("Собрать два ответа"):
            red = PenResponse.generate(ink_container_value=10, size_letter=1.5, color="red")
            green = PenResponse.generate(ink_container_value=20, size_letter=1, color="green")
            red_pen = red.pen()
            green_pen = green.pen()
        with step("Списать чернила только у первой", word="a"):
            expected = red.after_write("a")
            assert red_pen.write("a") == expected.text
            assert red_pen.ink_container_value == expected.ink_container_value
        with step("Проверить, что вторая ручка осталась на своём ответе"):
            assert red_pen.color == red.color
            assert red_pen.size_letter == red.size_letter
            assert green_pen.ink_container_value == green.ink_container_value
            assert green_pen.color == green.color
            assert green_pen.check_pen_state() is green.ready()

    @pytest.mark.defect
    @case(id=3, title="Дробный объём чернил не обрезается при создании")
    def test_init_keeps_fractional_ink(self) -> None:
        """BUG-05. int() в конструкторе отрезает дробную часть."""
        with step("Собрать ответ на 10.9 чернил"):
            response = PenResponse.generate(ink_container_value=10.9)
            pen = response.pen()
        with step("Сверить объём ручки с ответом"):
            assert pen.ink_container_value == response.ink_container_value, (
                "BUG-05: конструктор делает int(ink_container_value) и теряет дробную часть. "
                f"PenResponse требует {response.ink_container_value}, в ручке {pen.ink_container_value!r}."
            )

    @case(id=4, title="Слово, на которое хватает чернил, пишется целиком")
    def test_write_spends_ink_for_full_word(self) -> None:
        """Успешная ветка write: стоимость = длина * размер буквы."""
        word = "ab"
        with step("Взять ответ, которому хватает на две буквы размера 2"):
            response = PenResponse.generate(ink_container_value=10, size_letter=2)
            pen = response.pen()
            expected = response.after_write(word)
        with step("Записать слово и сверить с ответом", word=word):
            assert pen.write(word) == expected.text
            assert pen.ink_container_value == expected.ink_container_value
            assert pen.check_pen_state() is expected.ready()

    @case(id=5, title="Слово ровно по остатку чернил опустошает ручку")
    def test_write_exact_fit_sets_empty_state(self) -> None:
        """Граница size_of_word == ink: слово возвращается, состояние становится пустым."""
        word = "abcd"
        with step("Взять ответ ровно на 4 символа размера 1"):
            response = PenResponse.generate(ink_container_value=4, size_letter=1)
            pen = response.pen()
            expected = response.after_write(word)
        with step("Записать слово на весь остаток", word=word):
            assert pen.write(word) == expected.text
            assert pen.ink_container_value == expected.ink_container_value
            assert pen.check_pen_state() is expected.ready()

    @case(id=6, title="Пустая строка не расходует чернила")
    def test_write_empty_string_keeps_ink(self) -> None:
        """len('') * size_letter == 0, ручка остаётся рабочей."""
        response = self.response
        pen = self.pen
        word = ""
        expected = response.after_write(word)
        with step("Записать пустую строку"):
            written = pen.write(word)
        with step("Сверить текст и остаток с ответом"):
            assert written == expected.text
            assert pen.ink_container_value == expected.ink_container_value
            assert pen.check_pen_state() is expected.ready()

    @case(id=7, title="Пустая ручка ничего не пишет")
    def test_write_on_empty_pen_returns_blank(self) -> None:
        """Ветка check_pen_state == False."""
        word = "слово"
        with step("Взять ответ без чернил"):
            response = PenResponse.generate(ink_container_value=0)
            pen = response.pen()
            expected = response.after_write(word)
        with step("Попытаться записать слово", word=word):
            assert pen.check_pen_state() is response.ready()
            assert pen.write(word) == expected.text
            assert pen.ink_container_value == expected.ink_container_value

    @case(id=8, title="Частичная запись при размере буквы 1 отрезает слово по остатку")
    def test_partial_write_unit_size_on_fresh_pen(self) -> None:
        """Иначе-ветка write на целых чернилах и size_letter = 1 ещё корректна."""
        word = "hello!!"
        with step("Взять свежий ответ на 5 чернил"):
            response = PenResponse.generate(ink_container_value=5, size_letter=1)
            pen = response.pen()
            expected = response.after_write(word)
        with step("Записать слово длиннее остатка", word=word):
            assert pen.write(word) == expected.text
            assert pen.ink_container_value == expected.ink_container_value
            assert pen.check_pen_state() is expected.ready()

    @pytest.mark.defect
    @case(id=9, title="Длина частичной записи зависит от размера буквы")
    def test_partial_write_length_depends_on_letter_size(self) -> None:
        """BUG-02. Срез берёт ink символов вместо floor(ink / size_letter)."""
        word = "abcdef"
        with step("Взять 5 чернил и букву стоимостью 2"):
            response = PenResponse.generate(ink_container_value=5, size_letter=2)
            pen = response.pen()
            expected = response.after_write(word)
        with step("Записать слово длиннее того, на что хватает чернил", word=word):
            written = pen.write(word)
        with step("Сверить фрагмент с ответом"):
            assert written == expected.text, (
                "BUG-02: при нехватке чернил длина фрагмента считается как "
                "floor(чернила / size_letter). "
                f"PenResponse требует {expected.text!r}, ручка вернула {written!r}."
            )

    @pytest.mark.defect
    @case(id=10, title="Частичная запись оставляет остаток меньше одной буквы")
    def test_partial_write_leaves_remainder_ink(self) -> None:
        """BUG-03. Ветка нехватки чернил присваивает остатку 0."""
        word = "abcdef"
        with step("Взять 5 чернил и букву стоимостью 2"):
            response = PenResponse.generate(ink_container_value=5, size_letter=2)
            pen = response.pen()
            expected = response.after_write(word)
        with step("Записать слово, которое не помещается целиком", word=word):
            pen.write(word)
        with step("Сверить остаток с ответом"):
            assert pen.ink_container_value == expected.ink_container_value, (
                "BUG-03: после частичной записи должен сохраниться остаток меньше одной буквы. "
                f"PenResponse требует {expected.ink_container_value}, в ручке {pen.ink_container_value!r}, "
                f"check_pen_state={pen.check_pen_state()!r}, по ответу ready={expected.ready()!r}."
            )

    @pytest.mark.defect
    @case(id=11, title="Повторная запись длинного слова не падает после дробного остатка")
    def test_partial_write_after_success_does_not_raise(self) -> None:
        """BUG-04. Успешная запись превращает чернила в float, срез затем падает."""
        response = self.response
        pen = self.pen
        first = "ok"
        with step("Записать короткое слово по ответу", word=first):
            expected_first = response.after_write(first)
            assert pen.write(first) == expected_first.text
            assert pen.ink_container_value == expected_first.ink_container_value
        word = "x" * 2000
        expected = expected_first.after_write(word)
        with step("Записать слово длиннее нового остатка", ink=expected_first.ink_container_value):
            try:
                written = pen.write(word)
            except TypeError as exc:
                pytest.fail(
                    "BUG-04: size_letter имеет тип float, поэтому после первой записи "
                    f"остаток становится float ({pen.ink_container_value!r}). "
                    "Следующая частичная запись делает word[0:остаток] и падает: "
                    f"{exc}. PenResponse следующего шага требует префикс длиной "
                    f"{len(expected.text)} и остаток {expected.ink_container_value}."
                )
        with step("Сверить префикс и остаток со вторым ответом"):
            assert written == expected.text
            assert pen.ink_container_value == expected.ink_container_value

    @pytest.mark.defect
    @case(id=12, title="get_color возвращает цвет этой ручки")
    def test_get_color_returns_pen_color(self) -> None:
        """BUG-01. get_color зашит на 'blue', хотя self.color хранит переданный цвет."""
        with step("Собрать ответ на красную ручку"):
            response = PenResponse.generate(color="red")
            pen = response.pen()
        with step("Сверить атрибут и get_color с цветом ответа"):
            assert pen.color == response.color
            assert pen.get_color() == response.color, (
                "BUG-01: get_color() должен вернуть цвет из PenResponse. "
                f"Ответ и атрибут color={response.color!r}, метод вернул {pen.get_color()!r}."
            )

    @case(id=13, title="Состояние ручки истинно только при положительном остатке")
    def test_check_pen_state_true_only_with_ink(self) -> None:
        """check_pen_state совпадает с PenResponse.ready до записи и после неё."""
        with step("Проверить ручку по умолчанию и ручку без чернил"):
            full = PenResponse.generate()
            empty = PenResponse.generate(ink_container_value=0)
            assert full.pen().check_pen_state() is full.ready()
            assert empty.pen().check_pen_state() is empty.ready()
        word = "a"
        with step("Списать единственный символ", word=word):
            one = PenResponse.generate(ink_container_value=1, size_letter=1)
            pen = one.pen()
            expected = one.after_write(word)
            assert pen.write(word) == expected.text
        with step("Убедиться, что готовность совпала с ответом после записи"):
            assert pen.check_pen_state() is expected.ready()

    @case(id=14, title="do_something_else печатает цвет ручки")
    def test_do_something_else_prints_color(self) -> None:
        """Метод печатает цвет ответа, а не результат get_color."""
        with step("Собрать ответ на зелёную ручку"):
            response = PenResponse.generate(color="green")
            pen = response.pen()
        with step("Перехватить stdout"):
            output = io.StringIO()
            with redirect_stdout(output):
                pen.do_something_else()
        with step("Сверить вывод с ответом"):
            assert output.getvalue() == response.printed()
