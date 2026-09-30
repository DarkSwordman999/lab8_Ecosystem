"""Представление (V в MVC): превращает данные в текст для терминала.

Функции ничего не читают и не сохраняют — только форматируют.
"""

STATUS_NAMES = {"planned": "в планах", "reading": "читаю",
                "finished": "прочитана"}


def book_line(book):
    stars = "★" * book.rating if book.rating else ""
    details = ", ".join(str(x) for x in (book.year,
                                         f"{book.pages} стр."
                                         if book.pages else None) if x)
    details = f" ({details})" if details else ""
    return (f"#{book.id:<3} {book.title} — {book.author}{details} "
            f"[{STATUS_NAMES[book.status]}] {stars}").rstrip()


def book_list(books):
    if not books:
        return "Список пуст"
    return "\n".join(book_line(book) for book in books)


def stats(data):
    average = data["average_rating"]
    return "\n".join([
        f"Всего книг:        {data['total']}",
        f"Читаю сейчас:      {data['reading']}",
        f"Прочитано:         {data['finished']}",
        f"Страниц прочитано: {data['pages_read']}",
        f"Средняя оценка:    {average if average is not None else '—'}",
    ])
