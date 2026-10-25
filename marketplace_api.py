"""Marketplace API, hosted by the same Flask process as the Cow QR app."""

from __future__ import annotations

import base64
import hashlib
import hmac
import io
import json
import os
import secrets
import threading
import time
from functools import wraps
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

import bcrypt
from flask import Blueprint, current_app, g, jsonify, request
from werkzeug.security import check_password_hash, generate_password_hash
from PIL import Image, UnidentifiedImageError
from werkzeug.utils import secure_filename


marketplace_api = Blueprint("marketplace_api", __name__)
# app.py imports this module before it calls load_dotenv(); load .env here too (it never overrides
# real environment variables) so DATA_DIR means the same thing in both places.
from dotenv import load_dotenv
load_dotenv()

# DATA_DIR (optional, e.g. a Render Disk) moves the marketplace data and photos onto persistent storage.
# The photos stay under <DATA_DIR>/uploads so the existing /uploads/... route keeps serving them.
_STORAGE_ROOT = Path(os.environ.get("DATA_DIR", "").strip() or Path(__file__).resolve().parent)
DATA_FILE = _STORAGE_ROOT / "server" / "data.json"
UPLOAD_FOLDER = _STORAGE_ROOT / "uploads" / "marketplace"
DATA_LOCK = threading.RLock()
ALLOWED_UPLOAD_EXTENSIONS = {"jpg", "jpeg", "png", "webp"}
MAX_UPLOAD_BYTES = 5 * 1024 * 1024
MAX_UPLOAD_PIXELS = 25_000_000


def _load_data():
    DATA_FILE.parent.mkdir(parents=True, exist_ok=True)
    if not DATA_FILE.exists():
        return {"users": [], "products": []}
    with DATA_FILE.open("r", encoding="utf-8") as data_file:
        data = json.load(data_file)
    if not isinstance(data, dict):
        raise ValueError("Marketplace data must be a JSON object.")
    data.setdefault("users", [])
    data.setdefault("products", [])
    return data


def _save_data(data):
    DATA_FILE.parent.mkdir(parents=True, exist_ok=True)
    temporary_file = DATA_FILE.with_suffix(".json.tmp")
    with temporary_file.open("w", encoding="utf-8") as data_file:
        json.dump(data, data_file, ensure_ascii=False, indent=2)
        data_file.flush()
        os.fsync(data_file.fileno())
    os.replace(temporary_file, DATA_FILE)


def _b64url(value):
    return base64.urlsafe_b64encode(value).rstrip(b"=").decode("ascii")


def _jwt_secret():
    configured = os.environ.get("MARKETPLACE_JWT_SECRET")
    return (configured or current_app.secret_key).encode("utf-8")


def _create_token(user):
    now = int(time.time())
    header = _b64url(json.dumps({"alg": "HS256", "typ": "JWT"}, separators=(",", ":")).encode())
    payload = _b64url(
        json.dumps(
            {"id": user["id"], "email": user["email"], "iat": now, "exp": now + 7200},
            separators=(",", ":"),
        ).encode()
    )
    unsigned = f"{header}.{payload}"
    signature = hmac.new(_jwt_secret(), unsigned.encode(), hashlib.sha256).digest()
    return f"{unsigned}.{_b64url(signature)}"


def _read_token(token):
    try:
        header, payload, signature = token.split(".")
        unsigned = f"{header}.{payload}"
        expected = _b64url(hmac.new(_jwt_secret(), unsigned.encode(), hashlib.sha256).digest())
        if not hmac.compare_digest(signature, expected):
            return None
        claims = json.loads(base64.urlsafe_b64decode(payload + "=" * (-len(payload) % 4)))
        if claims.get("exp", 0) <= int(time.time()):
            return None
        return claims
    except (ValueError, TypeError, json.JSONDecodeError):
        return None


