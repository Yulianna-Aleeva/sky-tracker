from typing import Any

import psycopg2


class DBManager:
    """Класс для выполнения аналитических запросов к PostgreSQL."""

    def __init__(self, db_params: dict):
        self.db_params = db_params

    def get_countries_and_aeroplanes_count(self) -> list:
        """Возвращает список стран и количество летящих в них самолетов."""
        query = """
            SELECT c.country_name, COUNT(a.icao24)
            FROM countries c
            LEFT JOIN aeroplanes a ON c.country_id = a.country_id
            GROUP BY c.country_name;
        """
        with psycopg2.connect(**self.db_params) as conn:
            with conn.cursor() as cur:
                cur.execute(query)
                data: list = cur.fetchall()
                return data

    def get_all_aeroplanes(self) -> list[tuple[Any, ...]]:
        """Возвращает список всех воздушных судов из базы данных."""
        with psycopg2.connect(**self.db_params) as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT icao24, callsign, velocity FROM aeroplanes;")
                data: list[tuple[Any, ...]] = cur.fetchall()
                return data

    def get_avg_speed(self) -> float:
        """Считает среднюю скорость всех самолетов в воздухе."""
        with psycopg2.connect(**self.db_params) as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT AVG(velocity) FROM aeroplanes;")
                res = cur.fetchone()
                return float(res[0]) if res and res[0] else 0.0

    def get_aeroplanes_with_higher_speed(self) -> list[tuple[Any, ...]]:
        """Возвращает список самолетов, скорость которых выше средней."""
        query = """
            SELECT icao24, callsign, velocity
            FROM aeroplanes
            WHERE velocity > (SELECT AVG(velocity) FROM aeroplanes);
        """
        with psycopg2.connect(**self.db_params) as conn:
            with conn.cursor() as cur:
                cur.execute(query)
                data: list[tuple[Any, ...]] = cur.fetchall()
                return data

    def get_aeroplanes_with_keyword(self, keyword: str) -> list[tuple[Any, ...]]:
        """Ищет самолеты по ключевым символам в их позывном."""
        query = "SELECT icao24, callsign, velocity FROM aeroplanes WHERE callsign LIKE %s;"
        with psycopg2.connect(**self.db_params) as conn:
            with conn.cursor() as cur:
                cur.execute(query, (f"%{keyword}%",))
                data: list[tuple[Any, ...]] = cur.fetchall()
                return data
