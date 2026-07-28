import pytest

from src.utils.validators import to_clean_str, to_float_or_none, to_int_or_none


@pytest.mark.parametrize(
    "value, expected",
    [
        ("hello", "hello"),
        ("  spaces  ", "spaces"),
        ("", None),
        ("   ", None),
        (None, None),
        (123, None),
        ([], None),
    ],
)
def test_to_clean_str(value, expected):
    """Проверяет очистку строк и обработку не-строк."""
    assert to_clean_str(value) == expected


@pytest.mark.parametrize(
    "value, expected",
    [
        (1, 1.0),
        (1.5, 1.5),
        ("2.7", 2.7),
        ("bad", None),
        (None, None),
        ([], None),
    ],
)
def test_to_float_or_none(value, expected):
    """Проверяет приведение к float и обработку мусора."""
    assert to_float_or_none(value) == expected


@pytest.mark.parametrize(
    "value, expected",
    [
        (5, 5),
        ("10", 10),
        (3.9, 3),
        ("bad", None),
        (None, None),
        ([], None),
    ],
)
def test_to_int_or_none(value, expected):
    """Проверяет приведение к int и обработку мусора."""
    assert to_int_or_none(value) == expected
