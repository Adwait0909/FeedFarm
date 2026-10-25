"""Cow registration: photo upload end-to-end, live review markup, and missing-photo handling."""
import io
import os
import sqlite3

from PIL import Image

import app


def _image(fmt="PNG", size=(40, 30)):
    buffer = io.BytesIO()
    Image.new("RGB", size, (120, 80, 40)).save(buffer, format=fmt)
    return buffer.getvalue()


def _farmer(email="photo@example.test"):
    client = app.app.test_client()
    client.post("/farmer/register", data={"full_name": "P", "email": email, "phone": "1", "password": "abcdef", "confirm_password": "abcdef"})
    client.post("/farmer/farm", data={"farm_name": "F", "village": "v", "taluka": "t", "district": "Pune", "state": "MH"})
    return client


def _doctor():
    client = app.app.test_client()
    client.post("/doctor/login", data={"email": "doctor@farmcare.local", "password": os.environ["DOCTOR_PASSWORD"]})
    return client


def _register(client, photo=None, name="photo.png", **extra):
    data = {"cow_name": "Gauri", "breed": "Gir", "cow_type": "Dairy", "gender": "Female", "local_cow_number": "7", **extra}
    if photo is not None:
        data["cow_image"] = (io.BytesIO(photo), name)
    return client.post("/farmer/cows/new", data=data, content_type="multipart/form-data")


def _image_path(cow_id):
    conn = sqlite3.connect(app.DB_PATH)
    try:
        return conn.execute("SELECT image_path FROM cows WHERE cow_id=?", (cow_id,)).fetchone()[0]
    finally:
        conn.close()


def test_uploaded_photo_is_saved_and_shown_on_every_cow_page():
    farmer = _farmer()
    response = _register(farmer, _image("PNG"))
    assert response.status_code == 302
    cow = response.headers["Location"].split("/")[-2]
    stored = _image_path(cow)
    assert stored and os.path.isfile(os.path.join(app.app.config["UPLOAD_FOLDER"], stored))
    photo_url = f"/uploads/{stored}"
    assert photo_url.encode() in farmer.get(f"/farmer/cows/{cow}").data               # owner's page
    assert photo_url.encode() in _doctor().get(f"/doctor/cow/{cow}").data            # veterinarian's page
    assert photo_url.encode() in app.app.test_client().get(f"/cow/{cow}").data       # public QR page
    assert farmer.get(photo_url).status_code == 200


def test_jpeg_upload_works_and_bad_files_are_refused_with_a_message():
    farmer = _farmer()
    assert _register(farmer, _image("JPEG"), "cow.jpg", local_cow_number="8").status_code == 302
    for payload, name, text in [(b"<?php evil ?>", "shell.png", b"not a valid image"),
                                (_image("PNG"), "cow.gif", b"Only PNG, JPG or JPEG"),
                                (_image("PNG"), "cow.webp", b"Only PNG, JPG or JPEG"),
                                (b"", "empty.png", b"empty"),
                                (b"x" * (4 * 1024 * 1024 + 10), "big.png", b"larger than 5 MB")]:
        response = _register(farmer, payload, name, local_cow_number="9")
        assert response.status_code == 200 and text in response.data, (name, response.status_code)
    conn = sqlite3.connect(app.DB_PATH)
    assert conn.execute("SELECT COUNT(*) FROM cows WHERE farmer_id IS NOT NULL").fetchone()[0] == 1   # only the valid one
    conn.close()
    assert len(os.listdir(app.app.config["UPLOAD_FOLDER"])) == 1                                      # nothing else was written


def test_request_over_the_size_limit_gets_a_friendly_message():
    farmer = _farmer()
    response = _register(farmer, b"x" * (6 * 1024 * 1024), "huge.png")
    assert response.status_code == 413 and b"too large" in response.data


def test_registration_without_photo_still_works_and_shows_a_placeholder():
    farmer = _farmer()
    cow = _register(farmer).headers["Location"].split("/")[-2]
    assert _image_path(cow) is None
    assert b"No photo has been uploaded" in farmer.get(f"/farmer/cows/{cow}").data


def test_missing_photo_file_is_handled_without_a_broken_image():
    """Issue 18: a record that points to a photo file which is not on the server."""
    conn = sqlite3.connect(app.DB_PATH)
    conn.execute("UPDATE cows SET image_path='6bcec0fb8895462caa29116806c1465b.jpg' WHERE cow_id='COW001'")
    conn.commit(); conn.close()
    doctor = _doctor()
    assert b"image file is not available" in doctor.get("/doctor/cow/COW001").data
    public = app.app.test_client().get("/cow/COW001")
    assert public.status_code == 200 and b"6bcec0fb" not in public.data and b"<img" not in public.data.split(b"passport-title")[0]
    assert _image_path("COW001") == "6bcec0fb8895462caa29116806c1465b.jpg"            # the database reference is left alone


def test_both_forms_carry_the_live_review_and_photo_preview_markup():
    farmer_form = _farmer().get("/farmer/cows/new").get_data(as_text=True)
    doctor_form = _doctor().get("/register").get_data(as_text=True)
    for html, fields in ((farmer_form, ["cow_name", "local_cow_number", "breed", "cow_type", "gender", "color", "age"]),
                         (doctor_form, ["cow_id", "cow_name", "breed", "owner_name", "owner_contact", "health_status"])):
        assert "data-live-review" in html and "data-review-photo" in html and "data-review-progress" in html
        assert "data-photo-feedback" in html and "js/cow_register.js" in html
        for field in fields:
            assert f'data-review="{field}"' in html, field


def test_repair_script_reports_without_changing_then_clears_on_request(tmp_path, capsys):
    import importlib.util, pathlib
    conn = sqlite3.connect(app.DB_PATH)
    conn.execute("UPDATE cows SET image_path='gone.jpg' WHERE cow_id='COW002'")
    conn.commit(); conn.close()
    spec = importlib.util.spec_from_file_location("repair_missing_photos", pathlib.Path(app.BASE_DIR) / "scripts" / "repair_missing_photos.py")
    module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
    assert module.main(["--db", app.DB_PATH]) == 0
    assert "COW002" in capsys.readouterr().out and _image_path("COW002") == "gone.jpg"      # report only
    assert module.main(["--db", app.DB_PATH, "--clear"]) == 0
    assert _image_path("COW002") is None and list(pathlib.Path(app.DB_PATH).parent.glob("*.bak-*"))
