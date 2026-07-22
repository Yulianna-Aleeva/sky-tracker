class ApiMsg:  # Сообщения для API
    REQ_ERR = "Ошибка при запросе к API: {url}"  # API_REQUEST_ERROR
    COORD_NF = "Координаты для страны '{country}' не найдены."  # COORDINATES_NOT_FOUND
    PLANES_NF = "В воздушном пространстве '{country}' самолёты не найдены."  # NO_AEROPLANES_FOUND
    PLANES_OK = "Успешно получены данные о самолётах для '{country}'."  # SUCCESS_AEROPLANES


class ErrorMsg:  # Сообщения об ошибках
    COMPARE_ERR = "Сравнивать можно только объекты Aeroplane"
