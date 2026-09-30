"""Повышенная №3. Шаблон Repository (слой доступа к данным).

Сервисы работают с абстракцией BookRepository и не знают, где лежат
данные. Реализаций две:
    InMemoryBookRepository — в памяти (для тестов);
    JsonBookRepository     — в JSON-файле (для реальной работы).
Замена хранилища (например, на SQLite) не требует менять сервисы.
"""

import json
from abc import ABC, abstractmethod
from pathlib import Path

from booktracker.models import Book


class BookRepository(ABC):
    @abstractmethod
    def add(self, book):
        """Сохранить новую книгу, присвоить ей id и вернуть её."""

    @abstractmethod
    def get(self, book_id):
        """Книга по id или None."""

    @abstractmethod
    def list(self):
        """Все книги в порядке добавления."""

    @abstractmethod
    def update(self, book):
        """Сохранить изменения существующей книги."""

    @abstractmethod
    def delete(self, book_id):
        """Удалить книгу; True, если она была."""

    def find_by_isbn(self, isbn):
        return next((b for b in self.list() if b.isbn == isbn), None)


class InMemoryBookRepository(BookRepository):
    def __init__(self):
        self._books = {}
        self._next_id = 1

    def add(self, book):
        book.id = self._next_id
        self._next_id += 1
        self._books[book.id] = book
        return book

    def get(self, book_id):
        return self._books.get(book_id)

    def list(self):
        return list(self._books.values())

    def update(self, book):
        if book.id not in self._books:
            raise KeyError(book.id)
        self._books[book.id] = book

    def delete(self, book_id):
        return self._books.pop(book_id, None) is not None


class JsonBookRepository(BookRepository):
    """Хранит книги в JSON-файле. Файл перезаписывается целиком."""

    def __init__(self, path):
        self.path = Path(path)

    def _load(self):
        if not self.path.exists():
            return {"next_id": 1, "books": []}
        with self.path.open(encoding="utf-8") as file:
            return json.load(file)

    def _save(self, data):
        self.path.parent.mkdir(parents=True, exist_ok=True)
        tmp = self.path.with_suffix(".tmp")
        with tmp.open("w", encoding="utf-8") as file:
            json.dump(data, file, ensure_ascii=False, indent=2)
        tmp.replace(self.path)  # атомарная замена: файл не испортится

    def add(self, book):
        data = self._load()
        book.id = data["next_id"]
        data["next_id"] += 1
        data["books"].append(book.to_dict())
        self._save(data)
        return book

    def get(self, book_id):
        return next((b for b in self.list() if b.id == book_id), None)

    def list(self):
        return [Book.from_dict(item) for item in self._load()["books"]]

    def update(self, book):
        data = self._load()
        for index, item in enumerate(data["books"]):
            if item["id"] == book.id:
                data["books"][index] = book.to_dict()
                self._save(data)
                return
        raise KeyError(book.id)

    def delete(self, book_id):
        data = self._load()
        books = [b for b in data["books"] if b["id"] != book_id]
        if len(books) == len(data["books"]):
            return False
        data["books"] = books
        self._save(data)
        return True
