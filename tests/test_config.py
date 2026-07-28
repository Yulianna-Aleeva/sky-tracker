import logging
import sys
from pathlib import Path
from typing import List
from unittest.mock import patch

from src.config import BASE_DIR, LOG_DIR, LOG_FORMAT, get_logger


class MockFrame:
    def __init__(self, filename: str):
        self.filename = filename


def create_mock_stack(filenames: List[str]) -> List[MockFrame]:
    return [MockFrame(filename) for filename in filenames]


def test_get_logger_main_module() -> None:
    """Проверяем создание логгера для основного модуля."""
    filenames = ["__main__.py", str(BASE_DIR / "main_script.py")]
    with patch("inspect.stack", return_value=create_mock_stack(filenames)):
        logger = get_logger("__main__")
        expected_name = "main_script"
        assert isinstance(logger, logging.Logger)
        assert logger.level == logging.DEBUG
        assert not logger.propagate
        assert len(logger.handlers) == 1
        assert isinstance(logger.handlers[0], logging.FileHandler)
        assert logger.name == expected_name


def test_get_logger_submodule() -> None:
    """Проверяем создание логгера для подмодуля."""
    filenames = ["__main__.py", str(BASE_DIR / "src" / "api" / "api_adapter.py")]
    with patch("inspect.stack", return_value=create_mock_stack(filenames)):
        logger = get_logger("__main__")
        expected_name = "src.api.api_adapter"
        assert logger.name == expected_name
        assert (LOG_DIR / f"{expected_name}.log").exists()


def test_get_logger_no_stack() -> None:
    """Проверяем создание логгера при ValueError (файл вне BASE_DIR)."""
    # dummy.py вызовет ValueError, так как это не путь от BASE_DIR
    with patch("inspect.stack", return_value=create_mock_stack(["__main__.py", "dummy.py"])):
        logger = get_logger("__main__")
        assert logger.name == Path(sys.argv[0]).stem


def test_get_logger_no_handlers() -> None:
    """Проверяем, что логгер создаётся только при отсутствии хендлеров."""
    logger = get_logger("test_module_handlers")
    original_handlers = logger.handlers.copy()
    new_logger = get_logger("test_module_handlers")
    assert new_logger.handlers == original_handlers


def test_logger_file_handler() -> None:
    """Проверяем настройки FileHandler."""
    logger = get_logger("test_module_file")
    handler = logger.handlers[0]
    assert handler.level == logging.DEBUG
    assert isinstance(handler, logging.FileHandler)
    formatter = handler.formatter
    assert formatter is not None
    assert isinstance(formatter, logging.Formatter)
    assert formatter._style._fmt == LOG_FORMAT


def test_cleanup_log_files():
    """Безопасное удаление тестовых лог-файлов."""
    for file in LOG_DIR.glob("*.log"):
        try:
            if "pytest" not in file.name:
                file.unlink()
        except PermissionError:
            continue
