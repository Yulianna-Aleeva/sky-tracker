import requests
from psycopg2.extensions import cursor

from src.config import USER_SETTINGS, get_logger

logger = get_logger(__name__)


class DBSaver:
    """Класс для сохранения данных о самолетах и странах в СУБД."""

    def __init__(self, cur: cursor):
        self.cur = cur

    def create_tables(self) -> None:
        """Создаёт таблицы для стран и самолётов, если их нет."""
        logger.info("Создание таблиц countries и aeroplanes в БД...")
        self.cur.execute("""
            CREATE TABLE IF NOT EXISTS countries (
                country_id SERIAL PRIMARY KEY,
                country_name VARCHAR(100) UNIQUE NOT NULL,
                lat NUMERIC,
                lon NUMERIC
            );
        """)
        self.cur.execute("""
            CREATE TABLE IF NOT EXISTS aeroplanes (
                icao24 VARCHAR(50) PRIMARY KEY,
                callsign VARCHAR(50),
                velocity NUMERIC,
                country_id INT REFERENCES countries(country_id) ON DELETE CASCADE
            );
        """)

    def populate_countries(self) -> None:
        """Заполняет таблицу стран координатами напрямую из файла настроек JSON."""
        logger.info("Заполнение таблицы стран координатами из настроек...")

        # Достаем списки стран и их готовые координаты из JSON
        countries_list = USER_SETTINGS.get("user_countries", [])
        coordinates_dict = USER_SETTINGS.get("country_coordinates", {})

        for country in countries_list:
            # Получаем массив [min_lat, max_lat, min_lon, max_lon]
            coords = coordinates_dict.get(country)

            if coords and len(coords) == 4:
                # Берем среднее значение диапазона
                lat = (coords[0] + coords[1]) / 2
                lon = (coords[2] + coords[3]) / 2

                self.cur.execute(
                    """
                    INSERT INTO countries (country_name, lat, lon)
                    VALUES (%s, %s, %s)
                    ON CONFLICT (country_name) DO NOTHING;
                """,
                    (country, lat, lon),
                )

    def update_aeroplanes_online(self) -> None:
        """Загружает текущие самолеты из OpenSky и привязывает их к странам."""
        logger.info("Обновление данных о самолетах в воздухе...")
        self.cur.execute("TRUNCATE TABLE aeroplanes;")

        # Получаем ссылку из JSON настроек
        url = USER_SETTINGS.get("sky_url")
        response = requests.get(url).json()
        states = response.get("states", [])

        self.cur.execute("SELECT country_name, country_id FROM countries;")
        country_map = {name: cid for name, cid in self.cur.fetchall()}

        for state in states:
            origin_country = state[2]

            if origin_country in country_map:
                icao24 = state[0]
                callsign = state[1].strip() if state[1] else "UNKNOWN"
                velocity = state[9] if state[9] is not None else 0

                self.cur.execute(
                    """
                    INSERT INTO aeroplanes (icao24, callsign, velocity, country_id)
                    VALUES (%s, %s, %s, %s)
                    ON CONFLICT (icao24) DO NOTHING;
                """,
                    (icao24, callsign, velocity, country_map[origin_country]),
                )
