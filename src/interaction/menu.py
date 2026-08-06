from src.classes.aeroplane import Aeroplane
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
from src.interaction.db_actions import run_db_analytics
from src.interaction.display import show_help, show_menu


def run_menu() -> None:
    """Главный цикл интерактивного меню."""
    planes: list[Aeroplane] = []
    filters: dict = {}

    print(Msg.WELCOME)

    while True:
        result = action_load_planes(filters)

        # Если пользователь ввёл неверный пункт или нажал отмену/выход
        if result is None:
            print(Msg.GOOD_BYE)
            return

        # ПРОВЕРЯЕМ ФЛАГ НАЖАТИЯ МИНУСА
        if filters.get("db_analytics") is True:
            filters.clear()  # Полностью чистим временный флаг
            run_db_analytics()  # Запускаем SQL-меню
            continue  # После выхода из SQL-меню (0) отправляем обратно на выбор городов

        planes = result
        break

    # Главное меню
    while True:
        show_menu(filters)
        choice = input(Msg.CHOICE).strip()

        if choice == Msg.EXIT:
            print(Msg.GOOD_BYE)
            break

        elif choice == Msg.BACK:  # "/"
            show_help()

        elif choice == Msg.RESET:  # "*"
            filters.clear()
            print(Msg.RESET_OK)

        elif choice == "1":
            result = action_load_planes(filters)
            if result is not None:
                planes = result

        elif choice == "2":
            action_filter_country(planes, filters)

        elif choice == "3":
            action_leaders(apply_filters(planes, filters))

        elif choice == "4":
            action_top_altitude(apply_filters(planes, filters), filters)

        elif choice == "5":
            action_top_velocity(apply_filters(planes, filters), filters)

        elif choice == "6":
            action_stats_in_air(apply_filters(planes, filters))

        elif choice == "7":
            action_stats_on_ground(apply_filters(planes, filters))

        elif choice == "8":
            action_stats_spi(apply_filters(planes, filters))

        elif choice == "9":
            action_show_all(planes)

        else:
            print(Msg.INVALID)
