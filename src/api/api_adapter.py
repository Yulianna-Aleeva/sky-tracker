from typing import Any

import requests

from src.api.base_api import BaseAPI
from src.config import USER_SETTINGS, get_logger
from src.constants.messages import ApiMsg

logger = get_logger(__name__)


class ApiAdapter(BaseAPI):
    """Адаптер для получения гео-данных и информации о самолётах."""

    def __init__(self) -> None:
        self.geo_url = USER_SETTINGS.get("geo_url", "")
        self.sky_url = USER_SETTINGS.get("sky_url", "")
        # Обязательный User-Agent для обращения к Nominatim API (или блокировка запроса - HTTP 403)
        self.headers = {"User-Agent": "sky-tracker/1.0"}

    def _get_coordinates(self, country: str) -> list[str] | None:
        """Получает координаты (bounding box) страны."""
        params = {"country": country, "format": "json", "limit": 1}
        # Отправляем запрос к гео‑API (с таймаутом), если код вернул ошибку → except
        try:
            response = requests.get(self.geo_url, params=params, headers=self.headers, timeout=8)
            response.raise_for_status()
            data = response.json()

            # Если API не вернул данные, используем координаты из настроек
            if not data:
                logger.warning(ApiMsg.COORD_NF.format(country=country))
                return USER_SETTINGS.get("country_coordinates", {}).get(country)

            # Возвращаем первый результат и его bounding box
            return data[0].get("boundingbox")

        # Если сетевая ошибка или недоступно API, используем координаты из настроек
        except requests.RequestException as e:
            logger.error(f"{ApiMsg.REQ_ERR.format(url=self.geo_url)}: {e}")
            return USER_SETTINGS.get("country_coordinates", {}).get(country)

    def get_aeroplanes(self, country: str) -> list[Any]:
        """Получает список самолётов в воздушном пространстве страны."""
        # Узнаём координаты страны
        bbox = self._get_coordinates(country)
        # Если координаты не получены
        if not bbox:
            return []

        # Распаковываем параметры bounding box для OpenSky API
        min_lat, max_lat, min_lon, max_lon = bbox
        params = {
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

            states = data.get("states")
            # Если None, например, в небе над страной сейчас нет отслеживаемых бортов
            if not states:
                logger.warning(ApiMsg.PLANES_NF.format(country=country))
                return []

            # Успешный возврат списка самолётов
            logger.info(ApiMsg.PLANES_OK.format(country=country))
            return states

        # Если OpenSky API недоступно
        except requests.RequestException as e:
            logger.error(f"{ApiMsg.REQ_ERR.format(url=self.sky_url)}: {e}")
            return []
