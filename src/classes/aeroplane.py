from typing import Any

from src.constants.messages import ErrorMsg
from src.utils.validators import to_clean_str, to_float_or_none, to_int_or_none


class StateIndex:
    """Индексы полей в ответе OpenSky API (список states)."""

    ICAO24 = 0
    CALLSIGN = 1
    ORIGIN_COUNTRY = 2
    TIME_POSITION = 3
    LAST_CONTACT = 4
    LONGITUDE = 5
    LATITUDE = 6
    BARO_ALTITUDE = 7
    ON_GROUND = 8
    VELOCITY = 9
    TRUE_TRACK = 10
    VERTICAL_RATE = 11
    SENSORS = 12
    GEO_ALTITUDE = 13
    SQUAWK = 14
    SPI = 15
    POSITION_SOURCE = 16
    # защита от неполной строки
    MIN_LENGTH = 17


class Aeroplane:
    """Класс для представления самолёта."""

    def __init__(
        self,
        # Идентификация и метаданные
        icao24: str,  # 24-битный ICAO-код (уникальный идентификатор борта)
        callsign: str | None,  # позывной рейса (например, «AFL123»)
        origin_country: str | None,  # страна регистрации воздушного судна
        position_source: int,  # источник позиции (0=ADS-B, 1=ASTERIX, 2=MLAT, 3=FLARM)
        # Временные отметки
        time_position: int | None,  # время последнего обновления позиции (секунды с эпохи Unix)
        last_contact: int | None,  # время последнего контакта с бортом
        # Геолокация и высота
        longitude: float | None,  # долгота текущего положения
        latitude: float | None,  # широта текущего положения
        baro_altitude: float | None,  # барометрическая высота полёта над уровнем моря (метры)
        geo_altitude: float | None,  # геометрическая высота (метры)
        # Движение
        on_ground: bool,  # флаг: на земле (True) или в полёте (False)
        true_track: float | None,  # направление движения, курс (угол в градусах - 0–360)
        velocity: float | None,  # горизонтальная скорость (м/с)
        vertical_rate: float | None,  # вертикальная скорость (м/с)
        # Сигналы и статус
        sensors: list[int] | None,  # серийные номера датчиков, принявших сигнал
        squawk: str | None,  # 4-значный код ответчика (например, 7700-авария, 7600-потеря связи, 7500-захват судна)
        spi: bool,  # флаг специального назначения (Special Purpose Indicator - военный борт, борт с делегацией и т.п.)
    ) -> None:
        # Идентификация и метаданные
        self.icao24 = to_clean_str(icao24)
        self.callsign = to_clean_str(callsign)
        self.origin_country = to_clean_str(origin_country)
        self.position_source = to_int_or_none(position_source)
        # Временные отметки
        self.time_position = to_int_or_none(time_position)
        self.last_contact = to_int_or_none(last_contact)
        # Геолокация и высота
        self.longitude = to_float_or_none(longitude)
        self.latitude = to_float_or_none(latitude)
        self.baro_altitude = to_float_or_none(baro_altitude)
        self.geo_altitude = to_float_or_none(geo_altitude)
        # Движение
        self.on_ground = bool(on_ground)
        self.true_track = to_float_or_none(true_track)
        self.velocity = to_float_or_none(velocity)
        self.vertical_rate = to_float_or_none(vertical_rate)
        # Сигналы и статус
        self.sensors = sensors if isinstance(sensors, list) else None
        self.squawk = to_clean_str(squawk)
        self.spi = bool(spi)

    @classmethod
    def cast_to_object_list(cls, data: list[list[Any]]) -> list["Aeroplane"]:
        """Преобразует сырые данные API в объекты Aeroplane."""
        idx = StateIndex
        aeroplanes = []
        for item in data:
            if len(item) >= idx.MIN_LENGTH:
                # Передаём аргументы по именам, чтобы порядок не имел значения
                plane = cls(
                    icao24=item[idx.ICAO24],
                    callsign=item[idx.CALLSIGN],
                    origin_country=item[idx.ORIGIN_COUNTRY],
                    position_source=item[idx.POSITION_SOURCE],
                    time_position=item[idx.TIME_POSITION],
                    last_contact=item[idx.LAST_CONTACT],
                    longitude=item[idx.LONGITUDE],
                    latitude=item[idx.LATITUDE],
                    baro_altitude=item[idx.BARO_ALTITUDE],
                    geo_altitude=item[idx.GEO_ALTITUDE],
                    on_ground=item[idx.ON_GROUND],
                    true_track=item[idx.TRUE_TRACK],
                    velocity=item[idx.VELOCITY],
                    vertical_rate=item[idx.VERTICAL_RATE],
                    sensors=item[idx.SENSORS],
                    squawk=item[idx.SQUAWK],
                    spi=item[idx.SPI],
                )
                aeroplanes.append(plane)
        return aeroplanes

    @staticmethod
    def _num_key(value: float | None) -> tuple[bool, float]:
        """Ключ сравнения: None считается меньше любого числа."""
        return (value is not None, value if value is not None else 0.0)

    def __lt__(self, other: "Aeroplane") -> bool:
        """Сравнение по высоте, если одинаково - по скорости."""
        if not isinstance(other, Aeroplane):
            raise TypeError(ErrorMsg.COMPARE_ERR)
        return (self._num_key(self.baro_altitude), self._num_key(self.velocity)) < (
            self._num_key(other.baro_altitude),
            self._num_key(other.velocity),
        )

    def __eq__(self, other: object) -> bool:
        """Равенство, если высота и скорость совпадают (включая None)."""
        if not isinstance(other, Aeroplane):
            return NotImplemented
        return self.baro_altitude == other.baro_altitude and self.velocity == other.velocity

    def __hash__(self) -> int:
        """Хэш согласован с __eq__ (для корректной работы set/dict)."""
        return hash((self.baro_altitude, self.velocity))

    def __repr__(self) -> str:
        """Выводит "Unknown" для красивого отображения."""
        callsign_disp = self.callsign if self.callsign else "Unknown"
        country_disp = self.origin_country if self.origin_country else "Unknown"
        return (
            f"Aeroplane(callsign='{callsign_disp}', country='{country_disp}', "
            f"velocity={self.velocity}, altitude={self.baro_altitude})"
        )
