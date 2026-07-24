import os

from dotenv import load_dotenv
from flask import Flask, render_template, request
from flask.typing import ResponseReturnValue

from src.api.api_adapter import ApiAdapter
from src.classes.aeroplane import Aeroplane
from src.config import USER_SETTINGS

app = Flask(__name__)
api = ApiAdapter()

load_dotenv()

OPENSKY_USER = os.getenv("OPENSKY_USER")
OPENSKY_PASS = os.getenv("OPENSKY_PASS")


def _load_planes(country: str) -> list[Aeroplane]:
    """Загружает самолёты по стране через API."""
    raw = api.get_aeroplanes(country) or []
    # Если API требует авторизацию, нужно обновить ApiAdapter
    return Aeroplane.cast_to_object_list(raw)


@app.route("/", methods=["GET"])
def index() -> ResponseReturnValue:
    """Главная: форма выбора страны."""
    return render_template("index.html", countries=USER_SETTINGS.get("user_countries", []))


@app.route("/planes", methods=["POST"])
def planes() -> ResponseReturnValue:
    """Список самолётов по выбранной или введённой стране."""
    country = request.form.get("country", "").strip()
    if country == "__custom__":
        country = request.form.get("custom_country", "").strip()
    planes = _load_planes(country)
    return render_template("planes.html", country=country, planes=planes)


@app.route("/planes_back", methods=["GET"])
def planes_back() -> ResponseReturnValue:
    """Возврат к списку самолётов по country из query."""
    country = request.args.get("country", "").strip()
    planes = _load_planes(country)
    return render_template("planes.html", country=country, planes=planes)


@app.route("/leaders", methods=["GET"])
def leaders() -> ResponseReturnValue:
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


@app.route("/filter", methods=["GET"])
def filter_country() -> ResponseReturnValue:
    """Фильтр самолётов по стране регистрации (origin_country)."""
    country = request.args.get("country", "").strip()
    reg = request.args.get("reg", "").strip()
    planes = _load_planes(country)

    filtered = None
    if reg:
        filtered = [p for p in planes if p.origin_country and p.origin_country.lower() == reg.lower()]

    return render_template(
        "filter.html",
        country=country,
        reg=reg,
        planes=filtered,
    )


@app.route("/top-altitude", methods=["GET"])
def top_altitude() -> ResponseReturnValue:
    """Топ-N самолётов по высоте (DESC)."""
    country = request.args.get("country", "").strip()
    n = request.args.get("n", type=int)
    planes = _load_planes(country)

    top = None
    if n and n > 0:
        top = sorted(
            planes,
            key=lambda p: p.baro_altitude if p.baro_altitude is not None else -1,
            reverse=True,
        )[:n]

    return render_template("top.html", country=country, n=n, planes=top, mode="altitude")


@app.route("/top-velocity", methods=["GET"])
def top_velocity() -> ResponseReturnValue:
    """Топ-N самолётов по скорости (DESC)."""
    country = request.args.get("country", "").strip()
    n = request.args.get("n", type=int)
    planes = _load_planes(country)

    top = None
    if n and n > 0:
        top = sorted(
            planes,
            key=lambda p: p.velocity if p.velocity is not None else -1,
            reverse=True,
        )[:n]

    return render_template("top.html", country=country, n=n, planes=top, mode="velocity")


@app.route("/stats/<mode>", methods=["GET"])
def stats(mode: str) -> ResponseReturnValue:
    """Статистика: in_air / on_ground / spi."""
    country = request.args.get("country", "").strip()
    planes = _load_planes(country)

    modes = {
        "in_air": ("В воздухе", lambda p: not p.on_ground),
        "on_ground": ("На земле", lambda p: p.on_ground),
        "spi": ("Спецрейсы (SPI)", lambda p: p.spi),
    }
    label, check = modes.get(mode, ("Неизвестно", lambda p: False))

    filtered = [p for p in planes if check(p)]
    total = len(planes)
    count = len(filtered)
    percent = (count / total * 100) if total else 0

    return render_template(
        "stats.html",
        country=country,
        label=label,
        count=count,
        total=total,
        percent=percent,
        planes=filtered,
    )


if __name__ == "__main__":
    app.run(debug=True)
