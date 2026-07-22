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
        # User-Agent для запроса к Nominatim API
        self.headers = {"User-Agent": "sky-tracker/1.0"}

    def _get_coordinates(self, country: str) -> list[str] | None:
        """Получает координаты (bounding box) страны."""
        # Параметры запроса: ищем страну, просим ответ в JSON, берем только 1 совпадение
        params = {"country": country, "format": "json", "limit": 1}
        try:
            # Отправляем GET-запрос к Nominatim. Ожидаем ответ до 8 сек.
            response = requests.get(self.geo_url, params=params, headers=self.headers, timeout=8)
            # Если сервер вернул ошибку, код остановится и перейдёт в except
            response.raise_for_status()
            # Превращаем ответ сервера в список/словарь
            data = response.json()

            # Если вернулся пустой список (страна не найдена)
            if not data:
                logger.warning(ApiMsg.COORD_NF.format(country=country))
                return USER_SETTINGS.get("country_coordinates", {}).get(country)

            # В ответе берём первый элемент списка (словарь) и достаём из него координаты по ключу 'boundingbox'
            return data[0].get("boundingbox")

        except requests.RequestException as e:
            # Если пропал интернет или сервер упал
            logger.error(f"{ApiMsg.REQ_ERR.format(url=self.geo_url)}: {e}")
            return USER_SETTINGS.get("country_coordinates", {}).get(country)

    def get_aeroplanes(self, country: str) -> list[Any]:
        """Получает список самолётов в воздушном пространстве страны."""
        # Узнаём координаты страны с помощью приватного метода
        bbox = self._get_coordinates(country)
        # Если координаты не нашлись или ошибка - возвращаем пустой список
        if not bbox:
            return []

        # Формируем параметры для OpenSky API по bounding box
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
            # Превращаем ответ в словарь
            data = response.json()

            # Кладём данные о самолётах из OpenSky в ключ "states"
            states = data.get("states")
            # Если None, например, в небе над страной сейчас пусто
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
