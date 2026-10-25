"""Weather search (/api/weather/current and /forecast) against a local stand-in for the Open-Meteo service."""
import json
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import parse_qs, urlparse

import pytest

import app
import marketplace_api

PLACES = {
    "pune": [{"name": "Pune", "latitude": 18.5196, "longitude": 73.8553, "country_code": "IN", "country": "India", "admin1": "Maharashtra"}],
    "पुणे": [{"name": "पुणे", "latitude": 18.5196, "longitude": 73.8553, "country_code": "IN", "country": "India", "admin1": "Maharashtra"}],
    "baramati": [{"name": "Baramati", "latitude": 18.15, "longitude": 74.58, "country_code": "IN", "country": "India", "admin1": "Maharashtra"}],
    "aurangabad": [
        {"name": "Aurangabad", "latitude": 19.88, "longitude": 75.32, "country_code": "IN", "country": "India", "admin1": "Maharashtra"},
        {"name": "Aurangabad", "latitude": 24.76, "longitude": 84.37, "country_code": "IN", "country": "India", "admin1": "Bihar"}],
    "hyderabad": [
        {"name": "Hyderabad", "latitude": 25.39, "longitude": 68.37, "country_code": "PK", "country": "Pakistan", "admin1": "Sindh"},
        {"name": "Hyderabad", "latitude": 17.38, "longitude": 78.48, "country_code": "IN", "country": "India", "admin1": "Telangana"}],
}
def _hourly_humidity():
    times, values = [], []
    for day in range(14, 19):
        for hour in range(24):
            times.append(f"2026-10-{day}T{hour:02d}:00")
            values.append({6: 82, 7: 84, 8: 80, 9: 78, 13: 42, 14: 40, 15: 38, 16: 40}.get(hour, 60))
    return {"time": times, "relative_humidity_2m": values}


FORECAST = {
    "current": {"time": "2026-10-14T11:30", "temperature_2m": 29.4, "relative_humidity_2m": 61, "apparent_temperature": 31.2,
                "weather_code": 2, "wind_speed_10m": 10.8, "wind_direction_10m": 315, "wind_gusts_10m": 25.2, "precipitation": 0.2},
    "daily": {"time": [f"2026-10-{14 + i}" for i in range(5)], "weather_code": [0, 1, 3, 61, 95],
              "temperature_2m_max": [31, 32, 30, 28, 27], "temperature_2m_min": [20, 21, 20, 19, 19],
              "precipitation_probability_max": [10, 20, 55, 80, 90], "precipitation_sum": [0, 0.4, 2.2, 9.5, 18.25],
              "wind_speed_10m_max": [18, 22, 14.4, 30.6, 36], "wind_gusts_10m_max": [32.4, 40, 28.8, 50, 61],
              "wind_direction_10m_dominant": [315, 270, 90, 180, 22],
              "et0_fao_evapotranspiration": [5.43, 6.1, 4.2, 2.04, 1.0]},
    "hourly": _hourly_humidity(),
}


class Provider(BaseHTTPRequestHandler):
    mode = "ok"
    hits = []
    failures_left = 0

    def log_message(self, *args):
        pass

    def do_GET(self):
        url = urlparse(self.path)
        query = parse_qs(url.query)
        Provider.hits.append((url.path, query.get("name", [""])[0], query.get("language", [""])[0]))
        if Provider.mode == "down" or (Provider.failures_left > 0 and not setattr(Provider, "failures_left", Provider.failures_left - 1)):
            self.send_response(500); self.end_headers(); return
        if Provider.mode == "garbage":
            body = b"<html>not json</html>"
        elif url.path.endswith("/search"):
            name = query.get("name", [""])[0]
            results = PLACES.get(name.lower() if name.isascii() else name, [])
            body = json.dumps({"results": results} if results else {"generationtime_ms": 0.2}).encode()
        else:
            body = json.dumps(FORECAST).encode()
        self.send_response(200); self.send_header("Content-Type", "application/json"); self.end_headers(); self.wfile.write(body)


