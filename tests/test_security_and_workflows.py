"""Regression tests for the security and workflow fixes (all run on a throw-away database)."""
import re
import sqlite3

import pytest

import app


def _doctor_client(monkeypatch=None):
    import os
    client = app.app.test_client()
    response = client.post("/doctor/login", data={"email": "doctor@farmcare.local", "password": os.environ["DOCTOR_PASSWORD"]})
    assert response.status_code == 302
    return client


def _farmer_client(email="farmer@example.test"):
    client = app.app.test_client()
    client.post("/farmer/register", data={"full_name": "Test Farmer", "email": email, "phone": "9000000000",
                                          "password": "abcdef", "confirm_password": "abcdef"})
    client.post("/farmer/farm", data={"farm_name": "F", "village": "v", "taluka": "t", "district": "Pune", "state": "MH"})
    return client


def _add_cow(client, name="Own", local="1"):
    response = client.post("/farmer/cows/new", data={"cow_name": name, "breed": "Gir", "cow_type": "Dairy",
                                                     "gender": "Female", "local_cow_number": local})
    assert response.status_code == 302
    return response.headers["Location"].split("/")[-2]


def _rows(sql, params=()):
    conn = sqlite3.connect(app.DB_PATH)
    try:
        return conn.execute(sql, params).fetchall()
    finally:
        conn.close()


# ---------------- Issue 1 / 2 ----------------
def test_delete_requires_doctor_login_and_works_for_doctors():
    anonymous = app.app.test_client()
    response = anonymous.post("/delete/COW001")
    assert response.status_code == 302 and "/doctor/login" in response.headers["Location"]
    assert _rows("SELECT 1 FROM cows WHERE cow_id='COW001'")

    farmer = _farmer_client()
    assert farmer.post("/delete/COW001").status_code == 302
    assert _rows("SELECT 1 FROM cows WHERE cow_id='COW001'")          # a farmer is not a doctor

    assert _doctor_client().post("/delete/COW001").status_code == 302
    assert not _rows("SELECT 1 FROM cows WHERE cow_id='COW001'")


def test_published_default_doctor_password_is_refused_unless_demo_mode(monkeypatch):
    from werkzeug.security import generate_password_hash
    conn = sqlite3.connect(app.DB_PATH)
    conn.execute("INSERT INTO doctors (full_name, email, password_hash, specialization) VALUES (?,?,?,?)",
                 ("Old", "old@example.test", generate_password_hash("Vet@2026"), "General"))
    conn.commit(); conn.close()
    client = app.app.test_client()
    refused = client.post("/doctor/login", data={"email": "old@example.test", "password": "Vet@2026"})
    assert refused.status_code == 200 and b"published demo password" in refused.data
    assert client.get("/doctor").status_code == 302                      # still signed out
    monkeypatch.setenv("FARM2FEED_DEMO_MODE", "1")
    assert client.post("/doctor/login", data={"email": "old@example.test", "password": "Vet@2026"}).status_code == 302


def test_first_doctor_without_configured_password_has_no_usable_password(monkeypatch, tmp_path):
    monkeypatch.delenv("DOCTOR_PASSWORD", raising=False)
    monkeypatch.setattr(app, "DB_PATH", str(tmp_path / "fresh.sqlite3"))
    conn = sqlite3.connect(app.DB_PATH); app.ensure_sqlite_schema(conn); conn.close()
    client = app.app.test_client()
    for guess in ("Vet@2026", "replace-with-a-strong-password", ""):
        assert client.post("/doctor/login", data={"email": "doctor@farmcare.local", "password": guess}).status_code == 200
    assert client.get("/doctor").status_code == 302


def test_reset_script_only_touches_known_default_accounts(tmp_path):
    from werkzeug.security import check_password_hash, generate_password_hash
    import importlib.util, pathlib
    spec = importlib.util.spec_from_file_location("reset_doctor_passwords",
                                                  pathlib.Path(app.BASE_DIR) / "scripts" / "reset_doctor_passwords.py")
    reset = importlib.util.module_from_spec(spec); spec.loader.exec_module(reset)
    db = tmp_path / "reset.sqlite3"
    conn = sqlite3.connect(db); app.ensure_sqlite_schema(conn)
    conn.execute("INSERT INTO doctors (full_name,email,password_hash,specialization) VALUES (?,?,?,?)",
                 ("Default", "default@example.test", generate_password_hash("Vet@2026"), "x"))
    conn.execute("INSERT INTO doctors (full_name,email,password_hash,specialization) VALUES (?,?,?,?)",
                 ("Custom", "custom@example.test", generate_password_hash("my-own-secret-1"), "x"))
    conn.commit(); before = dict(conn.execute("SELECT email, password_hash FROM doctors")); conn.close()
    assert reset.main(["--db", str(db), "--dry-run"]) == 0
    assert reset.main(["--db", str(db)]) == 0
    conn = sqlite3.connect(db); after = dict(conn.execute("SELECT email, password_hash FROM doctors")); conn.close()
    assert after["custom@example.test"] == before["custom@example.test"]            # untouched
    assert after["default@example.test"] != before["default@example.test"]         # replaced
    assert not check_password_hash(after["default@example.test"], "Vet@2026")
    assert list(db.parent.glob("reset.sqlite3.bak-*"))                               # backup was written


