from unittest.mock import MagicMock, patch

import pytest

from src.classes.db_manager import DBManager
from src.storage.DBSaver import DBSaver


@pytest.fixture
def mock_cursor():
    """Фикстура для создания поддельного курсора БД."""
    return MagicMock()


@pytest.fixture
def db_manager():
    """Фикстура для создания менеджера БД."""
    return DBManager({"host": "localhost", "dbname": "test"})


def test_create_tables(mock_cursor):
    """Тест создания таблиц."""
    saver = DBSaver(mock_cursor)
    saver.create_tables()
    assert mock_cursor.execute.call_count == 2


@patch("requests.get")
@patch("src.storage.DBSaver.USER_SETTINGS")
def test_populate_countries(mock_settings, mock_get, mock_cursor):
    """Тест заполнения стран координатами."""
    mock_settings.get.side_effect = lambda key, default=None: {
        "user_countries": ["Fiji"],
        "country_coordinates": {"Fiji": [-18.3, -17.2, 177.2, 178.8]},
    }.get(key, default)

    saver = DBSaver(mock_cursor)
    saver.populate_countries()
    mock_cursor.execute.assert_called_once()


@patch("requests.get")
@patch("src.storage.DBSaver.USER_SETTINGS")
def test_update_aeroplanes_online(mock_settings, mock_get, mock_cursor):
    """Тест обновления самолетов из API."""
    mock_settings.get.return_value = "http://test"
    mock_get.return_value.json.return_value = {
        "states": [["icao1", "AFL123 ", "Russia", 0, 0, 0, 0, 0, 250.0, 0, 0, False]]
    }
    mock_cursor.fetchall.return_value = [("Russia", 1)]

    saver = DBSaver(mock_cursor)
    saver.update_aeroplanes_online()
    assert mock_cursor.execute.call_count == 3


@patch("psycopg2.connect")
def test_get_countries_count(mock_connect, db_manager):
    """Тест подсчета самолетов по странам."""
    mock_ctx = mock_connect.return_value.__enter__.return_value
    mock_fetchall = mock_ctx.cursor.return_value.__enter__.return_value.fetchall
    mock_fetchall.return_value = [("Fiji", 5)]
    res = db_manager.get_countries_and_aeroplanes_count()
    assert res == [("Fiji", 5)]


@patch("psycopg2.connect")
def test_get_all_aeroplanes(mock_connect, db_manager):
    """Тест получения всех самолетов."""
    mock_ctx = mock_connect.return_value.__enter__.return_value
    mock_fetchall = mock_ctx.cursor.return_value.__enter__.return_value.fetchall
    mock_fetchall.return_value = [("icao1", "AFL", 200)]
    res = db_manager.get_all_aeroplanes()
    assert len(res) == 1


@patch("psycopg2.connect")
def test_get_avg_speed(mock_connect, db_manager):
    """Тест вычисления средней скорости."""
    mock_cur = mock_connect.return_value.__enter__.return_value.cursor.return_value.__enter__.return_value
    mock_cur.fetchone.return_value = (250.0,)
    assert db_manager.get_avg_speed() == 250.0

    mock_cur.fetchone.return_value = None
    assert db_manager.get_avg_speed() == 0.0


@patch("psycopg2.connect")
def test_get_higher_speed(mock_connect, db_manager):
    """Тест фильтра скорости выше средней."""
    mock_ctx = mock_connect.return_value.__enter__.return_value
    mock_fetchall = mock_ctx.cursor.return_value.__enter__.return_value.fetchall
    mock_fetchall.return_value = []
    assert db_manager.get_aeroplanes_with_higher_speed() == []


@patch("psycopg2.connect")
def test_get_with_keyword(mock_connect, db_manager):
    """Тест поиска по ключевому слову."""
    mock_ctx = mock_connect.return_value.__enter__.return_value
    mock_fetchall = mock_ctx.cursor.return_value.__enter__.return_value.fetchall
    mock_fetchall.return_value = []
    assert db_manager.get_aeroplanes_with_keyword("TEST") == []


@patch("sys.argv", ["main.py"])
def test_logger_main_branch():
    """Тест системной ветки логгера для 100% покрытия config.py."""
    from src.config import get_logger

    logger = get_logger("__main__")
    assert logger is not None


def test_action_load_planes_minus_flag():
    """Тест перехвата кнопки '-' для 100% покрытия actions.py."""
    from src.interaction.actions import action_load_planes

    filters = {}
    with patch("builtins.input", return_value="-"):
        res = action_load_planes(filters)
        assert res == []
        assert filters["db_analytics"] is True


@patch("configparser.ConfigParser.read")
@patch("configparser.ConfigParser.has_section")
@patch("configparser.ConfigParser.items")
def test_get_db_config_success(mock_items, mock_has, mock_read):
    """Тест успешного чтения конфигурации базы данных."""
    from src.config import get_db_config

    mock_has.return_value = True
    mock_items.return_value = [("user", "postgres"), ("password", "123")]

    res = get_db_config()
    assert res == {"user": "postgres", "password": "123"}


@patch("configparser.ConfigParser.has_section")
def test_get_db_config_exception(mock_has):
    """Тест генерации ошибки при отсутствии секции в конфиге."""
    from src.config import get_db_config

    mock_has.return_value = False

    with pytest.raises(Exception):
        get_db_config()
