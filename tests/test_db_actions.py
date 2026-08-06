from unittest.mock import patch

from src.interaction.db_actions import run_db_analytics


@patch("src.interaction.db_actions.get_db_config")
@patch("src.interaction.db_actions.DBManager")
def test_run_db_analytics_menu(mock_manager, mock_config):
    """Тест интерактивного меню аналитики базы данных."""
    mock_config.return_value = {}
    mock_inst = mock_manager.return_value
    mock_inst.get_countries_and_aeroplanes_count.return_value = [("Fiji", 1)]
    mock_inst.get_all_aeroplanes.return_value = [("i1", "AFL", 200)]
    mock_inst.get_avg_speed.return_value = 200.0
    mock_inst.get_aeroplanes_with_higher_speed.return_value = [("i1", "AFL", 250)]
    mock_inst.get_aeroplanes_with_keyword.return_value = [("i1", "AFL", 250)]

    # Проверяем все пункты меню
    for choice in ["1", "2", "3", "0", "99"]:
        with patch("builtins.input", return_value=choice):
            run_db_analytics()
