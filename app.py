from flask import Flask, render_template, request

from src.api.api_adapter import ApiAdapter
from src.classes.aeroplane import Aeroplane
from src.config import USER_SETTINGS

app = Flask(__name__)
api = ApiAdapter()


@app.route("/", methods=["GET"])
def index() -> str:
    """Главная: форма выбора страны."""
    return render_template("index.html", countries=USER_SETTINGS.get("user_countries", []))


@app.route("/planes", methods=["POST"])
def planes() -> str:
    """Список самолётов по выбранной стране."""
    country = request.form.get("country", "").strip()
    raw = api.get_aeroplanes(country) or []
    planes = Aeroplane.cast_to_object_list(raw)
    return render_template("planes.html", country=country, planes=planes)


if __name__ == "__main__":
    app.run(debug=True)
