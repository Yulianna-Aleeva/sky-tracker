from src.constants.messages import Msg
from src.interaction.display import (
    show_aeroplanes_table,
    show_help,
    show_leaders,
    show_menu,
    show_statistics,
    show_summary,
)
from tests.test_aeroplane import make_plane


def test_table_empty(capsys):
    """Пустой список → сообщение о нет данных."""
    show_aeroplanes_table([])
    assert Msg.NO_DATA in capsys.readouterr().out


def test_table_with_planes(capsys):
    """Таблица содержит icao24 и callsign."""
    planes = [make_plane(icao24="abc123", callsign="TEST1")]
    show_aeroplanes_table(planes)
    out = capsys.readouterr().out
    assert "abc123" in out
    assert "TEST1" in out


def test_table_none_values(capsys):
    """None-значения заменяются на '-'."""
    planes = [make_plane(callsign=None, baro_altitude=None, velocity=None)]
    show_aeroplanes_table(planes)
    out = capsys.readouterr().out
    assert "-" in out


def test_summary_empty(capsys):
    """Пустой список → сообщение о нет данных."""
    show_summary([])
    assert Msg.NO_DATA in capsys.readouterr().out


def test_summary_groups_by_country(capsys):
    """Сводка группирует по origin_country."""
    planes = [
        make_plane(origin_country="Italy"),
        make_plane(origin_country="Italy"),
        make_plane(origin_country="China"),
    ]
    show_summary(planes)
    out = capsys.readouterr().out
    assert "Italy: 2" in out
    assert "China: 1" in out
    assert "Всего сохранено: 3" in out


def test_stats_empty(capsys):
    """Пустой список → сообщение о нет данных."""
    show_statistics([], "in_air")
    assert Msg.NO_DATA in capsys.readouterr().out


def test_stats_in_air(capsys):
    """Статистика 'в воздухе' считает планы с on_ground=False."""
    planes = [
        make_plane(on_ground=False),
        make_plane(on_ground=False),
        make_plane(on_ground=True),
    ]
    show_statistics(planes, "in_air")
    out = capsys.readouterr().out
    assert "2 из 3" in out


def test_stats_on_ground(capsys):
    """Статистика 'на земле'."""
    planes = [make_plane(on_ground=True), make_plane(on_ground=False)]
    show_statistics(planes, "on_ground")
    out = capsys.readouterr().out
    assert "1 из 2" in out


def test_stats_spi(capsys):
    """Статистика спецрейсов (SPI)."""
    planes = [make_plane(spi=True), make_plane(spi=False)]
    show_statistics(planes, "spi")
    out = capsys.readouterr().out
    assert "1 из 2" in out


def test_stats_invalid_mode(capsys):
    """Неизвестный режим → сообщение о неверном вводе."""
    show_statistics([make_plane()], "wrong")
    assert Msg.INVALID in capsys.readouterr().out


def test_leaders_empty(capsys):
    """Пустой список → сообщение о нет данных."""
    show_leaders([])
    assert Msg.NO_DATA in capsys.readouterr().out


def test_leaders_selects_correct(capsys):
    """Лидеры выбираются корректно."""
    planes = [
        make_plane(callsign="FAST", velocity=300.0, baro_altitude=1000.0, vertical_rate=1.0),
        make_plane(callsign="HIGH", velocity=100.0, baro_altitude=9000.0, vertical_rate=1.0),
        make_plane(callsign="STEEP", velocity=100.0, baro_altitude=1000.0, vertical_rate=20.0),
    ]
    show_leaders(planes)
    out = capsys.readouterr().out
    assert "FAST" in out
    assert "HIGH" in out
    assert "STEEP" in out


def test_help_prints_symbols(capsys):
    """Справка содержит управляющие символы."""
    show_help()
    out = capsys.readouterr().out
    assert Msg.YES in out
    assert Msg.NO in out
    assert Msg.RESET in out
    assert Msg.BACK in out


def test_menu_no_filters(capsys):
    """Меню без фильтров содержит заголовок и все пункты."""
    show_menu({})
    out = capsys.readouterr().out
    assert "SKY TRACKER" in out
    for i in range(1, 10):
        assert f"{i} -" in out


def test_menu_shows_active_filters(capsys):
    """Меню показывает активные фильтры под пунктами."""
    show_menu({"country": "Italy", "top_altitude": 5})
    out = capsys.readouterr().out
    assert "> Italy" in out
    assert "> 5" in out
