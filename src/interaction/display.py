from collections import Counter

from src.classes.aeroplane import Aeroplane
from src.constants.messages import Msg


def show_aeroplanes_table(planes: list[Aeroplane]) -> None:
    """Выводит список самолётов в виде краткой таблицы."""
    if not planes:
        print(Msg.NO_DATA)
        return

    header = f"{'ICAO24':<10} | {'Callsign':<10} | {'Country':<20} | {'Altitude':>10} | {'Velocity':>10}"
    print(header)
    print("-" * len(header))

    for p in planes:
        icao = p.icao24 or "-"
        callsign = p.callsign or "-"
        country = p.origin_country or "-"
        altitude = f"{p.baro_altitude:.1f}" if p.baro_altitude is not None else "-"
        velocity = f"{p.velocity:.1f}" if p.velocity is not None else "-"
        print(f"{icao:<10} | {callsign:<10} | {country:<20} | {altitude:>10} | {velocity:>10}")


def show_summary(planes: list[Aeroplane]) -> None:
    """Выводит сводку: всего самолётов и распределение по странам вылета."""
    if not planes:
        print(Msg.NO_DATA)
        return

    print(f"Всего сохранено: {len(planes)} самолётов\n")
    print("По странам (origin_country):")

    counter = Counter(p.origin_country or "Unknown" for p in planes)
    for country, count in counter.most_common():
        print(f"  {country}: {count}")


def show_statistics(planes: list[Aeroplane], mode: str) -> None:
    """Выводит статистику: на земле / в воздухе / спецрейсы (SPI)."""
    if not planes:
        print(Msg.NO_DATA)
        return

    total = len(planes)

    if mode == "on_ground":
        count = sum(1 for p in planes if p.on_ground)
        label = "На земле"
    elif mode == "in_air":
        count = sum(1 for p in planes if not p.on_ground)
        label = "В воздухе"
    elif mode == "spi":
        count = sum(1 for p in planes if p.spi)
        label = "Спецрейсы (SPI)"
    else:
        print(Msg.INVALID)
        return

    percent = count / total * 100
    print(f"{label}: {count} из {total} ({percent:.1f}%)")


def show_leaders(planes: list[Aeroplane]) -> None:
    """Выводит топ-3 лидеров: самый быстрый, самый высокий, крутой набор высоты."""
    if not planes:
        print(Msg.NO_DATA)
        return

    fastest = max(planes, key=lambda p: p.velocity if p.velocity is not None else -1)
    highest = max(planes, key=lambda p: p.baro_altitude if p.baro_altitude is not None else -1)
    steepest = max(planes, key=lambda p: p.vertical_rate if p.vertical_rate is not None else -1)

    print("Топ-лидеры:")
    print(
        f"Самый быстрый:    {fastest.callsign or '-'} ({fastest.origin_country or '-'}) — {fastest.velocity:.1f} м/с"
    )
    print(
        f"Выше всех:        {highest.callsign or '-'} ({highest.origin_country or '-'}) "
        f"— {highest.baro_altitude:.1f} м"
    )
    print(
        f"Крутой набор:     {steepest.callsign or '-'} ({steepest.origin_country or '-'}) "
        f"— {steepest.vertical_rate:.1f} м/с"
    )


def show_help() -> None:
    """Выводит справку по управлению программой."""
    print("=== ПОМОЩЬ ===")
    print("Управляющие символы:")
    print(f"  {Msg.YES} — Да")
    print(f"  {Msg.NO} — Нет")
    print(f"  {Msg.CUSTOM} — Свой ввод / Выход из программы")
    print(f"  {Msg.RESET} — Обнулить фильтр (в главном меню — все фильтры)")
    print(f"  {Msg.BACK} — Назад в главное меню (в главном меню — это справка)")
    print()
    print("Как работает программа:")
    print("  1. Загрузите самолёты по стране (пункт 1).")
    print("  2. Установите фильтры (пункты 2-8).")
    print("  3. Смотрите топы, статистику, лидеров.")
    print("  Активные фильтры отображаются под пунктами меню.")


def show_menu(filters: dict) -> None:
    """Выводит главное меню с активными фильтрами под пунктами."""
    items = [
        (1, "Выбрать другую страну или город для анализа", "country"),
        (2, "Фильтр по стране вылета", "reg_country"),
        (3, "Топ-лидеры (быстрый / высокий / крутой)", None),
        (4, "Топ-N по высоте", "top_altitude"),
        (5, "Топ-N по скорости", "top_velocity"),
        (6, "Статистика: в воздухе", None),
        (7, "Статистика: на земле", None),
        (8, "Статистика: спецрейсы (SPI)", None),
        (9, "Показать все сохранённые", None),
    ]

    print("\n=== SKY TRACKER ===")
    for num, title, key in items:
        print(f"{num} - {title}")
        if key and filters.get(key) is not None:
            print(f"    > {filters[key]}")

    print("* - Обнулить все фильтры")
    print("/ - Помощь / Инструкция")
    print("0 - Выход")
