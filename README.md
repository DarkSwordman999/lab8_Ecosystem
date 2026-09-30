# Лабораторная работа №8 — Экосистема Python

[![Python check](https://github.com/DarkSwordman999/lab8_Ecosystem/actions/workflows/python-check.yml/badge.svg)](https://github.com/DarkSwordman999/lab8_Ecosystem/actions/workflows/python-check.yml)

**Фураев Владислав Викторович, группа 221341, вариант 10, лабораторная №8.**

## Цель работы

Познакомиться с инструментами экосистемы Python: управление зависимостями (Poetry), тестирование (pytest), архитектурные шаблоны.

## Задания варианта 10

| Сложность | № | Задание | Реализация |
|---|---|---|---|
| Средняя | 10 | Описать архитектуру MVC для приложения | [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md), `cli.py` / `views.py` / модель |
| Средняя | 2 | Добавить зависимость requests | `pyproject.toml`, `poetry.lock`, `src/booktracker/openlibrary.py` |
| Средняя | 8 | Написать простой модуль с CLI argparse | `src/booktracker/cli.py` |
| Повышенная | 10 | Реализовать слой сервисов + слой данных | `services.py` (`BookService`) + `repositories.py` |
| Повышенная | 3 | Использовать шаблон Repository | `repositories.py` — `BookRepository` и две реализации |

## Приложение

**Booktracker** — консольный учёт прочитанных книг. Книгу можно добавить по ISBN (данные подгружаются из [Open Library](https://openlibrary.org)) или вручную. Для книги ведётся статус «в планах → читаю → прочитана», прочитанным книгам ставится оценка, есть статистика. Данные хранятся в JSON-файле.

```text
src/booktracker/
├── models.py        # Book (dataclass)
├── repositories.py  # Repository: абстракция + InMemory + JSON  ─┐ слой данных
├── openlibrary.py   # клиент Open Library на requests            ─┘
├── services.py      # BookService — бизнес-правила                  слой сервисов
├── views.py         # форматирование вывода                         View
├── cli.py           # argparse, команды                             Controller
└── __main__.py      # python -m booktracker
docs/ARCHITECTURE.md # описание MVC и слоёв
tests/               # 44 теста pytest
```

## Средняя №2. Poetry и зависимость requests

Проект управляется Poetry: `pyproject.toml` (формат PEP 621) и зафиксированный `poetry.lock`.

```bash
poetry add requests                       # так добавлена зависимость
poetry add --group dev pytest flake8      # зависимости для разработки
poetry install
poetry run booktracker --version
```

`requests` используется в `OpenLibraryClient`: запрос `GET https://openlibrary.org/search.json?isbn=...` с таймаутом и заголовком `User-Agent`. Сетевые ошибки, HTTP-ошибки (`raise_for_status`) и ответ не в формате JSON превращаются в понятное исключение `BookInfoError`. Сессия передаётся в конструктор, поэтому в тестах запросы подменяются через `unittest.mock`, без выхода в интернет.

В `[project.scripts]` объявлена команда `booktracker`: после `poetry install` она доступна в окружении.

## Средняя №8. CLI на argparse

- подкоманды через `add_subparsers`: `add`, `list`, `start`, `finish`, `rate`, `remove`, `stats`;
- `add` — взаимоисключающая группа `--isbn` / `--title`;
- проверки типов и значений делает argparse: `type=int`, `choices=range(1, 6)` для оценки, `choices` для статуса;
- общие опции: `--version`, `--db` (или переменная окружения `BOOKTRACKER_DB`);
- ошибки предметной области выводятся в stderr, программа завершается с кодом 1. Функция `main(argv, service)` принимает аргументы и сервис, поэтому её легко тестировать.

## Средняя №10. Архитектура MVC

Подробно — в [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md): схема компонентов, ответственность каждой части, путь одной команды через слои и то, как слои тестируются по отдельности. Кратко:

- **Model** — `models.py`, `services.py`, `repositories.py`, `openlibrary.py`;
- **View** — `views.py` (только форматирование);
- **Controller** — `cli.py` (разбор команды, вызов сервиса, выбор представления).

## Повышенные №10 и №3. Слой сервисов + слой данных, Repository

- **Слой данных.** Абстрактный класс `BookRepository(ABC)` задаёт операции `add/get/list/update/delete/find_by_isbn`. `JsonBookRepository` хранит книги в JSON и пишет атомарно: сначала во временный файл, потом `replace`. `InMemoryBookRepository` используется в тестах.
- **Слой сервисов.** `BookService` получает репозиторий и клиент API через конструктор и содержит все правила: нормализация и проверка ISBN, запрет дубликатов (без лишнего запроса к API), допустимые переходы статуса, оценка 1–5 только прочитанной книге, статистика.
- Ни сервис, ни CLI не знают, как устроено хранение. Тесты репозиториев параметризованы: один и тот же набор проверяет обе реализации, значит они взаимозаменяемы.

## Тесты

```bash
poetry run pytest -v
poetry run flake8 src tests
```

44 теста: `test_repositories.py` (обе реализации), `test_services.py` (правила, фейковый API), `test_openlibrary.py` (`requests` через `Mock`: успех, «не найдено», сетевые и HTTP-ошибки, не-JSON), `test_cli.py` (все команды, stdout/stderr, коды возврата, ошибки argparse). GitHub Actions ставит Poetry, выполняет `poetry install`, flake8, pytest и проверяет команду `booktracker`.

## Пример работы

Реальный запуск с обращением к Open Library:

```text
$ booktracker add --isbn 9780140449136
Добавлено: #1   Преступление и наказание — Fiódor Dostoievski (1866, 520 стр.) [в планах]

$ booktracker add --isbn 978-0-14-303943-3
Добавлено: #2   The Grapes of Wrath — John Steinbeck (1939, 544 стр.) [в планах]

$ booktracker add --title "Мастер и Маргарита" --author "Михаил Булгаков" --pages 480 --year 1967
Добавлено: #3   Мастер и Маргарита — Михаил Булгаков (1967, 480 стр.) [в планах]

$ booktracker start 1
Читаю: #1   Преступление и наказание — Fiódor Dostoievski (1866, 520 стр.) [читаю]

$ booktracker finish 1
Прочитано: #1   Преступление и наказание — Fiódor Dostoievski (1866, 520 стр.) [прочитана]

$ booktracker rate 1 5
Оценено: #1   Преступление и наказание — Fiódor Dostoievski (1866, 520 стр.) [прочитана] ★★★★★

$ booktracker start 2
Читаю: #2   The Grapes of Wrath — John Steinbeck (1939, 544 стр.) [читаю]

$ booktracker list
#1   Преступление и наказание — Fiódor Dostoievski (1866, 520 стр.) [прочитана] ★★★★★
#2   The Grapes of Wrath — John Steinbeck (1939, 544 стр.) [читаю]
#3   Мастер и Маргарита — Михаил Булгаков (1967, 480 стр.) [в планах]

$ booktracker list --status finished
#1   Преступление и наказание — Fiódor Dostoievski (1866, 520 стр.) [прочитана] ★★★★★

$ booktracker rate 3 5
Ошибка: Оценить можно только прочитанную книгу

$ booktracker add --isbn 9780140449136
Ошибка: Книга с ISBN 9780140449136 уже есть в списке

$ booktracker stats
Всего книг:        3
Читаю сейчас:      1
Прочитано:         1
Страниц прочитано: 520
Средняя оценка:    5.0
```

Название и автор первой книги пришли из Open Library в том виде, в каком они есть в каталоге (название — по-русски, имя автора — в латинской транслитерации).
