from unittest import mock

import pytest
import requests

from booktracker.openlibrary import (SEARCH_URL, BookInfoError,
                                     OpenLibraryClient)


def fake_session(json_data=None, error=None, status=200):
    session = mock.Mock()
    session.headers = {}
    response = mock.Mock()
    response.json.return_value = json_data
    if status >= 400:
        response.raise_for_status.side_effect = requests.HTTPError(
            f"{status} error")
    session.get.return_value = response
    if error:
        session.get.side_effect = error
    return session


def test_found():
    session = fake_session({"numFound": 1, "docs": [{
        "title": "Crime and Punishment",
        "author_name": ["Fyodor Dostoyevsky"],
        "first_publish_year": 1866,
        "number_of_pages_median": 671}]})
    info = OpenLibraryClient(session).find_by_isbn("9780140449136")
    assert info == {"title": "Crime and Punishment",
                    "author": "Fyodor Dostoyevsky", "year": 1866,
                    "pages": 671}
    args, kwargs = session.get.call_args
    assert args == (SEARCH_URL,)
    assert kwargs["params"]["isbn"] == "9780140449136"
    assert kwargs["timeout"] == 10
    assert "booktracker" in session.headers["User-Agent"]


def test_missing_fields_have_defaults():
    session = fake_session({"docs": [{}]})
    info = OpenLibraryClient(session).find_by_isbn("1")
    assert info == {"title": "Без названия", "author": "Неизвестен",
                    "year": None, "pages": None}


def test_not_found():
    session = fake_session({"numFound": 0, "docs": []})
    assert OpenLibraryClient(session).find_by_isbn("1") is None


@pytest.mark.parametrize("session", [
    fake_session(error=requests.ConnectionError("нет сети")),
    fake_session(error=requests.Timeout("долго")),
    fake_session(status=503),
])
def test_network_errors(session):
    with pytest.raises(BookInfoError):
        OpenLibraryClient(session).find_by_isbn("1")


def test_not_json():
    session = fake_session()
    session.get.return_value.json.side_effect = ValueError("html")
    with pytest.raises(BookInfoError, match="не JSON"):
        OpenLibraryClient(session).find_by_isbn("1")
