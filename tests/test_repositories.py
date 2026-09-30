import json

import pytest

from booktracker.models import Book
from booktracker.repositories import (BookRepository, InMemoryBookRepository,
                                      JsonBookRepository)


@pytest.fixture(params=["memory", "json"])
def repo(request, tmp_path):
    """Одни и те же тесты для обеих реализаций репозитория."""
    if request.param == "memory":
        return InMemoryBookRepository()
    return JsonBookRepository(tmp_path / "books.json")


def test_is_repository(repo):
    assert isinstance(repo, BookRepository)


def test_add_assigns_ids(repo):
    first = repo.add(Book("A", "X"))
    second = repo.add(Book("B", "Y"))
    assert (first.id, second.id) == (1, 2)
    assert [b.title for b in repo.list()] == ["A", "B"]


def test_get_and_missing(repo):
    book = repo.add(Book("A", "X", isbn="123"))
    assert repo.get(book.id).title == "A"
    assert repo.get(99) is None
    assert repo.find_by_isbn("123").id == book.id
    assert repo.find_by_isbn("000") is None


def test_update(repo):
    book = repo.add(Book("A", "X"))
    book.status = "reading"
    repo.update(book)
    assert repo.get(book.id).status == "reading"
    with pytest.raises(KeyError):
        repo.update(Book("Z", "Z", id=42))


def test_delete_and_ids_not_reused(repo):
    book = repo.add(Book("A", "X"))
    assert repo.delete(book.id) is True
    assert repo.delete(book.id) is False
    assert repo.add(Book("B", "Y")).id == 2


def test_json_file_persists_between_instances(tmp_path):
    path = tmp_path / "data" / "books.json"
    JsonBookRepository(path).add(Book("Мастер и Маргарита", "Булгаков"))
    again = JsonBookRepository(path)
    assert again.list()[0].title == "Мастер и Маргарита"
    raw = json.loads(path.read_text(encoding="utf-8"))
    assert raw["next_id"] == 2
    assert "Мастер" in path.read_text(encoding="utf-8")  # не \u-коды


def test_json_missing_file_is_empty(tmp_path):
    assert JsonBookRepository(tmp_path / "none.json").list() == []
