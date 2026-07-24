from abc import ABC, abstractmethod
from typing import Any

from src.classes.aeroplane import Aeroplane


class BaseSaver(ABC):
    """Абстрактный класс для работы с хранилищем данных о самолётах."""

    @abstractmethod
    def add_aeroplane(self, aeroplane: Aeroplane) -> None:
        """Добавляет самолёт в хранилище."""
        ...

    @abstractmethod
    def get_aeroplanes(self, **criteria: Any) -> list[Aeroplane]:
        """Получает список самолётов из хранилища по указанным критериям."""
        ...

    @abstractmethod
    def delete_aeroplane(self, icao24: str) -> None:
        """Удаляет самолёт из хранилища по его уникальному коду ICAO24."""
        ...
