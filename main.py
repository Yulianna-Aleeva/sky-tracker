import psycopg2

from src.config import get_db_config, get_logger
from src.interaction.menu import run_menu
from src.storage.DBSaver import DBSaver

logger = get_logger(__name__)


def main() -> None:
    """Точка входа в приложение Sky-Tracker."""
    # 1. Читаем настройки из database.ini
    db_params = get_db_config()

    print("Подключение к PostgreSQL и обновление данных из API...")
    logger.info("Запуск инициализации базы данных...")

    # 2. Подключаемся к базе, чтобы развернуть структуру таблиц и залить самолёты
    with psycopg2.connect(**db_params) as conn:
        with conn.cursor() as cur:
            # Создаем объект DBSaver и передаем ему курсор базы
            db_saver = DBSaver(cur)

            # Создаем таблицы countries и aeroplanes
            db_saver.create_tables()

            # Скачиваем координаты стран
            db_saver.populate_countries()

            # Скачиваем живые самолёты в воздухе
            db_saver.update_aeroplanes_online()

    print("База данных успешно обновлена!")
    logger.info("База данных готова. Запуск пользовательского меню.")

    # 3. Запускаем интерактивное меню программы
    run_menu()


if __name__ == "__main__":
    main()
