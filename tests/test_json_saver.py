import json

import pytest

from src.classes.aeroplane import Aeroplane
from src.storage.JSONSaver import JSONSaver
from tests.test_aeroplane import make_plane


@pytest.fixture
def saver(tmp_path):
    """Создаёт JSONSaver с временным файлом."""
    file_path = tmp_path / "test_planes.json"
    return JSONSaver(file_path=file_path)


def test_init_creates_file(tmp_path):
    """При инициализации создаётся пустой JSON-файл, если его нет."""
    file_path = tmp_path / "new.json"
    JSONSaver(file_path=file_path)
    assert file_path.exists()
    assert json.loads(file_path.read_text(encoding="utf-8")) == []


def test_add_aeroplane(saver):
    """Добавление самолёта в файл."""
    plane = make_plane(icao24="abc123")
    saver.add_aeroplane(plane)
    data = saver._read()
    assert len(data) == 1
    assert data[0]["icao24"] == "abc123"


def test_add_updates_duplicate(saver):
    """Повторный icao24 обновляет запись, не добавляет новую."""
    p1 = make_plane(icao24="abc123", velocity=100.0)
    p2 = make_plane(icao24="abc123", velocity=999.0)
    saver.add_aeroplane(p1)
    saver.add_aeroplane(p2)
    data = saver._read()
    assert len(data) == 1
    assert data[0]["velocity"] == 999.0


def test_add_multiple(saver):
    """Добавление нескольких разных самолётов."""
    for i in range(3):
        saver.add_aeroplane(make_plane(icao24=f"id{i}"))
    assert len(saver._read()) == 3


def test_delete_aeroplane(saver):
    """Удаление самолёта по icao24."""
    saver.add_aeroplane(make_plane(icao24="abc"))
    saver.add_aeroplane(make_plane(icao24="def"))
    saver.delete_aeroplane("abc")
    data = saver._read()
    assert len(data) == 1
    assert data[0]["icao24"] == "def"


def test_delete_nonexistent(saver):
    """Удаление несуществующего icao24 не ломает файл."""
    saver.add_aeroplane(make_plane(icao24="abc"))
    saver.delete_aeroplane("xxx")
    assert len(saver._read()) == 1


def test_get_aeroplanes_no_criteria(saver):
    """Получение всех самолётов без критериев."""
    saver.add_aeroplane(make_plane(icao24="a"))
    saver.add_aeroplane(make_plane(icao24="b"))
    result = saver.get_aeroplanes()
    assert len(result) == 2
    assert all(isinstance(p, Aeroplane) for p in result)


def test_get_aeroplanes_by_criteria(saver):
    """Фильтрация по критериям."""
    saver.add_aeroplane(make_plane(icao24="a", origin_country="Italy"))
    saver.add_aeroplane(make_plane(icao24="b", origin_country="Germany"))
    result = saver.get_aeroplanes(origin_country="Italy")
    assert len(result) == 1
    assert result[0].icao24 == "a"


def test_get_aeroplanes_no_match(saver):
    """Если критерии не совпадают — пустой список."""
    saver.add_aeroplane(make_plane(icao24="a", origin_country="Italy"))
    result = saver.get_aeroplanes(origin_country="China")
    assert result == []


def test_read_corrupted_file(tmp_path):
    """Битый JSON → возвращается пустой список (не падает)."""
    file_path = tmp_path / "bad.json"
    file_path.write_text("{{{not json}}}", encoding="utf-8")
    saver = JSONSaver(file_path=file_path)
    assert saver._read() == []
