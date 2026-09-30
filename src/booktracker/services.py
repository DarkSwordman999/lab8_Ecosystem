"""Повышенная №10. Слой сервисов (бизнес-логика).

BookService знает правила предметной области и ничего не знает ни о
командной строке, ни о формате хранения: хранилище (BookRepository)
и клиент внешнего API передаются в конструктор (внедрение зависимостей).
"""

from booktracker.models import STATUSES, Book


class ServiceError(Exception):
    """Нарушено правило предметной области."""


def normalize_isbn(isbn):
    digits = isbn.replace("-", "").replace(" ", "").upper()
    if len(digits) not in (10, 13) or not digits[:-1].isdigit():
        raise ServiceError(f"Некорректный ISBN: {isbn}")
    return digits


class BookService:
    def __init__(self, repository, info_client=None):
        self.repository = repository
        self.info_client = info_client

    def _get(self, book_id):
        book = self.repository.get(book_id)
        if book is None:
            raise ServiceError(f"Книга #{book_id} не найдена")
        return book

    def add_manual(self, title, author, pages=None, year=None):
        if not title.strip() or not author.strip():
            raise ServiceError("Название и автор обязательны")
        if pages is not None and pages <= 0:
            raise ServiceError("Число страниц должно быть положительным")
        return self.repository.add(Book(title=title.strip(),
                                        author=author.strip(),
                                        pages=pages, year=year))

    def add_by_isbn(self, isbn):
        isbn = normalize_isbn(isbn)
        if self.repository.find_by_isbn(isbn):
            raise ServiceError(f"Книга с ISBN {isbn} уже есть в списке")
        if self.info_client is None:
            raise ServiceError("Поиск по ISBN недоступен")
        info = self.info_client.find_by_isbn(isbn)
        if info is None:
            raise ServiceError(f"Книга с ISBN {isbn} не найдена")
        return self.repository.add(Book(isbn=isbn, **info))

    def start(self, book_id):
        book = self._get(book_id)
        if book.status == "finished":
            raise ServiceError("Книга уже прочитана")
        book.status = "reading"
        self.repository.update(book)
        return book

    def finish(self, book_id, today=None):
        book = self._get(book_id)
        book.mark_finished(today)
        self.repository.update(book)
        return book

    def rate(self, book_id, rating):
        book = self._get(book_id)
        if book.status != "finished":
            raise ServiceError("Оценить можно только прочитанную книгу")
        if not 1 <= rating <= 5:
            raise ServiceError("Оценка должна быть от 1 до 5")
        book.rating = rating
        self.repository.update(book)
        return book

    def remove(self, book_id):
        if not self.repository.delete(book_id):
            raise ServiceError(f"Книга #{book_id} не найдена")

    def list_books(self, status=None):
        if status is not None and status not in STATUSES:
            raise ServiceError(f"Неизвестный статус: {status}")
        books = self.repository.list()
        if status:
            books = [b for b in books if b.status == status]
        return books

    def stats(self):
        books = self.repository.list()
        finished = [b for b in books if b.status == "finished"]
        rated = [b.rating for b in finished if b.rating]
        return {
            "total": len(books),
            "finished": len(finished),
            "reading": sum(b.status == "reading" for b in books),
            "pages_read": sum(b.pages or 0 for b in finished),
            "average_rating": (round(sum(rated) / len(rated), 2)
                               if rated else None),
        }
