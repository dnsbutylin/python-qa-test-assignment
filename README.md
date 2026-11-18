# Тестовое задание: автотесты Pen

`Pen.py` не менялся. В классе пять дефектов, их должны поймать падающие тесты.
Письменные ответы по бланкам в этот репозиторий не входят: их удобнее отправить отдельным файлом.

Каркас вырос из [back_autotest_pydantic](https://github.com/dnsbutylin/back_autotest_pydantic):
pytest, Allure (`case` / `step`), фикстура на соединение с базой. Отдельные
модели на вход и на ответ убраны. Их заменяет один класс `Contract`
(`src/contract.py`): он валидирует данные ручки и он же описывает контракт
результата, с которым тест сравнивает `Pen`. Клиент Users и PostgreSQL сюда
не переносились: тестируется класс и выборки из условия.

## Запуск

```powershell
python -m venv .venv
.\.venv\Scripts\python -m pip install -r requirements.txt
$env:PYTHONIOENCODING = "utf-8"
.\.venv\Scripts\pytest
```

Если pip останавливается на самоподписанном сертификате прокси, к установке добавляются `--trusted-host pypi.org --trusted-host files.pythonhosted.org`.

Только найденные дефекты:

```powershell
.\.venv\Scripts\pytest -m defect
```

Всё, что в классе сейчас работает как задумано, плюс SQL:

```powershell
.\.venv\Scripts\pytest -m "not defect"
```

Ожидание полного прогона: **13 passed, 5 failed**. Пять падений — это BUG-01…BUG-05, не поломка набора.

## Дефекты Pen

Формула живёт в `Contract.written` и `Contract.ink_after`, а не в каждом тесте.
Если чернил больше нуля, можно записать `floor(чернила / size_letter)` символов.
Списывается стоимость записанного фрагмента, остаток меньше одной буквы сохраняется.

| Тест | Дефект |
| --- | --- |
| `test_get_color_returns_pen_color` | **BUG-01.** `get_color` всегда возвращает `'blue'`, хотя `self.color` хранит переданный цвет. |
| `test_partial_write_length_depends_on_letter_size` | **BUG-02.** При нехватке чернил срез берёт `word[0:ink]`, а не `floor(ink / size_letter)` символов. Ручка отдаёт текст, который стоит дороже остатка. |
| `test_partial_write_leaves_remainder_ink` | **BUG-03.** В той же ветке остаток принудительно становится 0. Для 5 чернил и буквы стоимостью 2 должен остаться 1. |
| `test_partial_write_after_success_does_not_raise` | **BUG-04.** `size_letter` — float, поэтому уже первая успешная запись превращает остаток в float. Следующий частичный срез падает с `TypeError: slice indices must be integers`. |
| `test_init_keeps_fractional_ink` | **BUG-05.** Конструктор делает `int(...)` и отбрасывает дробную часть объёма. Это расходится с дробным расходом чернил. |

Остальные 9 тестов проходят: значения по умолчанию, успешная запись, точная граница, пустое слово, пустая ручка, частичная запись при размере буквы 1 на ещё целом остатке, `check_pen_state`, печать цвета в `do_something_else`.

Эталон ветки нехватки чернил и геттера, без подмены `Pen.py`:

```python
letters = int(self.ink_container_value // self.size_letter)
part = word[:letters]
self.ink_container_value -= len(part) * self.size_letter
return part

def get_color(self):
    return self.color
```

Объём в конструкторе стоит хранить как `float`, а не обрезать через `int`.
