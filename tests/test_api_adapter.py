from typing import Any
from unittest.mock import Mock, patch

import pytest
import requests

from src.api.api_adapter import ApiAdapter


@pytest.fixture
def api() -> ApiAdapter:
    """Экземпляр ApiAdapter для тестов."""
    return ApiAdapter()


def make_response(json_data: Any, status: int = 200) -> Mock:
    """Фабрика мок-ответа requests."""
    resp = Mock()
    resp.json.return_value = json_data
    resp.status_code = status
    resp.raise_for_status = Mock()
    return resp


@pytest.mark.parametrize(
    "value, expected",
    [
        (["1", "2", "3", "4"], [1.0, 2.0, 3.0, 4.0]),
        ([1, 2, 3, 4], [1.0, 2.0, 3.0, 4.0]),
        ([1, 2, 3], None),
        ("not a list", None),
        (["a", "b", "c", "d"], None),
        (None, None),
    ],
)
def test_to_bbox(api: ApiAdapter, value: Any, expected: list[float] | None) -> None:
    """Приведение bounding box к списку float."""
    assert api._to_bbox(value) == expected


@patch("src.api.api_adapter.requests.get")
def test_get_coordinates_success(mock_get: Mock, api: ApiAdapter) -> None:
    """Успешное получение координат из Nominatim."""
    mock_get.return_value = make_response([{"boundingbox": ["1", "2", "3", "4"]}])
    assert api._get_coordinates("Testland") == [1.0, 2.0, 3.0, 4.0]


@patch("src.api.api_adapter.requests.get")
def test_get_coordinates_empty_response_uses_fallback(mock_get: Mock, api: ApiAdapter) -> None:
    """Если Nominatim вернул [], используются сохранённые координаты."""
    mock_get.return_value = make_response([])
    with patch.object(api, "_get_saved_coords", return_value=[10.0, 20.0, 30.0, 40.0]):
        assert api._get_coordinates("Unknown") == [10.0, 20.0, 30.0, 40.0]


@patch("src.api.api_adapter.requests.get")
def test_get_coordinates_network_error_uses_fallback(mock_get: Mock, api: ApiAdapter) -> None:
    """При сетевой ошибке используются сохранённые координаты."""
    mock_get.side_effect = requests.RequestException("timeout")
    with patch.object(api, "_get_saved_coords", return_value=[1.0, 2.0, 3.0, 4.0]):
        assert api._get_coordinates("X") == [1.0, 2.0, 3.0, 4.0]


def test_get_coordinates_empty_geo_url(api: ApiAdapter) -> None:
    """Проверяем поведение при пустом geo_url."""
    api.geo_url = ""
    country = "Italy"
    with patch.object(api, "_get_saved_coords") as mock_saved:
        mock_saved.return_value = [1.0, 2.0, 3.0, 4.0]
        assert api._get_coordinates(country) == [1.0, 2.0, 3.0, 4.0]
        mock_saved.assert_called_once_with(country)


@patch("src.api.api_adapter.requests.get")
def test_get_coordinates_invalid_bbox_uses_fallback(mock_get: Mock, api: ApiAdapter) -> None:
    """Если boundingbox некорректный (мало данных или не список), берём сохранённые."""
    # Передаём 2 координаты
    mock_get.return_value = make_response([{"boundingbox": ["1", "2"]}])
    with patch.object(api, "_get_saved_coords", return_value=[10.0, 20.0, 30.0, 40.0]):
        assert api._get_coordinates("BadBbox") == [10.0, 20.0, 30.0, 40.0]

    # Передаём без boundingbox
    mock_get.return_value = make_response([{"other_data": "yes"}])
    with patch.object(api, "_get_saved_coords", return_value=[1.0, 2.0, 3.0, 4.0]):
        assert api._get_coordinates("NoBbox") == [1.0, 2.0, 3.0, 4.0]


@patch("src.api.api_adapter.requests.get")
def test_get_aeroplanes_success(mock_get: Mock, api: ApiAdapter) -> None:
    """Успешное получение самолётов."""
    fake_state = ["abc", "TEST", "Italy"] + [None] * 14
    mock_get.side_effect = [
        make_response([{"boundingbox": ["1", "2", "3", "4"]}]),  # geo
        make_response({"states": [fake_state]}),  # sky
    ]
    assert api.get_aeroplanes("Testland") == [fake_state]


@patch("src.api.api_adapter.requests.get")
def test_get_aeroplanes_no_coords_returns_none(mock_get: Mock, api: ApiAdapter) -> None:
    """Если координаты не получены → None."""
    mock_get.return_value = make_response([])
    with patch.object(api, "_get_saved_coords", return_value=None):
        assert api.get_aeroplanes("Nowhere") is None


@patch("src.api.api_adapter.requests.get")
def test_get_aeroplanes_empty_sky_returns_empty_list(mock_get: Mock, api: ApiAdapter) -> None:
    """Если API вернуло states=None → пустой список."""
    mock_get.side_effect = [
        make_response([{"boundingbox": ["1", "2", "3", "4"]}]),
        make_response({"states": None}),
    ]
    assert api.get_aeroplanes("Testland") == []


@patch("src.api.api_adapter.requests.get")
def test_get_aeroplanes_bad_response_returns_none(mock_get: Mock, api: ApiAdapter) -> None:
    """Если ответ OpenSky не dict → None."""
    mock_get.side_effect = [
        make_response([{"boundingbox": ["1", "2", "3", "4"]}]),
        make_response("bad data"),
    ]
    assert api.get_aeroplanes("Testland") is None


@patch("src.api.api_adapter.requests.get")
def test_get_aeroplanes_network_error_raises(mock_get: Mock, api: ApiAdapter) -> None:
    """Если ошибка сети у OpenSky → пробрасывается RequestException после 3 попыток (retry)."""
    # Мокаем _get_coordinates, чтобы не тратить моки requests.get на geo
    with patch.object(api, "_get_coordinates", return_value=[1.0, 2.0, 3.0, 4.0]):
        mock_get.side_effect = requests.RequestException("timeout")
        with pytest.raises(requests.RequestException):
            api.get_aeroplanes("Testland")
    # Проверяем, что было 3 попытки
    assert mock_get.call_count == 3


@patch("src.api.api_adapter.requests.get")
def test_get_aeroplanes_filters_invalid_states(mock_get: Mock, api: ApiAdapter) -> None:
    """Если в списке states попался не список (строка/число), он игнорируется."""
    mock_get.side_effect = [
        make_response([{"boundingbox": ["1", "2", "3", "4"]}]),
        make_response({"states": [["good", "plane"], "bad_plane", 123, ["another", "good"]]}),
    ]
    assert api.get_aeroplanes("Testland") == [["good", "plane"], ["another", "good"]]


def test_get_saved_coords(api):
    """Проверка реального извлечения координат из настроек."""
    with patch.dict("src.api.api_adapter.USER_SETTINGS", {"country_coordinates": {"TestCountry": [10, 20, 30, 40]}}):
        # Существующая страна
        assert api._get_saved_coords("TestCountry") == [10.0, 20.0, 30.0, 40.0]
        # Несуществующая страна
        assert api._get_saved_coords("Unknown") is None


@pytest.fixture(autouse=True)
def _no_retry_wait(monkeypatch: pytest.MonkeyPatch) -> None:
    """Отключает задержку между попытками retry в тестах этого файла."""
    monkeypatch.setattr(ApiAdapter.get_aeroplanes.retry, "wait", lambda *a, **kw: 0)
