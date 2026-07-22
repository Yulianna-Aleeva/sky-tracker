from src.api.api_adapter import ApiAdapter


def main() -> None:
    api = ApiAdapter()
    # country = "Russia - Tobolsk"
    # country = "Russia - Tyumen"
    country = "Russia - Moscow"
    # country = "China - Beijing"
    # country = "USA - New-York"
    # country = "Switzerland"

    print(f"Запрос данных для {country}.")
    aeroplanes = api.get_aeroplanes(country)

    if aeroplanes:
        print(f"Найдено самолётов: {len(aeroplanes)}")
        print(f"Пример данных (первый самолёт): {aeroplanes[0]}")
        print(f"Пример данных (второй самолёт): {aeroplanes[1]}")
        print(f"Пример данных (третий самолёт): {aeroplanes[2]}")
    else:
        print("Самолёты не найдены или произошла ошибка.")


if __name__ == "__main__":
    main()
