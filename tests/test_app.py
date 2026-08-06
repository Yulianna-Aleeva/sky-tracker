from unittest.mock import MagicMock, patch

import pytest

from app import app


@pytest.fixture
def client():
    """Фикстура веб-клиента Flask для отправки запросов."""
    app.config["TESTING"] = True
    with app.test_client() as client:
        yield client


@patch("app._load_planes")
def test_index_and_planes_routes(mock_load, client):
    """Тест главной страницы и списков самолетов."""
    mock_load.return_value = []

    # 1. Главная страница
    res = client.get("/")
    assert res.status_code == 200

    # 2. Выбор страны из списка
    res = client.post("/planes", data={"country": "Fiji"})
    assert res.status_code == 200

    # 3. Свой ввод страны
    res = client.post("/planes", data={"country": "__custom__", "custom_country": "Germany"})
    assert res.status_code == 200

    # 4. Возврат назад по ссылке
    res = client.get("/planes_back?country=Fiji")
    assert res.status_code == 200


@patch("app._load_planes")
def test_analytics_and_stats_routes(mock_load, client):
    """Тест страниц топов, лидеров и статистики."""
    mock_plane = MagicMock()
    mock_plane.velocity = 200.0
    mock_plane.baro_altitude = 10000.0
    mock_plane.vertical_rate = 10.0
    mock_plane.on_ground = False
    mock_plane.spi = True
    mock_plane.origin_country = "Fiji"

    mock_load.return_value = [mock_plane]

    # 1. Страница лидеров
    res = client.get("/leaders?country=Fiji")
    assert res.status_code == 200

    # 2. Фильтр по стране регистрации
    res = client.get("/filter?country=Fiji&reg=Fiji")
    assert res.status_code == 200

    # 3. Топ по высоте
    res = client.get("/top-altitude?country=Fiji&n=5")
    assert res.status_code == 200

    # 4. Топ по скорости
    res = client.get("/top-velocity?country=Fiji&n=5")
    assert res.status_code == 200

    # 5. Статистика (в воздухе, на земле, спецрейсы)
    for mode in ["in_air", "on_ground", "spi"]:
        res = client.get(f"/stats/{mode}?country=Fiji")
        assert res.status_code == 200


@patch("app.DBManager")
@patch("app.get_db_config")
def test_db_analytics_web_route(mock_config, mock_manager, client):
    """Тест новой веб-страницы аналитики PostgreSQL."""
    mock_config.return_value = {}
    mock_inst = mock_manager.return_value
    mock_inst.get_countries_and_aeroplanes_count.return_value = [("Fiji", 1)]
    mock_inst.get_avg_speed.return_value = 200.0
    mock_inst.get_aeroplanes_with_higher_speed.return_value = []

    res = client.get("/db-analytics")
    assert res.status_code == 200


@patch("app.api.get_aeroplanes")
def test_load_planes_exception(mock_get_api, client):
    """Тест обработки ошибки сети во Flask-приложении."""
    import requests

    # Имитируем сбой сети при запросе к API
    mock_get_api.side_effect = requests.RequestException("API Error")

    # Проверяем, что роут не падает с ошибкой 500, а возвращает 200
    res = client.post("/planes", data={"country": "Germany"})
    assert res.status_code == 200
