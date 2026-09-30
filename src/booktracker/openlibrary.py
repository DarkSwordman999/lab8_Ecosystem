"""Средняя №2. Внешний сервис через библиотеку requests.

Клиент Open Library (https://openlibrary.org) ищет книгу по ISBN.
Сессия передаётся в конструктор, чтобы в тестах подменить её и не
ходить в интернет.
"""

import requests

SEARCH_URL = "https://openlibrary.org/search.json"
FIELDS = "title,author_name,first_publish_year,number_of_pages_median"


class BookInfoError(Exception):
    """Не удалось получить данные о книге."""


class OpenLibraryClient:
    def __init__(self, session=None, timeout=10):
        self.session = session or requests.Session()
        self.session.headers.setdefault(
            "User-Agent", "booktracker/1.0 (educational project)")
        self.timeout = timeout

    def find_by_isbn(self, isbn):
        """Словарь title/author/year/pages или None, если не найдено."""
        try:
            response = self.session.get(
                SEARCH_URL, params={"isbn": isbn, "fields": FIELDS},
                timeout=self.timeout)
            response.raise_for_status()
            data = response.json()
        except requests.RequestException as error:
            raise BookInfoError(f"Open Library недоступна: {error}") from error
        except ValueError as error:
            raise BookInfoError("Open Library вернула не JSON") from error

        if not data.get("docs"):
            return None
        doc = data["docs"][0]
        return {
            "title": doc.get("title", "Без названия"),
            "author": ", ".join(doc.get("author_name", [])) or "Неизвестен",
            "year": doc.get("first_publish_year"),
            "pages": doc.get("number_of_pages_median"),
        }
