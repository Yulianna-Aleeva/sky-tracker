from abc import ABC, abstractmethod
from typing import Any


class BaseAPI(ABC):
    """Абстрактный базовый класс для работы с API."""

    @abstractmethod
    def get_aeroplanes(self, country: str) -> list[dict[str, Any]] | None:
        """Получает информацию о самолётах по названию страны."""
        pass
