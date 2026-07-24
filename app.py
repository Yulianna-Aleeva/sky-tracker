from flask import Flask, render_template, request

from src.api.api_adapter import ApiAdapter
from src.classes.aeroplane import Aeroplane
from src.config import USER_SETTINGS

app = Flask(__name__)
api = ApiAdapter()


def _load_planes(country: str) -> list[Aeroplane]:
    """Загружает самолёты по стране через API."""
    raw = api.get_aeroplanes(country) or []
    return Aeroplane.cast_to_object_list(raw)


@app.route("/", methods=["GET"])
def index() -> str:
    """Главная: форма выбора страны."""
    return render_template("index.html", countries=USER_SETTINGS.get("user_countries", []))


@app.route("/planes", methods=["POST"])
def planes() -> str:
    """Список самолётов по выбранной или введённой стране."""
    country = request.form.get("country", "").strip()
    if country == "__custom__":
        country = request.form.get("custom_country", "").strip()
    planes = _load_planes(country)
    return render_template("planes.html", country=country, planes=planes)


@app.route("/planes_back", methods=["GET"])
def planes_back() -> str:
    """Возврат к списку самолётов по country из query."""
    country = request.args.get("country", "").strip()
    planes = _load_planes(country)
    return render_template("planes.html", country=country, planes=planes)


@app.route("/leaders", methods=["GET"])
def leaders() -> str:
    """Топ-лидеры: быстрый / высокий / крутой."""
    country = request.args.get("country", "").strip()
    planes = _load_planes(country)
    leaders_data = None
    if planes:
        leaders_data = {
            "fastest": max(planes, key=lambda p: p.velocity if p.velocity is not None else -1),
            "highest": max(planes, key=lambda p: p.baro_altitude if p.baro_altitude is not None else -1),
            "steepest": max(planes, key=lambda p: p.vertical_rate if p.vertical_rate is not None else -1),
        }
    return render_template("leaders.html", country=country, leaders=leaders_data)


if __name__ == "__main__":
    app.run(debug=True)