# ---------------- Issue 4 / 5 / 6 / 20 / 21 ----------------
def test_help_request_reaches_doctor_and_reply_reaches_farmer():
    farmer = _farmer_client()
    own = _add_cow(farmer)
    assert farmer.post("/farmer/help", data={"cow_id": "COW001", "request_type": "Checkup", "description": "x"},
                       follow_redirects=True).status_code == 200
    assert not _rows("SELECT 1 FROM farmers_assistance_requests")                    # someone else's cow: refused
    farmer.post("/farmer/help", data={"cow_id": own, "request_type": "Checkup", "description": "Limping badly"})
    doctor = _doctor_client()
    assert b"Limping badly" in doctor.get("/doctor/assistance").data
    request_id = _rows("SELECT id FROM farmers_assistance_requests")[0][0]
    assert doctor.post(f"/doctor/requests/{request_id}/contact", data={"doctor_response": "Visit tomorrow"}).status_code == 302
    assert b"Visit tomorrow" in farmer.get("/farmer/help").data
    # changing only the status keeps the reply
    doctor.post("/doctor/assistance", data={"request_id": request_id, "status": "resolved", "doctor_response": ""})
    assert _rows("SELECT status, doctor_response FROM farmers_assistance_requests") == [("resolved", "Visit tomorrow")]
    assert doctor.post("/doctor/assistance", data={"request_id": request_id, "status": "bogus"}).status_code == 302
    assert _rows("SELECT status FROM farmers_assistance_requests") == [("resolved",)]


def test_found_reports_are_shown_to_the_owner_only():
    owner, other = _farmer_client("a@example.test"), _farmer_client("b@example.test")
    cow = _add_cow(owner)
    assert app.app.test_client().post(f"/report_found/{cow}", data={"finder_name": "Finder", "finder_contact": "123",
                                      "current_area": "Market", "message": "Found near road"}).status_code == 302
    assert b"Found near road" in owner.get(f"/farmer/cows/{cow}").data
    assert other.get(f"/farmer/cows/{cow}").status_code == 404                       # not the owner's page
    public = other.get(f"/cow/{cow}")                                                # public page, no private data
    assert public.status_code == 200 and b"Found near road" not in public.data and b"123" not in public.data
    assert b"Found near road" not in app.app.test_client().get(f"/cow/{cow}").data


def test_doctor_logout_keeps_the_farmer_session():
    client = _farmer_client()
    client.post("/doctor/login", data={"email": "doctor@farmcare.local", "password": __import__("os").environ["DOCTOR_PASSWORD"]})
    client.get("/doctor/logout")
    assert client.get("/farmer").status_code == 200
    assert client.get("/doctor").status_code == 302


# ---------------- Issue 9 / 15 ----------------
GOOD_COW = {"cow_id": "PUB-1", "cow_name": "n", "breed": "b", "cow_type": "Dairy", "gender": "Female",
            "owner_name": "o", "owner_contact": "1", "age": "abc", "milk_production": "lots", "health_score": "high"}


def test_register_requires_a_farmer_or_doctor_login():
    anonymous = app.app.test_client()
    page = anonymous.get("/register")
    assert page.status_code == 302 and "/farmer/login" in page.headers["Location"]
    posted = anonymous.post("/register", data=GOOD_COW)
    assert posted.status_code == 302 and "/farmer/login" in posted.headers["Location"]
    assert not _rows("SELECT 1 FROM cows WHERE cow_id='PUB-1'")                       # nothing was created
    assert _farmer_client().get("/register").status_code == 200
    assert _doctor_client().get("/register").status_code == 200


