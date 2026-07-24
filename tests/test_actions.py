from contextlib import ExitStack
from unittest.mock import call, patch

import pytest

from src.constants.messages import Msg
from src.interaction.actions import (
    action_filter_country,
    action_leaders,
    action_load_planes,
    action_show_all,
    action_stats_in_air,
    action_stats_on_ground,
    action_stats_spi,
    action_top_altitude,
    action_top_velocity,
    apply_filters,
)
from tests.test_aeroplane import make_plane

TOP_ACTIONS = [
    (action_top_altitude, "top_altitude", "baro_altitude"),
    (action_top_velocity, "top_velocity", "velocity"),
]


def test_apply_filters_no_filter() -> None:
    """Без фильтров возвращается исходный список."""
    planes = [make_plane(icao24="a"), make_plane(icao24="b")]
    assert apply_filters(planes, {}) == planes


def test_apply_filters_by_country_case_insensitive() -> None:
    """Фильтр по стране регистрации работает без учёта регистра и пропускает None."""
    planes = [
        make_plane(icao24="a", origin_country="Italy"),
        make_plane(icao24="b", origin_country="CHINA"),
        make_plane(icao24="c", origin_country=None),
    ]
    result = apply_filters(planes, {"reg_country": "italy"})
    assert [p.icao24 for p in result] == ["a"]


def test_load_planes_invalid_choice(capsys) -> None:
    """Неверный ввод → INVALID."""
    with (
        patch("src.interaction.actions.USER_SETTINGS", {"user_countries": ["Italy"]}),
        patch(
            "builtins.input",
            return_value="99",
        ),
    ):
        assert action_load_planes({}) is None
    assert Msg.INVALID in capsys.readouterr().out


def test_load_planes_api_error(capsys) -> None:
    """API вернул None → LOAD_ERR."""
    with ExitStack() as stack:
        stack.enter_context(patch("src.interaction.actions.USER_SETTINGS", {"user_countries": ["Italy"]}))
        mock_api = stack.enter_context(patch("src.interaction.actions.ApiAdapter"))
        stack.enter_context(patch("builtins.input", return_value="1"))
        mock_api.return_value.get_aeroplanes.return_value = None
        assert action_load_planes({}) is None
    assert Msg.LOAD_ERR in capsys.readouterr().out


def test_load_planes_empty_result_custom_choice(capsys) -> None:
    """Свой ввод + пустой результат → EMPTY_SKY и пустой список."""
    filters: dict = {}

    with ExitStack() as stack:
        stack.enter_context(patch("src.interaction.actions.USER_SETTINGS", {"user_countries": ["Italy"]}))
        mock_api = stack.enter_context(patch("src.interaction.actions.ApiAdapter"))
        mock_cast = stack.enter_context(patch("src.interaction.actions.Aeroplane.cast_to_object_list"))
        mock_saver = stack.enter_context(patch("src.interaction.actions.JSONSaver"))
        stack.enter_context(patch("builtins.input", side_effect=[Msg.CUSTOM, "Japan"]))
        mock_api.return_value.get_aeroplanes.return_value = []
        mock_cast.return_value = []
        result = action_load_planes(filters)

    assert result == []
    assert filters["country"] == "Japan"
    mock_saver.assert_not_called()
    assert Msg.EMPTY_SKY in capsys.readouterr().out


def test_load_planes_success() -> None:
    """Успешная загрузка: страна из списка, сохранение в JSON и показ таблицы."""
    filters: dict = {}
    raw = [["raw"]]
    planes = [make_plane(icao24="a"), make_plane(icao24="b")]

    with ExitStack() as stack:
        stack.enter_context(patch("src.interaction.actions.USER_SETTINGS", {"user_countries": ["Italy", "China"]}))
        mock_api = stack.enter_context(patch("src.interaction.actions.ApiAdapter"))
        mock_saver_cls = stack.enter_context(patch("src.interaction.actions.JSONSaver"))
        mock_cast = stack.enter_context(patch("src.interaction.actions.Aeroplane.cast_to_object_list"))
        mock_show = stack.enter_context(patch("src.interaction.actions.show_aeroplanes_table"))
        stack.enter_context(patch("builtins.input", return_value="2"))

        mock_api.return_value.get_aeroplanes.return_value = raw
        mock_cast.return_value = planes
        result = action_load_planes(filters)

    assert result == planes
    assert filters["country"] == "China"
    mock_api.return_value.get_aeroplanes.assert_called_once_with("China")
    mock_cast.assert_called_once_with(raw)
    mock_saver_cls.return_value.add_aeroplane.assert_has_calls([call(planes[0]), call(planes[1])])
    mock_show.assert_called_once_with(planes[:5])


