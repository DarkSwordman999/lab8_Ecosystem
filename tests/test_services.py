from datetime import date

import pytest

from booktracker.services import ServiceError, normalize_isbn


def test_add_manual(service):
    book = service.add_manual("  Мастер и Маргарита ", "Булгаков", 480)
    assert (book.id, book.title, book.status) == (1, "Мастер и Маргарита",
                                                  "planned")


@pytest.mark.parametrize("title, author, pages", [
    ("", "Автор", None), ("Книга", "  ", None), ("Книга", "Автор", 0)])
def test_add_manual_validation(service, title, author, pages):
    with pytest.raises(ServiceError):
        service.add_manual(title, author, pages)


def test_add_by_isbn_uses_client(service, client):
    book = service.add_by_isbn("978-0-14-044913-6")
    assert book.title == "Crime and Punishment"
    assert book.isbn == "9780140449136"
    assert client.calls == ["9780140449136"]


def test_duplicate_isbn_does_not_call_api(service, client):
    service.add_by_isbn("9780140449136")
    with pytest.raises(ServiceError, match="уже есть"):
        service.add_by_isbn("9780140449136")
    assert len(client.calls) == 1


def test_isbn_not_found(service):
    with pytest.raises(ServiceError, match="не найдена"):
        service.add_by_isbn("9780000000002")


@pytest.mark.parametrize("raw, expected", [
    ("978-0-14-044913-6", "9780140449136"),
    ("0 14 044913 x", "014044913X"),
])
def test_normalize_isbn(raw, expected):
    assert normalize_isbn(raw) == expected


@pytest.mark.parametrize("bad", ["123", "abcdefghij", "97801404491X6"])
def test_bad_isbn(bad):
    with pytest.raises(ServiceError):
        normalize_isbn(bad)


def test_reading_flow(service):
    book = service.add_manual("Книга", "Автор", 100)
    assert service.start(book.id).status == "reading"
    finished = service.finish(book.id, today=date(2026, 12, 1))
    assert (finished.status, finished.finished_on) == ("finished",
                                                       "2026-12-01")
    with pytest.raises(ServiceError):
        service.start(book.id)  # прочитанную нельзя начать заново


def test_rating_rules(service):
    book = service.add_manual("Книга", "Автор")
    with pytest.raises(ServiceError, match="только прочитанную"):
        service.rate(book.id, 5)
    service.finish(book.id)
    with pytest.raises(ServiceError):
        service.rate(book.id, 6)
    assert service.rate(book.id, 4).rating == 4


def test_unknown_book(service):
    for action in (service.start, service.finish, service.remove):
        with pytest.raises(ServiceError, match="#7"):
            action(7)


def test_list_filter(service):
    first = service.add_manual("A", "X")
    service.add_manual("B", "Y")
    service.finish(first.id)
    assert [b.title for b in service.list_books("finished")] == ["A"]
    assert len(service.list_books()) == 2
    with pytest.raises(ServiceError):
        service.list_books("lost")


def test_stats(service):
    a = service.add_manual("A", "X", pages=300)
    b = service.add_manual("B", "Y", pages=200)
    c = service.add_manual("C", "Z", pages=1000)
    service.finish(a.id)
    service.finish(b.id)
    service.rate(a.id, 5)
    service.rate(b.id, 4)
    service.start(c.id)
    assert service.stats() == {"total": 3, "finished": 2, "reading": 1,
                               "pages_read": 500, "average_rating": 4.5}


def test_stats_empty(service):
    assert service.stats()["average_rating"] is None
