import json
from pathlib import Path
from typing import Any

from src.classes.aeroplane import Aeroplane
from src.config import FILE_PATH, get_logger
from src.constants.messages import ErrorMsg
from src.storage.base_saver import BaseSaver

logger = get_logger(__name__)


class JSONSaver(BaseSaver):
    """Класс для работы с информацией о самолётах в JSON-файле."""

    def __init__(self, file_path: str | Path = FILE_PATH) -> None:
        self._file_path = Path(file_path)
        # Создаём папку, если её нет
        self._file_path.parent.mkdir(parents=True, exist_ok=True)
        # Если файла нет, создаём его с пустым списком
        if not self._file_path.exists():
            self._write([])

    def _read(self) -> list[dict[str, Any]]:
        """Читает список самолётов из файла."""
        try:
            with self._file_path.open(encoding="utf-8") as f:
                data: list[dict[str, Any]] = json.load(f)
                return data

        except (FileNotFoundError, json.JSONDecodeError) as e:
            logger.error(ErrorMsg.READ_ERR.format(e=e))
            return []

    def _write(self, data: list[dict[str, Any]]) -> None:
        """Записывает список самолётов в файл (с отступами для читаемости)."""
        with self._file_path.open("w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def add_aeroplane(self, aeroplane: Aeroplane) -> None:
        """Добавляет самолёт в файл, если icao24 уже есть - обновляет."""
        data = self._read()
        new_dict = aeroplane.__dict__
        # Ищем самолёт с таким же icao24 и обновляем его данные

        for i, item in enumerate(data):
            if item.get("icao24") == aeroplane.icao24:
                data[i] = new_dict
                self._write(data)
                return
        # Если не нашли — добавляем как новый
        data.append(new_dict)
        self._write(data)

    def get_aeroplanes(self, **criteria: Any) -> list[Aeroplane]:
        """Возвращает самолёты, соответствующие критериям."""
        data = self._read()
        result = [item for item in data if all(item.get(k) == v for k, v in criteria.items())]
        return [Aeroplane(**item) for item in result]

    def delete_aeroplane(self, icao24: str) -> None:
        """Удаляет самолёт из файла по icao24."""
        data = self._read()
        new_data = [item for item in data if item.get("icao24") != icao24]
        self._write(new_data)