@pytest.mark.parametrize(("action", "key", "field"), TOP_ACTIONS)
def test_top_action_empty_planes(action, key, field, capsys) -> None:
    """Пустой список → сообщение о пустом небе."""
    action([], {})
    assert Msg.EMPTY_SKY in capsys.readouterr().out


@pytest.mark.parametrize(("action", "key", "field"), TOP_ACTIONS)
def test_top_action_new_filter(action, key, field) -> None:
    """Новый фильтр задаётся и выводит топ по убыванию."""
    planes = [
        make_plane(icao24="low", **{field: 1.0}),
        make_plane(icao24="high", **{field: 9.0}),
        make_plane(icao24="mid", **{field: 5.0}),
    ]
    filters: dict = {}

    with (
        patch("src.interaction.actions.show_aeroplanes_table") as mock_show,
        patch("builtins.input", return_value="2"),
    ):
        action(planes, filters)

    assert filters[key] == 2
    assert [p.icao24 for p in mock_show.call_args.args[0]] == ["high", "mid"]


@pytest.mark.parametrize(("action", "key", "field"), TOP_ACTIONS)
def test_top_action_new_filter_invalid_input(action, key, field, capsys) -> None:
    """Некорректный ввод нового фильтра → INVALID."""
    with patch("builtins.input", return_value="abc"):
        action([make_plane()], {})
    assert Msg.INVALID in capsys.readouterr().out


@pytest.mark.parametrize(("action", "key", "field"), TOP_ACTIONS)
def test_top_action_existing_filter_reset(action, key, field) -> None:
    """RESET при активном фильтре → сброс."""
    filters = {key: 3}
    with (
        patch("src.interaction.actions.show_aeroplanes_table") as mock_show,
        patch(
            "builtins.input",
            return_value=Msg.RESET,
        ),
    ):
        action([make_plane()], filters)
    assert key not in filters
    mock_show.assert_not_called()


@pytest.mark.parametrize(("action", "key", "field"), TOP_ACTIONS)
def test_top_action_existing_filter_back(action, key, field) -> None:
    """BACK при активном фильтре → возврат без изменений."""
    filters = {key: 3}
    with (
        patch("src.interaction.actions.show_aeroplanes_table") as mock_show,
        patch(
            "builtins.input",
            return_value=Msg.BACK,
        ),
    ):
        action([make_plane()], filters)
    assert filters[key] == 3
    mock_show.assert_not_called()


@pytest.mark.parametrize(("action", "key", "field"), TOP_ACTIONS)
def test_top_action_existing_filter_invalid_input(action, key, field, capsys) -> None:
    """Некорректный ввод при активном фильтре → INVALID."""
    filters = {key: 3}
    with patch("builtins.input", return_value="0"):
        action([make_plane()], filters)
    assert filters[key] == 3
    assert Msg.INVALID in capsys.readouterr().out


@pytest.mark.parametrize(("action", "key", "field"), TOP_ACTIONS)
def test_top_action_existing_filter_updates_value(action, key, field) -> None:
    """Активный фильтр можно заменить новым валидным значением."""
    planes = [
        make_plane(icao24="low", **{field: 1.0}),
        make_plane(icao24="high", **{field: 9.0}),
    ]
    filters = {key: 5}

    with (
        patch("src.interaction.actions.show_aeroplanes_table") as mock_show,
        patch("builtins.input", return_value="1"),
    ):
        action(planes, filters)

    assert filters[key] == 1
    assert [p.icao24 for p in mock_show.call_args.args[0]] == ["high"]


def test_filter_country_empty_planes(capsys) -> None:
    """Пустой список → сообщение о пустом небе."""
    action_filter_country([], {})
    assert Msg.EMPTY_SKY in capsys.readouterr().out


def test_filter_country_invalid_choice(capsys) -> None:
    """Неверный номер страны → INVALID."""
    with (
        patch("src.interaction.actions.USER_SETTINGS", {"user_countries": ["Italy"]}),
        patch(
            "builtins.input",
            return_value="99",
        ),
    ):
        action_filter_country([make_plane(origin_country="Italy")], {})
    assert Msg.INVALID in capsys.readouterr().out