def test_register_rejects_path_traversal_ids_and_numeric_garbage():
    doctor = _doctor_client()
    for bad in ("../../evil", "a/b", "..", "x" * 80, ".hidden"):
        response = doctor.post("/register", data={**GOOD_COW, "cow_id": bad})
        assert response.status_code == 200 and b"letters, numbers" in response.data
    assert not _rows("SELECT 1 FROM cows WHERE cow_id LIKE '%evil%'")
    with pytest.raises(ValueError):
        app.generate_qr_for_cow("../../evil")
    assert doctor.post("/register", data=GOOD_COW).status_code == 302
    assert _rows("SELECT farmer_id, age, milk_production, health_score FROM cows WHERE cow_id='PUB-1'") == [(None, None, None, None)]


def test_cow_registered_by_a_logged_in_farmer_belongs_to_that_farmer():
    farmer = _farmer_client()
    assert farmer.post("/register", data={**GOOD_COW, "cow_id": "PUB-2", "age": "5"}).status_code == 302
    owner = _rows("SELECT farmer_id, farm_id, age FROM cows WHERE cow_id='PUB-2'")[0]
    assert owner[0] is not None and owner[1] is not None and owner[2] == 5


# ---------------- Issue 6 ----------------
def test_logged_in_farmer_sees_public_page_of_other_cows():
    farmer = _farmer_client()
    response = farmer.get("/cow/COW001")
    assert response.status_code == 200
    assert b"owner_contact" not in response.data


# ---------------- Issue 26 ----------------
def test_doctor_dashboard_api_requires_login_and_reflects_new_requests():
    assert app.app.test_client().get("/doctor/api/dashboard").status_code == 401
    doctor = _doctor_client()
    first = doctor.get("/doctor/api/dashboard")
    data = first.get_json()
    assert data["source"] == "database" and data["total"] == 3 and data["demo_count"] == 3
    assert all(cow["is_demo"] for cow in data["cows"])
    assert doctor.get("/doctor/api/dashboard", headers={"If-None-Match": first.headers["ETag"]}).status_code == 304
    assert doctor.get("/doctor/api/dashboard?summary=1").get_json()["cows"] == []
    farmer = _farmer_client()
    own = _add_cow(farmer)
    farmer.post("/farmer/help", data={"cow_id": own, "request_type": "Checkup", "description": "Cough"})
    after = doctor.get("/doctor/api/dashboard").get_json()
    assert after["request_count"] == 1 and after["request_version"] != data["request_version"]
    assert after["total"] == 4 and after["demo_count"] == 3                               # the real cow is not marked demo
    assert [c["is_demo"] for c in after["cows"] if c["cow_id"] == own] == [False]
    page = doctor.get("/doctor").data
    assert b"doctor_live.js" in page and b'id="live-status"' in page


# ---------------- Issue 2: shipped database ----------------
def test_shipped_database_has_no_doctor_account_on_a_published_password():
    from werkzeug.security import check_password_hash
    shipped = sqlite3.connect(f"file:{app.BASE_DIR}/cow_qr_demo.sqlite3?mode=ro", uri=True)
    try:
        hashes = [row[0] for row in shipped.execute("SELECT password_hash FROM doctors")]
    finally:
        shipped.close()
    assert hashes
    for password_hash in hashes:
        assert not any(check_password_hash(password_hash, p) for p in app.KNOWN_DEFAULT_DOCTOR_PASSWORDS)


def test_accounts_without_a_password_cannot_sign_in_and_reset_script_sets_one(tmp_path):
    import importlib.util, pathlib
    from werkzeug.security import check_password_hash
    conn = sqlite3.connect(app.DB_PATH)
    conn.execute("UPDATE doctors SET password_hash = 'unset$abc' WHERE email='doctor@farmcare.local'")
    conn.commit(); conn.close()
    client = app.app.test_client()
    for guess in ("unset$abc", "", "anything"):
        assert client.post("/doctor/login", data={"email": "doctor@farmcare.local", "password": guess}).status_code == 200
    spec = importlib.util.spec_from_file_location("reset_doctor_passwords", pathlib.Path(app.BASE_DIR) / "scripts" / "reset_doctor_passwords.py")
    reset = importlib.util.module_from_spec(spec); spec.loader.exec_module(reset)
    assert reset.main(["--db", app.DB_PATH, "--no-backup"]) == 0
    new_hash = _rows("SELECT password_hash FROM doctors WHERE email='doctor@farmcare.local'")[0][0]
    assert not new_hash.startswith("unset$")
    assert not check_password_hash(new_hash, "Vet@2026")