def _authenticated(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        authorization = request.headers.get("Authorization", "")
        scheme, _, token = authorization.partition(" ")
        if scheme.lower() != "bearer" or not token:
            return jsonify(error="No token"), 401
        user = _read_token(token)
        if not user:
            return jsonify(error="Invalid token"), 403
        g.marketplace_user = user
        return view(*args, **kwargs)

    return wrapped


def _normalize_images(images):
    if isinstance(images, str):
        try:
            images = json.loads(images)
        except json.JSONDecodeError:
            images = []
    return images if isinstance(images, list) else []


@marketplace_api.post("/api/auth/signup")
def signup():
    body = request.get_json(silent=True) or {}
    email = str(body.get("email", "")).strip().lower()
    password = str(body.get("password", ""))
    if not email or "@" not in email or len(password) < 6:
        return jsonify(error="Enter a valid email and a password with at least 6 characters."), 400

    try:
        with DATA_LOCK:
            data = _load_data()
            if any(str(user.get("email", "")).lower() == email for user in data["users"]):
                return jsonify(error="User already exists"), 400
            next_id = max((int(user.get("id", 0)) for user in data["users"]), default=0) + 1
            user = {
                "id": int(time.time() * 1000) + next_id,
                "email": email,
                "passwordHash": bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("ascii"),
                "createdAt": int(time.time() * 1000),
            }
            data["users"].append(user)
            _save_data(data)
        return jsonify(message="User created", token=_create_token(user))
    except Exception:
        current_app.logger.exception("Marketplace signup failed")
        return jsonify(error="Signup failed"), 500


@marketplace_api.post("/api/auth/login")
def login():
    body = request.get_json(silent=True) or {}
    email = str(body.get("email", "")).strip().lower()
    password = str(body.get("password", ""))
    try:
        with DATA_LOCK:
            data = _load_data()
            user = next(
                (entry for entry in data["users"] if str(entry.get("email", "")).lower() == email),
                None,
            )
        if not user:
            return jsonify(error="Invalid credentials"), 400

        stored_hash = str(user.get("passwordHash", ""))
        try:
            if stored_hash.startswith(("$2a$", "$2b$", "$2y$")):
                valid = bcrypt.checkpw(password.encode("utf-8"), stored_hash.encode("ascii"))
            else:
                valid = check_password_hash(stored_hash, password)
        except (ValueError, TypeError):
            valid = False
        if not valid:
            return jsonify(error="Invalid credentials"), 400
        return jsonify(token=_create_token(user))
    except Exception:
        current_app.logger.exception("Marketplace login failed")
        return jsonify(error="Login failed"), 500


@marketplace_api.get("/api/products")
def list_products():
    try:
        with DATA_LOCK:
            data = _load_data()
        products = sorted(
            data["products"],
            key=lambda item: int(item.get("createdAt", 0) or 0),
            reverse=True,
        )
        for product in products:
            product["images"] = _normalize_images(product.get("images", []))
        return jsonify(products)
    except Exception:
        current_app.logger.exception("Marketplace product listing failed")
        return jsonify(error="Failed to fetch products"), 500


@marketplace_api.post("/api/products")
@_authenticated
def create_product():
    body = request.get_json(silent=True) or {}
    title = str(body.get("title", "")).strip()
    images = _normalize_images(body.get("images", []))
    if not title:
        return jsonify(error="A product title is required"), 400
    if not images:
        return jsonify(error="No images provided"), 400

    try:
        with DATA_LOCK:
            data = _load_data()
            next_id = max((int(item.get("id", 0)) for item in data["products"]), default=0) + 1
            product = {
                "id": int(time.time() * 1000) + next_id,
                "ownerId": g.marketplace_user["id"],
                "title": title,
                "category": str(body.get("category", "Others")),
                "price": body.get("price", 0),
                "description": str(body.get("description", "")),
                "images": images,
                "seller": str(body.get("seller", g.marketplace_user.get("email", ""))),
                "createdAt": int(time.time() * 1000),
            }
            data["products"].append(product)
            _save_data(data)
        return jsonify(message="Product added", product=product)
    except Exception:
        current_app.logger.exception("Marketplace product creation failed")
        return jsonify(error="Failed to add product"), 500


@marketplace_api.delete("/api/products/<int:product_id>")
@_authenticated
def delete_product(product_id):
    try:
        with DATA_LOCK:
            data = _load_data()
            product = next(
                (item for item in data["products"] if int(item.get("id", 0)) == product_id),
                None,
            )
            if not product:
                return jsonify(error="Listing not found"), 404
            if str(product.get("ownerId")) != str(g.marketplace_user["id"]):
                return jsonify(error="You can only remove your own listings"), 403
            data["products"].remove(product)
            _save_data(data)
        return jsonify(success=True)
    except Exception:
        current_app.logger.exception("Marketplace product deletion failed")
        return jsonify(error="Failed to delete product"), 500


@marketplace_api.post("/upload")
@_authenticated
def upload_image():
    image = request.files.get("image")
    if not image or not image.filename:
        return jsonify(error="No file uploaded"), 400
    filename = secure_filename(image.filename)
    if "." not in filename or filename.rsplit(".", 1)[1].lower() not in ALLOWED_UPLOAD_EXTENSIONS:
        return jsonify(error="Upload a JPG, PNG, or WebP image."), 400

    # Check the real content, not just the extension: size, that it decodes as an image, and that
    # the format matches the extension (so a script renamed to .png is rejected).
    data = image.stream.read(MAX_UPLOAD_BYTES + 1)
    if not data:
        return jsonify(error="The uploaded file is empty."), 400
    if len(data) > MAX_UPLOAD_BYTES:
        return jsonify(error="Images must be 5 MB or smaller."), 413
    extension = filename.rsplit(".", 1)[1].lower()
    try:
        with Image.open(io.BytesIO(data)) as probe:
            detected = (probe.format or "").upper()
            width, height = probe.size
            probe.verify()
    except (UnidentifiedImageError, OSError, SyntaxError, ValueError, Image.DecompressionBombError):
        return jsonify(error="That file is not a valid image."), 400
    expected = {"jpg": "JPEG", "jpeg": "JPEG", "png": "PNG", "webp": "WEBP"}[extension]
    if detected != expected:
        return jsonify(error="The file content does not match its extension."), 400
    if width * height > MAX_UPLOAD_PIXELS:
        return jsonify(error="Image dimensions are too large."), 400

    UPLOAD_FOLDER.mkdir(parents=True, exist_ok=True)
    saved_name = f"{secrets.token_hex(16)}.{extension}"
    (UPLOAD_FOLDER / saved_name).write_bytes(data)
    return jsonify(filePath=f"/uploads/marketplace/{saved_name}")


WEATHER_GEOCODING_URL = os.environ.get("WEATHER_GEOCODING_URL", "https://geocoding-api.open-meteo.com/v1/search")
WEATHER_FORECAST_URL = os.environ.get("WEATHER_FORECAST_URL", "https://api.open-meteo.com/v1/forecast")
WEATHER_CACHE_SECONDS = 600
_WEATHER_CACHE = {}
_WEATHER_CACHE_LOCK = threading.Lock()


class WeatherServiceError(Exception):
    """The weather provider could not be reached or answered with something unusable."""


def _weather_ssl_context():
    """Use certifi's CA bundle when available (python.org builds for macOS ship without root certificates)."""
    import ssl
    try:
        import certifi
        return ssl.create_default_context(cafile=certifi.where())
    except Exception:  # certifi missing: fall back to the system store
        return ssl.create_default_context()


def _request_weather_json(url):
    """GET a JSON document, retrying once on a timeout, network error or provider 5xx/429."""
    last_error = None
    for attempt in range(2):
        weather_request = Request(url, headers={"User-Agent": "KisanSaathiFarmTools/1.0", "Accept": "application/json"})
        try:
            with urlopen(weather_request, timeout=8, context=_weather_ssl_context()) as response:
                return json.loads(response.read().decode("utf-8"))
        except HTTPError as error:
            last_error = error
            if error.code not in (429, 500, 502, 503, 504):
                raise
        except (URLError, TimeoutError, OSError) as error:
            last_error = error
        if attempt == 0:
            time.sleep(0.4)
    raise last_error


def _weather_cached(key, loader):
    now = time.time()
    with _WEATHER_CACHE_LOCK:
        hit = _WEATHER_CACHE.get(key)
        if hit and hit[0] > now:
            return hit[1]
    value = loader()
    with _WEATHER_CACHE_LOCK:
        if len(_WEATHER_CACHE) > 500:
            _WEATHER_CACHE.clear()
        _WEATHER_CACHE[key] = (now + WEATHER_CACHE_SECONDS, value)
    return value


def _geocode(name, language):
    url = WEATHER_GEOCODING_URL + "?" + urlencode({"name": name, "count": 10, "language": language, "format": "json"})
    return _request_weather_json(url).get("results") or []


def _find_location(query):
    """Resolve what the user typed ("Baramati", "Pune, India", "Rahuri, Maharashtra", "पुणे") to one place."""
    import re
    parts = [part.strip() for part in re.split(r"[,;|]", query) if part.strip()]
    name = parts[0] if parts else query.strip()
    hints = [hint.lower() for hint in parts[1:]]
    language = "mr" if re.search(r"[\u0900-\u097F]", name) else "en"
    candidates = _geocode(name, language)
    if not candidates and len(name.split()) > 1:
        candidates = _geocode(name.split()[0], language)           # "Baramati town" -> "Baramati"
    if not candidates and language == "mr":
        candidates = _geocode(name, "en")
    if not candidates:
        return None
    if hints:
        def matches(place):
            haystack = " ".join(str(place.get(k, "")) for k in ("admin1", "admin2", "admin3", "country", "country_code")).lower()
            return all(hint in haystack for hint in hints)
        narrowed = [place for place in candidates if matches(place)]
        candidates = narrowed or candidates
    best = candidates[0]
    if best.get("country_code") != "IN":
        same_name_in_india = [p for p in candidates
                              if p.get("country_code") == "IN" and str(p.get("name", "")).lower() == name.lower()]
        if same_name_in_india and not any(h in ("usa", "uk", "us", "united states") for h in hints):
            best = same_name_in_india[0]
    return best


def _weather_description(code):
    descriptions = {
        0: ("Clear", "clear sky"),
        1: ("Clear", "mainly clear"),
        2: ("Clouds", "partly cloudy"),
        3: ("Clouds", "overcast"),
        45: ("Fog", "fog"),
        48: ("Fog", "rime fog"),
        51: ("Drizzle", "light drizzle"),
        53: ("Drizzle", "moderate drizzle"),
        55: ("Drizzle", "dense drizzle"),
        56: ("Drizzle", "freezing drizzle"),
        57: ("Drizzle", "heavy freezing drizzle"),
        61: ("Rain", "light rain"),
        63: ("Rain", "moderate rain"),
        65: ("Rain", "heavy rain"),
        66: ("Rain", "freezing rain"),
        67: ("Rain", "heavy freezing rain"),
        71: ("Snow", "light snow"),
        73: ("Snow", "moderate snow"),
        75: ("Snow", "heavy snow"),
        77: ("Snow", "snow grains"),
        80: ("Rain", "light rain showers"),
        81: ("Rain", "moderate rain showers"),
        82: ("Rain", "heavy rain showers"),
        85: ("Snow", "snow showers"),
        86: ("Snow", "heavy snow showers"),
        95: ("Thunderstorm", "thunderstorm"),
        96: ("Thunderstorm", "thunderstorm with hail"),
        99: ("Thunderstorm", "heavy thunderstorm with hail"),
    }
    return descriptions.get(int(code or 0), ("Clouds", "variable conditions"))


COMPASS_POINTS = ["N", "NNE", "NE", "ENE", "E", "ESE", "SE", "SSE", "S", "SSW", "SW", "WSW", "W", "WNW", "NW", "NNW"]
MORNING_HOURS = range(6, 10)       # 06:00-09:59 local time
AFTERNOON_HOURS = range(13, 17)    # 13:00-16:59 local time (usually the driest part of the day)


def _number(value):
    return value if isinstance(value, (int, float)) and not isinstance(value, bool) else None


def _rounded(value, digits=1):
    return None if _number(value) is None else round(value, digits)


def _compass(degrees):
    """16-point compass name for a bearing in degrees (the direction the wind blows FROM)."""
    if _number(degrees) is None:
        return None
    return COMPASS_POINTS[int((degrees % 360) / 22.5 + 0.5) % 16]


def _kmh_to_ms(value):
    return None if _number(value) is None else round(value / 3.6, 1)


def _at(series, index):
    """Item `index` of an optional provider list, or None when the list or value is missing."""
    if not isinstance(series, list) or index >= len(series):
        return None
    return _number(series[index])


def _hourly_mean(hourly, key, day, hours):
    times, values = hourly.get("time") or [], hourly.get(key) or []
    picked = [
        value for stamp, value in zip(times, values)
        if isinstance(stamp, str) and stamp.startswith(day) and len(stamp) >= 13
        and stamp[11:13].isdigit() and int(stamp[11:13]) in hours and _number(value) is not None
    ]
    return round(sum(picked) / len(picked)) if picked else None


def _today_key(current, forecast_data):
    stamp = str(current.get("time") or "")[:10]
    if stamp:
        return stamp
    days = (forecast_data.get("daily") or {}).get("time") or []
    return str(days[0]) if days else ""


def _farm_day(forecast_data, index, day):
    """Wind, rain, humidity and evapotranspiration for one forecast day (any value may be None)."""
    daily = forecast_data.get("daily") or {}
    hourly = forecast_data.get("hourly") or {}
    degrees = _at(daily.get("wind_direction_10m_dominant"), index)
    return {
        "rain": {
            "chance_percent": _at(daily.get("precipitation_probability_max"), index),
            "amount_mm": _rounded(_at(daily.get("precipitation_sum"), index)),
        },
        "wind": {
            "speed_max": _kmh_to_ms(_at(daily.get("wind_speed_10m_max"), index)),
            "gust_max": _kmh_to_ms(_at(daily.get("wind_gusts_10m_max"), index)),
            "degrees": degrees,
            "direction": _compass(degrees),
        },
        "humidity": {
            "morning": _hourly_mean(hourly, "relative_humidity_2m", day, MORNING_HOURS),
            "afternoon": _hourly_mean(hourly, "relative_humidity_2m", day, AFTERNOON_HOURS),
        },
        "et0_mm": _rounded(_at(daily.get("et0_fao_evapotranspiration"), index)),
    }


def _weather_data(endpoint):
    city = " ".join(request.args.get("city", "").split())
    if not city:
        return jsonify(error="Enter a city or town."), 400
    if len(city) > 100:
        return jsonify(error="That place name is too long."), 400

    try:
        location = _weather_cached(("place", city.lower()), lambda: _find_location(city))
        if not location:
            return jsonify(error="City not found. Check the spelling and try again."), 404

        params = {
            "latitude": location["latitude"],
            "longitude": location["longitude"],
            "current": "temperature_2m,relative_humidity_2m,apparent_temperature,weather_code,wind_speed_10m,"
                       "wind_direction_10m,wind_gusts_10m,precipitation",
            "daily": "weather_code,temperature_2m_max,temperature_2m_min,precipitation_probability_max,precipitation_sum,"
                     "wind_speed_10m_max,wind_gusts_10m_max,wind_direction_10m_dominant,et0_fao_evapotranspiration",
            "hourly": "relative_humidity_2m",
            "forecast_days": 5,
            "timezone": "auto",
        }
        forecast_data = _weather_cached(
            ("forecast", round(float(location["latitude"]), 3), round(float(location["longitude"]), 3)),
            lambda: _request_weather_json(WEATHER_FORECAST_URL + "?" + urlencode(params)),
        )
        if endpoint == "weather":
            current = forecast_data["current"]
            condition, description = _weather_description(current["weather_code"])
            return jsonify(
                {
                    "name": location["name"],
                    "region": ", ".join(str(location[k]) for k in ("admin1", "country") if location.get(k)),
                    "main": {
                        "temp": current["temperature_2m"],
                        "humidity": current["relative_humidity_2m"],
                        "feels_like": current["apparent_temperature"],
                    },
                    "weather": [{"main": condition, "description": description}],
                    "wind": {"speed": round(current["wind_speed_10m"] / 3.6, 1)},
                    "farm": {
                        "now": {
                            "wind_speed": _kmh_to_ms(current.get("wind_speed_10m")),
                            "wind_gust": _kmh_to_ms(current.get("wind_gusts_10m")),
                            "wind_degrees": _number(current.get("wind_direction_10m")),
                            "wind_direction": _compass(current.get("wind_direction_10m")),
                            "rain_mm": _rounded(current.get("precipitation")),
                            "humidity": _number(current.get("relative_humidity_2m")),
                        },
                        "today": _farm_day(forecast_data, 0, _today_key(current, forecast_data)),
                    },
                }
            )

        daily = forecast_data["daily"]
        forecast = []
        for index, forecast_date in enumerate(daily["time"]):
            condition, description = _weather_description(daily["weather_code"][index])
            forecast.append(
                {
                    "dt_txt": f"{forecast_date} 12:00:00",
                    "main": {
                        "temp_min": daily["temperature_2m_min"][index],
                        "temp_max": daily["temperature_2m_max"][index],
                    },
                    "weather": [{"main": condition, "description": description}],
                    "pop": None if _at(daily.get("precipitation_probability_max"), index) is None
                    else _at(daily.get("precipitation_probability_max"), index) / 100,
                    "farm": _farm_day(forecast_data, index, forecast_date),
                }
            )
        return jsonify({"list": forecast})
    except HTTPError as error:
        current_app.logger.warning("Weather provider returned HTTP %s", error.code)
        return jsonify(error="The weather service did not accept the request. Please try again in a minute."), 502
    except (URLError, TimeoutError, OSError) as error:
        current_app.logger.warning("Weather provider unreachable: %s", error)
        return jsonify(error="Could not reach the weather service. Check the internet connection of the server and try again."), 502
    except (json.JSONDecodeError, UnicodeDecodeError, KeyError, IndexError, TypeError, ValueError):
        return jsonify(error="The weather service returned an unreadable response."), 502


@marketplace_api.get("/api/weather/current")
def current_weather():
    return _weather_data("weather")


@marketplace_api.get("/api/weather/forecast")
def weather_forecast():
    return _weather_data("forecast")
