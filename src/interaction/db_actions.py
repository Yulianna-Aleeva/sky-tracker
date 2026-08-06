from src.classes.db_manager import DBManager
from src.config import get_db_config


def run_db_analytics() -> None:
    """Запускает меню аналитики напрямую из базы данных PostgreSQL."""
    params = get_db_config()
    manager = DBManager(params)

    print("\n====== АНАЛИТИКА POSTGRESQL ======")
    print("1. Количество самолетов по странам")
    print("2. Средняя скорость всех самолетов")
    print("3. Самолеты со скоростью выше средней")
    print("0. Вернуться обратно")

    choice = input("\n> Ваш выбор: ").strip()

    if choice == "1":
        print("\n[Самолетов по странам]:")
        for row in manager.get_countries_and_aeroplanes_count():
            print(f"Страна/Город: {row[0]} — Самолетов: {row[1]}")

    elif choice == "2":
        avg_speed = manager.get_avg_speed()
        print(f"\nСредняя скорость всех самолетов: {avg_speed:.2f} м/с")

    elif choice == "3":
        print("\n[Самолеты со скоростью выше средней (первые 10)]:")
        fast_planes = manager.get_aeroplanes_with_higher_speed()
        for p in fast_planes[:10]:
            print(f"Позывной: {p[1]} | Скорость: {p[2]} м/с")

    elif choice == "0":
        return
    else:
        print("Неверный пункт.")
