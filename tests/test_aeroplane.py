from typing import Any

import pytest

from src.classes.aeroplane import Aeroplane
from src.constants.messages import Msg


def make_plane(**overrides: Any) -> Aeroplane:
    """Фабрика самолёта с дефолтными значениями."""
    defaults: dict[str, Any] = dict(
        icao24="abc123",
        callsign="TEST1",
        origin_country="Testland",
        position_source=0,
        time_position=1000,
        last_contact=1000,
        longitude=10.0,
        latitude=20.0,
        baro_altitude=5000.0,
        geo_altitude=5010.0,
        on_ground=False,
        true_track=90.0,
        velocity=200.0,
        vertical_rate=5.0,
        sensors=None,
        squawk="1234",
        spi=False,
    )
    defaults.update(overrides)
    return Aeroplane(**defaults)


def test_init_cleans_strings():
    """Строки очищаются от пробелов, пустые → None."""
    p = make_plane(callsign="  AFL1  ", origin_country="")
    assert p.callsign == "AFL1"
    assert p.origin_country is None


def test_init_none_numbers():
    """None в числовых полях остаётся None (не искажается)."""
    p = make_plane(baro_altitude=None, velocity=None)
    assert p.baro_altitude is None
    assert p.velocity is None


def test_init_invalid_numbers():
    """Мусор в числах → None."""
    p = make_plane(baro_altitude="abc", velocity=[1, 2])
    assert p.baro_altitude is None
    assert p.velocity is None


def test_init_bool_coercion():
    """on_ground и spi приводятся к bool."""
    p = make_plane(on_ground=1, spi=0)
    assert p.on_ground is True
    assert p.spi is False


def test_lt_by_altitude():
    """Сравнение по высоте."""
    low = make_plane(baro_altitude=1000.0, velocity=300.0)
    high = make_plane(baro_altitude=9000.0, velocity=100.0)
    assert low < high


def test_lt_by_velocity_when_altitude_equal():
    """При равной высоте — сравнение по скорости."""
    a = make_plane(baro_altitude=5000.0, velocity=100.0)
    b = make_plane(baro_altitude=5000.0, velocity=200.0)
    assert a < b


def test_lt_none_altitude_goes_last():
    """Самолёт без высоты считается 'меньше' (при сортировке DESC уйдёт в конец)."""
    no_alt = make_plane(baro_altitude=None, velocity=999.0)
    with_alt = make_plane(baro_altitude=1.0, velocity=1.0)
    assert no_alt < with_alt


def test_lt_wrong_type_raises():
    """Сравнение с не-Aeroplane → TypeError."""
    p = make_plane()
    with pytest.raises(TypeError, match=Msg.COMPARE_ERR):
        _ = p < 5  # type: ignore[operator]


def test_eq_same_values():
    """Равенство по высоте и скорости."""
    a = make_plane(baro_altitude=5000.0, velocity=200.0)
    b = make_plane(baro_altitude=5000.0, velocity=200.0, callsign="OTHER")
    assert a == b


def test_eq_wrong_type():
    """Равенство с не-Aeroplane → NotImplemented."""
    p = make_plane()
    assert (p == "x") is False


def test_hash_consistent_with_eq():
    """Хэш согласован с равенством (для set/dict)."""
    a = make_plane(baro_altitude=5000.0, velocity=200.0)
    b = make_plane(baro_altitude=5000.0, velocity=200.0)
    assert hash(a) == hash(b)
    assert len({a, b}) == 1


def test_repr_contains_key_fields():
    """repr содержит callsign, страну, скорость, высоту."""
    p = make_plane(callsign="AFL1", origin_country="Italy")
    r = repr(p)
    assert "AFL1" in r
    assert "Italy" in r


def test_repr_unknown_for_none():
    """При None в callsign/country в repr выводится 'Unknown'."""
    p = make_plane(callsign=None, origin_country=None)
    r = repr(p)
    assert "Unknown" in r


def test_cast_to_object_list_valid():
    """Преобразование валидного raw-списка из 17 элементов."""
    raw = [
        [
            "abc123",
            "TEST1 ",
            "Testland",
            1000,
            1000,
            10.0,
            20.0,
            5000.0,
            False,
            200.0,
            90.0,
            5.0,
            None,
            5010.0,
            "1234",
            False,
            0,
        ]
    ]
    planes = Aeroplane.cast_to_object_list(raw)
    assert len(planes) == 1
    assert planes[0].icao24 == "abc123"
    assert planes[0].callsign == "TEST1"
    assert planes[0].baro_altitude == 5000.0


def test_cast_to_object_list_skips_short():
    """Короткие списки (меньше 17 элементов) пропускаются."""
    raw = [["abc", "X"], ["def", "Y", "Z"]]
    planes = Aeroplane.cast_to_object_list(raw)
    assert planes == []


def test_cast_to_object_list_empty():
    """Пустой вход → пустой выход."""
    assert Aeroplane.cast_to_object_list([]) == []


def test_cast_preserves_none():
    """None в raw-данных сохраняется как None, не как 0."""
    raw = [["abc", None, None, None, None, None, None, None, False, None, None, None, None, None, None, False, 0]]
    p = Aeroplane.cast_to_object_list(raw)[0]
    assert p.callsign is None
    assert p.baro_altitude is None
    assert p.velocity is None


def test_sort_desc_top_n():
    """Сортировка DESC по высоте корректна (топ-N)."""
    planes = [
        make_plane(baro_altitude=1000.0),
        make_plane(baro_altitude=9000.0),
        make_plane(baro_altitude=5000.0),
        make_plane(baro_altitude=None),
    ]
    top = sorted(planes, reverse=True)
    assert top[0].baro_altitude == 9000.0
    assert top[1].baro_altitude == 5000.0
    assert top[2].baro_altitude == 1000.0
    assert top[3].baro_altitude is None
