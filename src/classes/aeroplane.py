from src.constants.messages import ErrorMsg


class Aeroplane:
    """Класс для представления самолёта."""

    def __init__(
        self,
        icao24: str,  # 24-битный ICAO-код (уникальный идентификатор борта)
        callsign: str | None,  # позывной рейса (например, «AFL123»)
        origin_country: str | None,  # страна регистрации воздушного судна
        time_position: int | None,  # время последнего обновления позиции (секунды с эпохи Unix)
        last_contact: int | None,  # время последнего контакта с бортом
        longitude: float | None,  # долгота текущего положения
        latitude: float | None,  # широта текущего положения
        baro_altitude: float | None,  # барометрическая высота полёта над уровнем моря (метры)
        on_ground: bool,  # флаг: на земле (True) или в полёте (False)
        velocity: float | None,  # горизонтальная скорость (м/с)
        true_track: float | None,  # направление движения, курс (угол в градусах - 0–360)
        vertical_rate: float | None,  # вертикальная скорость (м/с)
        sensors: list[int] | None,  # серийные номера датчиков, принявших сигнал
        geo_altitude: float | None,  # геометрическая высота (метры)
        squawk: str | None,  # 4-значный код ответчика (например, 7700-авария, 7600-потеря связи, 7500-захват судна)
        spi: bool,  # флаг специального назначения (Special Purpose Indicator - военный борт, борт с делегацией и т.п.)
        position_source: int,  # источник позиции (0=ADS-B, 1=ASTERIX, 2=MLAT, 3=FLARM)
    ) -> None:
