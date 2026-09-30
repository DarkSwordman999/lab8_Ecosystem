"""Средняя №8. Модуль с CLI на argparse (контроллер, C в MVC).

Разбирает аргументы, вызывает сервис и передаёт результат
представлению. Примеры:
    booktracker add --isbn 9780140449136
    booktracker add --title "Мастер и Маргарита" --author Булгаков
    booktracker list --status finished
    booktracker finish 1
    booktracker rate 1 5
    booktracker stats
"""

import argparse
import os
import sys

from booktracker import __version__, views
from booktracker.models import STATUSES
from booktracker.openlibrary import BookInfoError, OpenLibraryClient
from booktracker.repositories import JsonBookRepository
from booktracker.services import BookService, ServiceError

DEFAULT_DB = os.path.join(os.path.expanduser("~"), ".booktracker.json")


def build_parser():
    parser = argparse.ArgumentParser(
        prog="booktracker", description="Учёт прочитанных книг")
    parser.add_argument("--version", action="version",
                        version=f"%(prog)s {__version__}")
    parser.add_argument("--db", default=os.environ.get("BOOKTRACKER_DB",
                                                       DEFAULT_DB),
                        help="JSON-файл с книгами (по умолчанию %(default)s)")
    sub = parser.add_subparsers(dest="command", required=True,
                                metavar="КОМАНДА")

    add = sub.add_parser("add", help="добавить книгу")
    source = add.add_mutually_exclusive_group(required=True)
    source.add_argument("--isbn", help="найти данные в Open Library")
    source.add_argument("--title", help="название (ввод вручную)")
    add.add_argument("--author", help="автор (с --title)")
    add.add_argument("--pages", type=int, help="число страниц")
    add.add_argument("--year", type=int, help="год издания")

    lst = sub.add_parser("list", help="показать книги")
    lst.add_argument("--status", choices=STATUSES)

    for name, text in [("start", "начать читать"),
                       ("finish", "отметить прочитанной"),
                       ("remove", "удалить книгу")]:
        cmd = sub.add_parser(name, help=text)
        cmd.add_argument("id", type=int)

    rate = sub.add_parser("rate", help="оценить прочитанную книгу")
    rate.add_argument("id", type=int)
    rate.add_argument("rating", type=int, choices=range(1, 6),
                      metavar="{1..5}")

    sub.add_parser("stats", help="статистика чтения")
    return parser


def run(args, service):
    """Выполнить команду и вернуть текст для вывода."""
    if args.command == "add":
        if args.isbn:
            book = service.add_by_isbn(args.isbn)
        else:
            if not args.author:
                raise ServiceError("Для --title нужен --author")
            book = service.add_manual(args.title, args.author,
                                      args.pages, args.year)
        return "Добавлено: " + views.book_line(book)
    if args.command == "list":
        return views.book_list(service.list_books(args.status))
    if args.command == "start":
        return "Читаю: " + views.book_line(service.start(args.id))
    if args.command == "finish":
        return "Прочитано: " + views.book_line(service.finish(args.id))
    if args.command == "rate":
        return "Оценено: " + views.book_line(service.rate(args.id,
                                                          args.rating))
    if args.command == "remove":
        service.remove(args.id)
        return f"Книга #{args.id} удалена"
    return views.stats(service.stats())


def main(argv=None, service=None):
    args = build_parser().parse_args(argv)
    if service is None:
        service = BookService(JsonBookRepository(args.db),
                              OpenLibraryClient())
    try:
        print(run(args, service))
    except (ServiceError, BookInfoError) as error:
        print(f"Ошибка: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
