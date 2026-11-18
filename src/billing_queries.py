"""Выборки из задания НПФ «Беркут» и данные для их проверки.

Открытый период в выгрузке заканчивается 31.12.2999 — так в биллинге
обычно обозначают «запись действует сейчас». В SQLite та же дата
хранится строкой ISO, чтобы сравнение было точным. В ответе для Oracle
та же логика записана через TO_DATE.
"""

OPEN_PERIOD = "2999-12-31"

SEED_SQL = """
CREATE TABLE subscriber (
    subs_id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    date_bdate TEXT NOT NULL,
    subs_status TEXT NOT NULL
);

CREATE TABLE phone_type (
    phone_type_id INTEGER PRIMARY KEY,
    phone_type TEXT NOT NULL
);

CREATE TABLE phone (
    phone_id INTEGER PRIMARY KEY,
    msisdn TEXT NOT NULL,
    phone_type_id INTEGER NOT NULL,
    status TEXT NOT NULL
);

CREATE TABLE phone_history (
    phone_id INTEGER NOT NULL,
    num_history INTEGER NOT NULL,
    subs_id INTEGER,
    stime TEXT NOT NULL,
    etime TEXT NOT NULL,
    PRIMARY KEY (phone_id, num_history)
);

INSERT INTO subscriber (subs_id, name, date_bdate, subs_status) VALUES
    (1, 'Иванов Иван Иванович', '1988-04-29', 'Активен'),
    (2, 'Петров Петр Петрович', '1967-05-24', 'Приостановлен'),
    (3, 'Айболитов Айболит Айболитович', '1941-07-04', 'Активен'),
    (4, 'Бармалеев Бармалей Бармалеевич', '1988-09-20', 'Заблокирован'),
    (5, 'Коржиков Коржик Коржикович', '1980-04-19', 'Закрыт');

INSERT INTO phone_type (phone_type_id, phone_type) VALUES
    (1, 'Обычный'),
    (2, 'Золотой'),
    (3, 'Серебряный'),
    (4, 'Платиновый');

INSERT INTO phone (phone_id, msisdn, phone_type_id, status) VALUES
    (1, '9081594512', 1, 'Используется'),
    (2, '9087531425', 1, 'Используется'),
    (3, '9087891245', 1, 'Свободен'),
    (4, '9083699865', 1, 'Отстой'),
    (5, '9087416677', 3, 'Используется'),
    (6, '9081112233', 2, 'Свободен');

INSERT INTO phone_history (phone_id, num_history, subs_id, stime, etime) VALUES
    (1, 1, 1, '2013-02-01', '2999-12-31'),
    (2, 1, 2, '2014-04-28', '2014-06-28'),
    (2, 2, NULL, '2014-06-28', '2014-08-21'),
    (2, 3, 3, '2014-08-21', '2999-12-31'),
    (5, 1, 5, '2014-09-23', '2014-12-20'),
    (5, 2, NULL, '2014-12-20', '2015-01-20'),
    (5, 3, 4, '2015-01-20', '2999-12-31'),
    (6, 1, 3, '2014-07-06', '2014-08-21'),
    (6, 2, NULL, '2014-08-21', '2999-12-31');
"""

CURRENT_SUBSCRIBER_NUMBERS = f"""
SELECT s.name, p.msisdn
FROM subscriber s
JOIN phone_history h
    ON h.subs_id = s.subs_id
   AND h.etime = '{OPEN_PERIOD}'
JOIN phone p
    ON p.phone_id = h.phone_id
"""

SUBSCRIBERS_WITH_ORDINARY_NUMBER = f"""
SELECT s.subs_id, s.name
FROM subscriber s
JOIN phone_history h
    ON h.subs_id = s.subs_id
   AND h.etime = '{OPEN_PERIOD}'
JOIN phone p
    ON p.phone_id = h.phone_id
JOIN phone_type t
    ON t.phone_type_id = p.phone_type_id
WHERE t.phone_type = 'Обычный'
"""

AIBOLIT_CURRENT_NUMBER = f"""
SELECT p.msisdn
FROM subscriber s
JOIN phone_history h
    ON h.subs_id = s.subs_id
   AND h.etime = '{OPEN_PERIOD}'
JOIN phone p
    ON p.phone_id = h.phone_id
WHERE s.name = 'Айболитов Айболит Айболитович'
"""

AIBOLIT_PREVIOUS_NUMBER = f"""
SELECT p.msisdn
FROM subscriber s
JOIN phone_history h
    ON h.subs_id = s.subs_id
JOIN phone p
    ON p.phone_id = h.phone_id
WHERE s.name = 'Айболитов Айболит Айболитович'
  AND h.etime = (
      SELECT MAX(h2.etime)
      FROM phone_history h2
      WHERE h2.subs_id = s.subs_id
        AND h2.etime < '{OPEN_PERIOD}'
  )
"""
