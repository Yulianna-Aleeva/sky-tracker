from typing import Any, cast

import requests

from src.api.base_api import BaseAPI
from src.config import USER_SETTINGS, get_logger
from src.constants.messages import Msg

logger = get_logger(__name__)


class ApiAdapter(BaseAPI):
    """Адаптер для получения гео-данных и информации о самолётах."""

    def __init__(self) -> None:
        self.geo_url = USER_SETTINGS.get("geo_url", "")
        self.sky_url = USER_SETTINGS.get("sky_url", "")
        # Обязательный User-Agent для обращения к Nominatim API (или блокировка запроса - HTTP 403)
        self.headers = {"User-Agent": "sky-tracker/1.0"}

    @staticmethod
    def _to_bbox(value: Any) -> list[float] | None:
        """Преобразует bounding box в список из 4 координат."""
        if not isinstance(value, list) or len(value) < 4:
            return None
        try:
            return [float(value[0]), float(value[1]), float(value[2]), float(value[3])]
        except (TypeError, ValueError):
            return None

    def _get_saved_coords(self, country: str) -> list[float] | None:
        """Берёт координаты страны из настроек."""
        save_coords = USER_SETTINGS.get("country_coordinates", {}).get(country)
        return self._to_bbox(save_coords)

    def _get_coordinates(self, country: str) -> list[float] | None:
        """Получает координаты (bounding box) страны."""
        # Если координаты не найдены, логируем предупреждение и возвращаем сохранённые координаты
        if not self.geo_url:
            logger.warning(Msg.COORD_NF.format(country=country))
            return self._get_saved_coords(country)

        params: dict[str, str | int] = {"country": country, "format": "json", "limit": 1}
        # Отправляем запрос к гео‑API (с таймаутом), если код вернул ошибку → except
        try:
            response = requests.get(self.geo_url, params=params, headers=self.headers, timeout=8)
            response.raise_for_status()
            data = response.json()

            # Если API не вернул данные, используем координаты из настроек
            if not isinstance(data, list) or not data or not isinstance(data[0], dict):
                logger.warning(Msg.COORD_NF.format(country=country))
                return self._get_saved_coords(country)

            # Возвращаем первый результат и его bounding box
            raw_bbox = data[0].get("boundingbox")
            if not isinstance(raw_bbox, list) or len(raw_bbox) < 4:
                return self._get_saved_coords(country)
            return [float(raw_bbox[0]), float(raw_bbox[1]), float(raw_bbox[2]), float(raw_bbox[3])]

        # Если сетевая ошибка или недоступно API, используем координаты из настроек
        except requests.RequestException as e:
            logger.error(f"{Msg.REQ_ERR.format(url=self.geo_url)}: {e}")
            return self._get_saved_coords(country)

    def get_aeroplanes(self, country: str) -> list[Any] | None:
        """Получает список самолётов в воздушном пространстве страны."""
        # Узнаём координаты страны
        bbox = self._get_coordinates(country)
        # Если координаты не получены
        if not bbox:
            return None

        # Распаковываем параметры bounding box для OpenSky API
        min_lat, max_lat, min_lon, max_lon = bbox
        params: dict[str, float] = {
            "lamin": min_lat,  # юг
            "lamax": max_lat,  # север
            "lomin": min_lon,  # запад
            "lomax": max_lon,  # восток
        }

        try:
            # Запрос к OpenSky API с координатами
            response = requests.get(self.sky_url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()

            if not isinstance(data, dict):
                logger.warning(Msg.RESP_ERR.format(country=country))
                return None

            states = data.get("states")
            # Если None, например, в небе над страной сейчас нет отслеживаемых бортов
            if states is None:
                logger.warning(Msg.PLANES_NF.format(country=country))
                return []

            planes: list[list[Any]] = [cast(list[Any], state) for state in states if isinstance(state, list)]

            # Успешный возврат списка самолётов
            logger.info(Msg.PLANES_OK.format(country=country))
            return planes

        # Если OpenSky API недоступно
        except requests.RequestException as e:
            logger.error(f"{Msg.REQ_ERR.format(url=self.sky_url)}: {e}")
            return None