@pytest.fixture()
def provider(monkeypatch):
    server = HTTPServer(("127.0.0.1", 0), Provider)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    base = f"http://127.0.0.1:{server.server_port}"
    monkeypatch.setattr(marketplace_api, "WEATHER_GEOCODING_URL", base + "/v1/search")
    monkeypatch.setattr(marketplace_api, "WEATHER_FORECAST_URL", base + "/v1/forecast")
    monkeypatch.setattr(marketplace_api.time, "sleep", lambda s: None)
    marketplace_api._WEATHER_CACHE.clear()
    Provider.mode, Provider.hits, Provider.failures_left = "ok", [], 0
    yield server
    server.shutdown()
    marketplace_api._WEATHER_CACHE.clear()


def _get(path, city):
    return app.app.test_client().get(path, query_string={"city": city})


def test_current_weather_and_five_day_forecast_for_a_city(provider):
    current = _get("/api/weather/current", "Pune")
    assert current.status_code == 200
    body = current.get_json()
    assert body["name"] == "Pune" and body["region"] == "Maharashtra, India"
    assert body["main"] == {"temp": 29.4, "humidity": 61, "feels_like": 31.2}
    assert body["weather"][0]["description"] == "partly cloudy" and body["wind"]["speed"] == 3.0
    forecast = _get("/api/weather/forecast", "Pune").get_json()["list"]
    assert len(forecast) == 5 and forecast[0]["dt_txt"] == "2026-10-14 12:00:00"
    assert forecast[3]["weather"][0]["description"] == "light rain" and forecast[0]["main"] == {"temp_min": 20, "temp_max": 31}


@pytest.mark.parametrize("typed, expected", [
    ("pune", "Pune"), ("  PUNE  ", "Pune"), ("Pune, India", "Pune"), ("Pune,Maharashtra", "Pune"),
    ("Baramati town", "Baramati"), ("Baramati, Maharashtra", "Baramati"), ("पुणे", "पुणे"),
])
def test_towns_typed_in_common_ways_are_found(provider, typed, expected):
    response = _get("/api/weather/current", typed)
    assert response.status_code == 200 and response.get_json()["name"] == expected


def test_ambiguous_names_prefer_the_indian_place_and_respect_a_state_hint(provider):
    assert _get("/api/weather/current", "Hyderabad").get_json()["region"] == "Telangana, India"
    assert _get("/api/weather/current", "Aurangabad, Bihar").get_json()["region"] == "Bihar, India"
    assert _get("/api/weather/current", "Aurangabad").get_json()["region"] == "Maharashtra, India"


def test_unknown_place_and_empty_input_give_clear_messages(provider):
    missing = _get("/api/weather/current", "Nowheresville")
    assert missing.status_code == 404 and "not found" in missing.get_json()["error"].lower()
    assert _get("/api/weather/current", "   ").status_code == 400
    assert _get("/api/weather/current", "x" * 200).status_code == 400


def test_marathi_name_is_looked_up_with_the_marathi_language(provider):
    assert _get("/api/weather/current", "पुणे").status_code == 200
    assert ("/v1/search", "पुणे", "mr") in Provider.hits


def test_one_provider_hiccup_is_retried_and_results_are_cached(provider):
    Provider.failures_left = 1
    assert _get("/api/weather/current", "Pune").status_code == 200
    hits_after_first = len(Provider.hits)
    assert _get("/api/weather/forecast", "Pune").status_code == 200       # the forecast tab reuses the cached lookup
    assert len(Provider.hits) == hits_after_first


