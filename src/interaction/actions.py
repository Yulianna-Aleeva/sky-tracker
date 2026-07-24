from src.api.api_adapter import ApiAdapter
from src.classes.aeroplane import Aeroplane
from src.config import USER_SETTINGS
from src.constants.messages import Msg
from src.interaction.display import (
    show_aeroplanes_table,
    show_leaders,
    show_statistics,
    show_summary,
)
from src.storage.JSONSaver import JSONSaver


def apply_filters(planes: list[Aeroplane], filters: dict) -> list[Aeroplane]:
    """Применяет активные фильтры к списку самолётов."""
    result = planes
    reg = filters.get("reg_country")
    if reg:
        result = [p for p in result if p.origin_country and p.origin_country.lower() == reg.lower()]
    return result


def action_load_planes(filters: dict) -> list[Aeroplane] | None:
    """Загружает самолёты по стране (из списка или свой ввод)."""
    countries = USER_SETTINGS.get("user_countries", [])
    print(Msg.COUNTRY_TITLE)
    for i, country in enumerate(countries, 1):
        print(f"  {i}. {country}")
    print(f"  {Msg.CUSTOM}. Свой ввод")

    choice = input(Msg.CHOICE).strip()

    if choice == Msg.CUSTOM:
        country = input(Msg.CUSTOM_COUNTRY).strip()
    elif choice.isdigit() and 1 <= int(choice) <= len(countries):
        country = countries[int(choice) - 1]
    else:
        print(Msg.INVALID)
        return None

    api = ApiAdapter()
    raw = api.get_aeroplanes(country)

    if raw is None:
        print(Msg.LOAD_ERR)
        return None

    planes = Aeroplane.cast_to_object_list(raw)
    filters["country"] = country

    if not planes:
        print(Msg.EMPTY_SKY)
        return planes

    # Сохраняем/обновляем данные в JSON (по icao24)
    saver = JSONSaver()
    for plane in planes:
        saver.add_aeroplane(plane)

    print(Msg.LOADED_OK.format(count=len(planes)))
    show_aeroplanes_table(planes[:5])

    return planes


def action_top_altitude(planes: list[Aeroplane], filters: dict) -> None:
    """Показывает топ-N самолётов по высоте (по убыванию)."""
    if not planes:
        print(Msg.NO_DATA)
        return

    if filters.get("top_altitude") is not None:
        print(Msg.CURRENT_FILTER.format(value=filters["top_altitude"]))
        value = input(Msg.NEW_TOP_N.format(reset=Msg.RESET, back=Msg.BACK)).strip()
        if value == Msg.BACK:
            return
        if value == Msg.RESET:
            filters.pop("top_altitude", None)
            return
        if not value.isdigit() or int(value) < 1:
            print(Msg.INVALID)
            return
        filters["top_altitude"] = int(value)
    else:
        value = input(Msg.TOP_N).strip()
        if not value.isdigit() or int(value) < 1:
            print(Msg.INVALID)
            return
        filters["top_altitude"] = int(value)

    n = filters["top_altitude"]

    sorted_planes = sorted(
        planes,
        key=lambda p: p.baro_altitude if p.baro_altitude is not None else -1,
        reverse=True,
    )

    print(f"\nТоп-{n} по высоте:")
    show_aeroplanes_table(sorted_planes[:n])


def action_top_velocity(planes: list[Aeroplane], filters: dict) -> None:
    """Показывает топ-N самолётов по скорости (по убыванию)."""
    if not planes:
        print(Msg.NO_DATA)
        return

    if filters.get("top_velocity") is not None:
        print(Msg.CURRENT_FILTER.format(value=filters["top_velocity"]))
        value = input(Msg.NEW_TOP_N.format(reset=Msg.RESET, back=Msg.BACK)).strip()
        if value == Msg.BACK:
            return
        if value == Msg.RESET:
            filters.pop("top_velocity", None)
            return
        if not value.isdigit() or int(value) < 1:
            print(Msg.INVALID)
            return
        filters["top_velocity"] = int(value)
    else:
        value = input(Msg.TOP_N).strip()
        if not value.isdigit() or int(value) < 1:
            print(Msg.INVALID)
            return
        filters["top_velocity"] = int(value)

    n = filters["top_velocity"]

    sorted_planes = sorted(
        planes,
        key=lambda p: p.velocity if p.velocity is not None else -1,
        reverse=True,
    )

    print(f"\nТоп-{n} по скорости:")
    show_aeroplanes_table(sorted_planes[:n])


def action_filter_country(planes: list[Aeroplane], filters: dict) -> None:
    """Фильтрует самолёты по стране регистрации (origin_country)."""
    if not planes:
        print(Msg.NO_DATA)
        return

    if filters.get("reg_country") is None:
        countries = USER_SETTINGS.get("user_countries", [])
        print("\nВыберите страну регистрации:")
        for i, country in enumerate(countries, 1):
            print(f"  {i}. {country}")
        print(f"  {Msg.CUSTOM}. Свой ввод")

        choice = input(Msg.CHOICE).strip()

        if choice == Msg.CUSTOM:
            value = input(Msg.CUSTOM_COUNTRY).strip()
        elif choice.isdigit() and 1 <= int(choice) <= len(countries):
            value = countries[int(choice) - 1]
        else:
            print(Msg.INVALID)
            return

        if not value:
            print(Msg.INVALID)
            return

        filters["reg_country"] = value

    country = filters["reg_country"]
    filtered = [p for p in planes if p.origin_country and p.origin_country.lower() == country.lower()]

    if not filtered:
        print(Msg.NOT_FOUND)
        return

    print(f"\nСамолёты из '{country}': {len(filtered)}")
    show_aeroplanes_table(filtered)


def action_leaders(planes: list[Aeroplane]) -> None:
    """Показывает топ-лидеров (быстрый / высокий / крутой)."""
    if not planes:
        print(Msg.NO_DATA)
        return
    show_leaders(planes)


def action_stats_in_air(planes: list[Aeroplane]) -> None:
    """Статистика: сколько в воздухе."""
    if not planes:
        print(Msg.NO_DATA)
        return
    show_statistics(planes, "in_air")


def action_stats_on_ground(planes: list[Aeroplane]) -> None:
    """Статистика: сколько на земле."""
    if not planes:
        print(Msg.NO_DATA)
        return
    show_statistics(planes, "on_ground")


def action_stats_spi(planes: list[Aeroplane]) -> None:
    """Статистика: спецрейсы (SPI)."""
    if not planes:
        print(Msg.NO_DATA)
        return
    show_statistics(planes, "spi")


def action_show_all(planes: list[Aeroplane]) -> None:
    """Показывает все сохранённые: сводка (+) или таблица (-)."""
    if not planes:
        print(Msg.NO_DATA)
        return

    choice = input(Msg.VIEW_MODE).strip()
    if choice == Msg.YES:
        show_summary(planes)
    elif choice == Msg.NO:
        show_aeroplanes_table(planes)
    else:
        print(Msg.INVALID)
