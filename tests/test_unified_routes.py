import io
import json

from PIL import Image

import app
import marketplace_api


def _png_bytes(size=(8, 8)):
    buffer = io.BytesIO()
    Image.new("RGB", size, (30, 140, 60)).save(buffer, format="PNG")
    return buffer.getvalue()


def test_cow_and_kisaath_pages_share_one_flask_origin():
    client = app.app.test_client()

    home = client.get("/")
    assert home.status_code == 200
    assert b"Every animal accounted for" in home.data
    assert b"/kisaath/" in home.data

    kisaath = client.get("/kisaath/weather")
    assert kisaath.status_code == 200
    assert b"KisanSaathi" in kisaath.data
    assert b"/kisaath/static/" in kisaath.data

    manifest_path = app.KISAATH_BUILD_DIR + "/asset-manifest.json"
    manifest = json.loads(open(manifest_path, encoding="utf-8").read())
    main_bundle = manifest["entrypoints"][-1]
    assert client.get(f"/kisaath/{main_bundle}").status_code == 200
    assert client.get("/api/products").get_json() == []


def test_animal_health_screening_is_public_and_uses_namespaced_routes():
    client = app.app.test_client()

    page = client.get("/animal-health/")
    assert page.status_code == 200
    assert b"/animal-health/static/style.css" in page.data
    assert b"/animal-health/static/script.js" in page.data
    assert client.get("/animal-health/static/script.js").status_code == 200

    # No session is needed to open the tool or reach its namespaced API.
    missing_image = client.post("/animal-health/predict", data={})
    assert missing_image.status_code == 400
    assert missing_image.get_json()["error"]

    home = client.get("/")
    assert b"Animal Health AI" in home.data


def test_marketplace_signup_product_upload_and_delete_share_flask_app(tmp_path, monkeypatch):
    data_file = tmp_path / "data.json"
    upload_folder = tmp_path / "marketplace"
    monkeypatch.setattr(marketplace_api, "DATA_FILE", data_file)
    monkeypatch.setattr(marketplace_api, "UPLOAD_FOLDER", upload_folder)
    monkeypatch.setitem(app.app.config, "UPLOAD_FOLDER", str(upload_folder.parent))
    client = app.app.test_client()

    signup = client.post(
        "/api/auth/signup",
        json={"email": "grower@example.com", "password": "secure-pass-123"},
    )
    assert signup.status_code == 200
    login = client.post(
        "/api/auth/login",
        json={"email": "grower@example.com", "password": "secure-pass-123"},
    )
    assert login.status_code == 200
    token = login.get_json()["token"]

    anonymous_upload = client.post(
        "/upload",
        data={"image": (io.BytesIO(_png_bytes()), "seeds.png")},
        content_type="multipart/form-data",
    )
    assert anonymous_upload.status_code == 401

    upload = client.post(
        "/upload",
        headers={"Authorization": f"Bearer {token}"},
        data={"image": (io.BytesIO(_png_bytes()), "seeds.png")},
        content_type="multipart/form-data",
    )
    assert upload.status_code == 200
    image_path = upload.get_json()["filePath"]
    assert client.get(image_path).status_code == 200

    created = client.post(
        "/api/products",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "title": "Organic seeds",
            "category": "Crops",
            "price": 120,
            "description": "Seed packet",
            "images": [image_path],
            "seller": "Local grower",
        },
    )
    assert created.status_code == 200
    product = created.get_json()["product"]
    listing = client.get("/api/products")
    assert listing.status_code == 200
    assert listing.get_json()[0]["title"] == "Organic seeds"

    deleted = client.delete(
        f"/api/products/{product['id']}",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert deleted.status_code == 200
    assert client.get("/api/products").get_json() == []

    stored = json.loads(data_file.read_text(encoding="utf-8"))
    assert len(stored["users"]) == 1
    assert stored["products"] == []


def test_marketplace_browsing_is_public_and_listings_are_owner_scoped(tmp_path, monkeypatch):
    monkeypatch.setattr(marketplace_api, "DATA_FILE", tmp_path / "data.json")
    client = app.app.test_client()

    assert client.get("/api/products").status_code == 200

    seller = client.post(
        "/api/auth/signup",
        json={"email": "seller@example.com", "password": "secure-pass-123"},
    ).get_json()
    buyer = client.post(
        "/api/auth/signup",
        json={"email": "buyer@example.com", "password": "secure-pass-123"},
    ).get_json()
    assert seller["token"]
    assert buyer["token"]

    created = client.post(
        "/api/products",
        headers={"Authorization": f"Bearer {seller['token']}"},
        json={
            "title": "Fresh greens",
            "category": "Crops",
            "price": 80,
            "images": ["/uploads/marketplace/greens.jpg"],
            "seller": "Local farm",
        },
    )
    listing_id = created.get_json()["product"]["id"]
    rejected = client.delete(
        f"/api/products/{listing_id}",
        headers={"Authorization": f"Bearer {buyer['token']}"},
    )
    assert rejected.status_code == 403
    assert len(client.get("/api/products").get_json()) == 1


def test_weather_uses_server_side_provider_and_returns_current_and_forecast(monkeypatch):
    def fake_weather_request(url):
        if "geocoding-api" in url:
            return {"results": [{"name": "Pune", "latitude": 18.5, "longitude": 73.8}]}
        return {
            "current": {
                "temperature_2m": 25.0,
                "relative_humidity_2m": 48,
                "apparent_temperature": 25.5,
                "weather_code": 2,
                "wind_speed_10m": 7.2,
            },
            "daily": {
                "time": ["2026-10-08", "2026-10-09"],
                "weather_code": [2, 61],
                "temperature_2m_min": [19, 20],
                "temperature_2m_max": [30, 28],
            },
        }

    monkeypatch.setattr(marketplace_api, "_request_weather_json", fake_weather_request)
    client = app.app.test_client()

    current = client.get("/api/weather/current?city=Pune")
    assert current.status_code == 200
    assert current.get_json()["name"] == "Pune"
    assert current.get_json()["main"]["temp"] == 25.0

    forecast = client.get("/api/weather/forecast?city=Pune")
    assert forecast.status_code == 200
    assert forecast.get_json()["list"][0]["weather"][0]["description"] == "partly cloudy"


def _marketplace_token(client, email="uploader@example.com"):
    client.post("/api/auth/signup", json={"email": email, "password": "secure-pass-123"})
    return client.post("/api/auth/login", json={"email": email, "password": "secure-pass-123"}).get_json()["token"]


def test_marketplace_upload_rejects_non_images_mismatches_and_oversize(tmp_path):
    client = app.app.test_client()
    headers = {"Authorization": f"Bearer {_marketplace_token(client)}"}

    def upload(payload, name):
        return client.post("/upload", headers=headers, content_type="multipart/form-data",
                           data={"image": (io.BytesIO(payload), name)})

    assert upload(b"<?php echo 1; ?>", "shell.png").status_code == 400          # not an image
    assert upload(_png_bytes(), "photo.jpg").status_code == 400                 # PNG content, .jpg name
    assert upload(b"", "empty.png").status_code == 400
    assert upload(b"x" * (6 * 1024 * 1024), "big.png").status_code == 413       # over the 5 MB limit
    assert upload(_png_bytes(), "notes.txt").status_code == 400                 # extension not allowed
    ok = upload(_png_bytes(), "good.png")
    assert ok.status_code == 200 and ok.get_json()["filePath"].endswith(".png")
    assert [p.suffix for p in marketplace_api.UPLOAD_FOLDER.iterdir()] == [".png"]  # only the valid image was stored