def test_filter_country_custom_empty_value(capsys) -> None:
    """Свой ввод, но пустая строка → INVALID."""
    with (
        patch("src.interaction.actions.USER_SETTINGS", {"user_countries": ["Italy"]}),
        patch(
            "builtins.input",
            side_effect=[Msg.CUSTOM, ""],
        ),
    ):
        action_filter_country([make_plane(origin_country="Italy")], {})
    assert Msg.INVALID in capsys.readouterr().out


def test_filter_country_from_list() -> None:
    """Выбор страны по номеру из списка."""
    planes = [make_plane(icao24="a", origin_country="Italy"), make_plane(icao24="b", origin_country="China")]
    filters: dict = {}

    with (
        patch("src.interaction.actions.USER_SETTINGS", {"user_countries": ["Italy", "China"]}),
        patch(
            "src.interaction.actions.show_aeroplanes_table",
        ) as mock_show,
        patch("builtins.input", return_value="1"),
    ):
        action_filter_country(planes, filters)

    assert filters["reg_country"] == "Italy"
    assert [p.icao24 for p in mock_show.call_args.args[0]] == ["a"]


def test_filter_country_custom_input() -> None:
    """Выбор своего ввода фильтрует по введённой стране."""
    planes = [make_plane(icao24="a", origin_country="Italy"), make_plane(icao24="b", origin_country="China")]
    filters: dict = {}

    with (
        patch("src.interaction.actions.USER_SETTINGS", {"user_countries": ["Italy"]}),
        patch(
            "src.interaction.actions.show_aeroplanes_table",
        ) as mock_show,
        patch("builtins.input", side_effect=[Msg.CUSTOM, "China"]),
    ):
        action_filter_country(planes, filters)

    assert filters["reg_country"] == "China"
    assert [p.icao24 for p in mock_show.call_args.args[0]] == ["b"]


def test_filter_country_no_match(capsys) -> None:
    """Если после фильтра нет самолётов → NOT_FOUND."""
    action_filter_country([make_plane(origin_country="Italy")], {"reg_country": "China"})
    assert Msg.NOT_FOUND in capsys.readouterr().out


def test_leaders_empty(capsys) -> None:
    """Пустой список → сообщение о пустом небе."""
    action_leaders([])
    assert Msg.EMPTY_SKY in capsys.readouterr().out


def test_leaders_calls_show() -> None:
    """Для непустого списка вызывается show_leaders."""
    planes = [make_plane()]
    with patch("src.interaction.actions.show_leaders") as mock_show:
        action_leaders(planes)
    mock_show.assert_called_once_with(planes)


@pytest.mark.parametrize("action", [action_stats_in_air, action_stats_on_ground, action_stats_spi])
def test_stats_actions_empty(action, capsys) -> None:
    """Пустой список → сообщение о пустом небе."""
    action([])
    assert Msg.EMPTY_SKY in capsys.readouterr().out


@pytest.mark.parametrize(
    ("action", "mode"),
    [
        (action_stats_in_air, "in_air"),
        (action_stats_on_ground, "on_ground"),
        (action_stats_spi, "spi"),
    ],
)
def test_stats_actions_call_show_statistics(action, mode) -> None:
    """Для непустого списка вызывается show_statistics с нужным режимом."""
    planes = [make_plane()]
    with patch("src.interaction.actions.show_statistics") as mock_show:
        action(planes)
    mock_show.assert_called_once_with(planes, mode)


def test_show_all_empty(capsys) -> None:
    """Пустой список → сообщение о пустом небе."""
    action_show_all([])
    assert Msg.EMPTY_SKY in capsys.readouterr().out


def test_show_all_table() -> None:
    """+ → таблица."""
    planes = [make_plane()]
    with (
        patch("src.interaction.actions.show_aeroplanes_table") as mock_show,
        patch(
            "builtins.input",
            return_value="+",
        ),
    ):
        action_show_all(planes)
    mock_show.assert_called_once_with(planes)


def test_show_all_summary() -> None:
    """- → сводка."""
    planes = [make_plane()]
    with patch("src.interaction.actions.show_summary") as mock_show, patch("builtins.input", return_value="-"):
        action_show_all(planes)
    mock_show.assert_called_once_with(planes)


def test_show_all_invalid(capsys) -> None:
    """Некорректный ввод → INVALID."""
    with patch("builtins.input", return_value="x"):
        action_show_all([make_plane()])
    assert Msg.INVALID in capsys.readouterr().out