def test_provider_outages_return_readable_errors_not_blank_pages(provider, monkeypatch):
    Provider.mode = "down"
    down = _get("/api/weather/current", "Pune")
    assert down.status_code == 502 and "weather service" in down.get_json()["error"]
    marketplace_api._WEATHER_CACHE.clear()
    Provider.mode = "garbage"
    assert _get("/api/weather/current", "Pune").status_code == 502
    marketplace_api._WEATHER_CACHE.clear()
    monkeypatch.setattr(marketplace_api, "WEATHER_GEOCODING_URL", "http://127.0.0.1:1/v1/search")      # nothing listens here
    unreachable = _get("/api/weather/current", "Pune")
    assert unreachable.status_code == 502 and "Could not reach the weather service" in unreachable.get_json()["error"]


def test_certificate_bundle_is_used_when_available():
    import ssl
    context = marketplace_api._weather_ssl_context()
    assert isinstance(context, ssl.SSLContext) and context.verify_mode == ssl.CERT_REQUIRED


def test_farm_conditions_for_today_wind_rain_humidity_and_evapotranspiration(provider):
    farm = _get("/api/weather/current", "Pune").get_json()["farm"]
    assert farm["now"] == {"wind_speed": 3.0, "wind_gust": 7.0, "wind_degrees": 315, "wind_direction": "NW",
                           "rain_mm": 0.2, "humidity": 61}
    today = farm["today"]
    assert today["humidity"] == {"morning": 81, "afternoon": 40}                       # mean of 06-09 h and 13-16 h
    assert today["rain"] == {"chance_percent": 10, "amount_mm": 0}
    assert today["wind"] == {"speed_max": 5.0, "gust_max": 9.0, "degrees": 315, "direction": "NW"}
    assert today["et0_mm"] == 5.4


def test_forecast_days_carry_rain_chance_wind_humidity_and_et0(provider):
    days = _get("/api/weather/forecast", "Pune").get_json()["list"]
    assert [d["farm"]["rain"]["chance_percent"] for d in days] == [10, 20, 55, 80, 90]
    assert days[4]["pop"] == 0.9 and days[4]["farm"]["rain"]["amount_mm"] == 18.2
    assert [d["farm"]["wind"]["direction"] for d in days] == ["NW", "W", "E", "S", "NNE"]
    assert [d["farm"]["et0_mm"] for d in days] == [5.4, 6.1, 4.2, 2.0, 1.0]
    assert all(d["farm"]["humidity"] == {"morning": 81, "afternoon": 40} for d in days)
    assert days[0]["main"] == {"temp_min": 20, "temp_max": 31}                         # existing fields unchanged


def test_compass_points_cover_the_full_circle():
    names = {0: "N", 11: "N", 12: "NNE", 22: "NNE", 45: "NE", 90: "E", 135: "SE", 180: "S", 225: "SW", 270: "W", 315: "NW", 337: "NNW", 349: "N", 360: "N"}
    for degrees, expected in names.items():
        assert marketplace_api._compass(degrees) == expected, degrees
    assert marketplace_api._compass(None) is None


def test_missing_optional_provider_fields_do_not_break_the_weather(provider, monkeypatch):
    """An older / partial provider answer still gives the original weather, with empty farm values."""
    trimmed = {"current": {k: v for k, v in FORECAST["current"].items() if k in
                           ("temperature_2m", "relative_humidity_2m", "apparent_temperature", "weather_code", "wind_speed_10m")},
               "daily": {k: v for k, v in FORECAST["daily"].items() if k in
                         ("time", "weather_code", "temperature_2m_max", "temperature_2m_min")}}
    monkeypatch.setitem(tw_globals(), "FORECAST", trimmed)
    current = _get("/api/weather/current", "Pune")
    assert current.status_code == 200
    body = current.get_json()
    assert body["main"]["temp"] == 29.4 and body["wind"]["speed"] == 3.0
    assert body["farm"]["today"]["humidity"] == {"morning": None, "afternoon": None}
    assert body["farm"]["now"]["wind_direction"] is None and body["farm"]["today"]["et0_mm"] is None
    days = _get("/api/weather/forecast", "Pune").get_json()["list"]
    assert len(days) == 5 and days[0]["pop"] is None and days[0]["farm"]["rain"]["chance_percent"] is None


def tw_globals():
    return globals()
