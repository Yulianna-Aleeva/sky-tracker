from typing import Any


def to_clean_str(value: Any) -> str | None:
    """Очищает строку от пробелов. Пустая строка или не строка → None."""
    # Проверяем, что значение строка
    if isinstance(value, str):
        # Убираем пробелы по краям
        clean = value.strip()
        # Если после очистки пусто → None
        return clean or None
    # Если не тот тип, сразу возвращаем None
    return None


def to_float_or_none(value: Any) -> float | None:
    """Приводит к float."""
    # Если данных нет → None
    if value is None:
        return None
    try:
        # Конвертируем число
        return float(value)
    except (ValueError, TypeError):
        # Невалидное значение → None
        return None


def to_int_or_none(value: Any) -> int | None:
    """Приводит к int."""
    # Если данных нет → None
    if value is None:
        return None
    try:
        # Конвертируем число
        return int(value)
    except (ValueError, TypeError):
        # Невалидное значение → None
        return None
