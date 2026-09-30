import pytest

from booktracker import cli
from booktracker.repositories import JsonBookRepository
from booktracker.services import BookService
from tests.conftest import FakeInfoClient


@pytest.fixture
def run(tmp_path, capsys):
    """Запуск CLI с файлом во временной папке и подменённой Open Library."""
    db = str(tmp_path / "books.json")

    def _run(*argv):
        service = BookService(JsonBookRepository(db), FakeInfoClient())
        code = cli.main(["--db", db, *argv], service=service)
        out, err = capsys.readouterr()
        return code, out.strip(), err.strip()
    return _run


def test_add_manual_and_list(run):
    code, out, _ = run("add", "--title", "Мастер и Маргарита",
                       "--author", "Булгаков", "--pages", "480")
    assert code == 0
    assert out == ("Добавлено: #1   Мастер и Маргарита — Булгаков "
                   "(480 стр.) [в планах]")
    assert run("list")[1].startswith("#1   Мастер и Маргарита")


def test_add_by_isbn(run):
    code, out, _ = run("add", "--isbn", "9780140449136")
    assert code == 0
    assert "Crime and Punishment — Fyodor Dostoyevsky (1866, 671 стр.)" in out


def test_full_flow_and_stats(run):
    run("add", "--title", "Книга", "--author", "Автор", "--pages", "100")
    run("start", "1")
    run("finish", "1")
    code, out, _ = run("rate", "1", "5")
    assert out.endswith("[прочитана] ★★★★★")
    stats = run("stats")[1]
    assert "Прочитано:         1" in stats
    assert "Страниц прочитано: 100" in stats
    assert "Средняя оценка:    5.0" in stats


def test_errors_go_to_stderr_with_code_1(run):
    code, out, err = run("rate", "1", "5")
    assert code == 1 and out == ""
    assert err == "Ошибка: Книга #1 не найдена"
    code, _, err = run("add", "--title", "Без автора")
    assert (code, err) == (1, "Ошибка: Для --title нужен --author")


def test_argparse_validation(run):
    with pytest.raises(SystemExit):
        run("rate", "1", "10")  # choices 1..5
    with pytest.raises(SystemExit):
        run("add", "--isbn", "1", "--title", "X")  # взаимоисключающие
    with pytest.raises(SystemExit):
        run("list", "--status", "lost")


def test_remove_and_empty_list(run):
    run("add", "--title", "A", "--author", "B")
    assert run("remove", "1")[1] == "Книга #1 удалена"
    assert run("list")[1] == "Список пуст"


def test_version(capsys):
    with pytest.raises(SystemExit) as exit_info:
        cli.main(["--version"])
    assert exit_info.value.code == 0
    assert "booktracker 1.0.0" in capsys.readouterr().out
