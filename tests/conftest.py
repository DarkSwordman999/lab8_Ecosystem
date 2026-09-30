import pytest

from booktracker.repositories import InMemoryBookRepository
from booktracker.services import BookService

BOOKS = {
    "9780140449136": {"title": "Crime and Punishment",
                      "author": "Fyodor Dostoyevsky", "year": 1866,
                      "pages": 671},
}


class FakeInfoClient:
    """Подменяет Open Library: отвечает из словаря, считает запросы."""

    def __init__(self, books=None):
        self.books = BOOKS if books is None else books
        self.calls = []

    def find_by_isbn(self, isbn):
        self.calls.append(isbn)
        info = self.books.get(isbn)
        return dict(info) if info else None


@pytest.fixture
def client():
    return FakeInfoClient()


@pytest.fixture
def service(client):
    return BookService(InMemoryBookRepository(), client)
