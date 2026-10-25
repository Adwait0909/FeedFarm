"""Run the main farmer / doctor workflow on real PostgreSQL and MySQL servers.

These tests are skipped unless you point them at a server whose user may CREATE DATABASE.  Each test
creates its own randomly named database and drops it afterwards, so no existing database is touched.

    PostgreSQL:  F2F_TEST_PG_HOST=localhost F2F_TEST_PG_USER=postgres F2F_TEST_PG_PASSWORD=...
    MySQL:       F2F_TEST_MYSQL_HOST=localhost F2F_TEST_MYSQL_USER=root F2F_TEST_MYSQL_PASSWORD=...
    (optional)   F2F_TEST_PG_PORT / F2F_TEST_MYSQL_PORT
"""
import os
import secrets

import pytest

import app
from services import db_compat


def _env(prefix, name, default=None):
    return os.environ.get(f"F2F_TEST_{prefix}_{name}", default)


@pytest.fixture(params=["postgres", "mysql"])
def server_db(request, monkeypatch):
    kind = request.param
    prefix = "PG" if kind == "postgres" else "MYSQL"
    if not _env(prefix, "HOST"):
        pytest.skip(f"set F2F_TEST_{prefix}_HOST (and USER/PASSWORD) to run the {kind} tests")
    database = "f2f_pytest_" + secrets.token_hex(4)
    host, user, password = _env(prefix, "HOST"), _env(prefix, "USER", "root"), _env(prefix, "PASSWORD", "")
    port = int(_env(prefix, "PORT", "5432" if kind == "postgres" else "3306"))

    if kind == "postgres":
        psycopg2 = pytest.importorskip("psycopg2")
        admin = psycopg2.connect(host=host, port=port, user=user, password=password, dbname="postgres")
        admin.autocommit = True
        admin.cursor().execute(f"CREATE DATABASE {database}")
        monkeypatch.setenv("PG_HOST", host); monkeypatch.setenv("PG_PORT", str(port)); monkeypatch.setenv("PG_USER", user)
        monkeypatch.setenv("PG_PASSWORD", password); monkeypatch.setenv("PG_NAME", database)
    else:
        connector = pytest.importorskip("mysql.connector")
        admin = connector.connect(host=host, port=port, user=user, password=password)
        admin.cursor().execute(f"CREATE DATABASE {database} CHARACTER SET utf8mb4")
        monkeypatch.setitem(app.DB_CONFIG, "host", host); monkeypatch.setitem(app.DB_CONFIG, "port", port)
        monkeypatch.setitem(app.DB_CONFIG, "user", user); monkeypatch.setitem(app.DB_CONFIG, "password", password)
        monkeypatch.setitem(app.DB_CONFIG, "database", database)
    monkeypatch.setattr(app, "DB_TYPE", kind)
    db_compat._SCHEMA_READY.discard(kind)
    yield kind
    db_compat._SCHEMA_READY.discard(kind)
    try:
        if kind == "postgres":
            admin.cursor().execute(f"DROP DATABASE IF EXISTS {database} WITH (FORCE)")
        else:
            admin.cursor().execute(f"DROP DATABASE IF EXISTS {database}")
    finally:
        admin.close()


def _login_doctor():
    client = app.app.test_client()
    assert client.post("/doctor/login", data={"email": "doctor@farmcare.local",
                                              "password": os.environ["DOCTOR_PASSWORD"]}).status_code == 302
    return client


def test_schema_is_created_and_seed_data_loaded(server_db):
    conn = app.get_db_connection()
    assert app.DB_TYPE == server_db, "the app silently fell back to SQLite"
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT COUNT(*) AS total FROM cows"); assert cursor.fetchone()["total"] == 3
    cursor.execute("SELECT COUNT(*) AS total FROM doctors"); assert cursor.fetchone()["total"] == 1
    cursor.close(); conn.close()
    # creating the schema again (new process / reconnect) is harmless
    db_compat._SCHEMA_READY.discard(server_db)
    app.get_db_connection().close()


def test_farmer_and_doctor_workflow_on_server_database(server_db):
    farmer = app.app.test_client()
    assert farmer.post("/farmer/register", data={"full_name": "गणेश पाटील", "email": "g@example.test", "phone": "9000000001",
                                                 "password": "abcdef", "confirm_password": "abcdef"}).status_code == 302
    assert farmer.post("/farmer/farm", data={"farm_name": "शेत", "village": "v", "taluka": "t", "district": "Pune", "state": "MH"}).status_code == 302
    created = farmer.post("/farmer/cows/new", data={"cow_name": "गौरी", "breed": "Gir", "cow_type": "Dairy", "gender": "Female",
                                                    "local_cow_number": "1", "age": "4", "milk_production": "9.5"})
    assert created.status_code == 302
    cow = created.headers["Location"].split("/")[-2]
    duplicate = farmer.post("/farmer/cows/new", data={"cow_name": "dup", "breed": "Gir", "cow_type": "Dairy",
                                                      "gender": "Female", "local_cow_number": "1"})
    assert duplicate.status_code == 200                                              # integrity error handled, not a 500
    for path in ("/farmer", f"/farmer/cows/{cow}", f"/farmer/health/{cow}", "/farmer/help", f"/cow/{cow}", f"/qr/{cow}"):
        assert farmer.get(path).status_code == 200, path
    assert "गौरी".encode() in farmer.get(f"/farmer/cows/{cow}").data                  # Marathi text round-trips

    farmer.post("/farmer/help", data={"cow_id": cow, "request_type": "Checkup", "description": "Limping badly"})
    app.app.test_client().post(f"/report_found/{cow}", data={"finder_name": "Finder", "finder_contact": "123",
                                                             "current_area": "Market", "message": "Found near road"})
    doctor = _login_doctor()
    for path in ("/doctor", "/doctor?q=%E0%A4%97", "/doctor/scan", "/doctor/assistance", "/dashboard",
                 f"/doctor/cow/{cow}", f"/doctor/update/{cow}", "/doctor/api/dashboard"):
        assert doctor.get(path).status_code == 200, path
    assert b"Limping badly" in doctor.get("/doctor/assistance").data
    assert doctor.get("/doctor/api/dashboard").get_json()["request_count"] == 1

    update = doctor.post(f"/doctor/update/{cow}", data={"health_status": "Healthy", "health_score": "90", "body_temperature": "38.5",
                                                        "weight_kg": "400", "last_health_check": "2026-10-01",
                                                        "next_checkup_date": "2026-10-15", "vaccination_status": "Up to date",
                                                        "record_title": "Visit", "summary": "ok"})
    assert update.status_code in (200, 302)
    conn = app.get_db_connection(); cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT id FROM farmers_assistance_requests ORDER BY id DESC LIMIT 1"); request_id = cursor.fetchone()["id"]
    cursor.close(); conn.close()
    assert doctor.post(f"/doctor/requests/{request_id}/contact", data={"doctor_response": "Visit tomorrow"}).status_code == 302
    assert b"Visit tomorrow" in farmer.get("/farmer/help").data
    assert "Found near road".encode() in farmer.get(f"/farmer/cows/{cow}").data

    assert doctor.post(f"/delete/{cow}").status_code == 302
    conn = app.get_db_connection(); cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT COUNT(*) AS total FROM cows WHERE cow_id = %s", (cow,)); assert cursor.fetchone()["total"] == 0
    cursor.execute("SELECT COUNT(*) AS total FROM found_reports WHERE cow_id = %s", (cow,)); assert cursor.fetchone()["total"] == 0
    cursor.close(); conn.close()


def test_legacy_columns_are_added_without_touching_existing_rows(server_db):
    """A database created by an older, smaller schema keeps its data and gains the missing columns."""
    conn = app.get_db_connection(); cursor = conn.cursor()
    cursor.execute("ALTER TABLE cows DROP COLUMN farm_id") if server_db == "postgres" else cursor.execute("ALTER TABLE cows DROP COLUMN farm_id")
    conn.commit(); cursor.close(); conn.close()
    db_compat._SCHEMA_READY.discard(server_db)
    conn = app.get_db_connection(); cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT cow_name, farm_id FROM cows WHERE cow_id = 'COW001'")
    row = cursor.fetchone()
    assert row["cow_name"] == "Ganga" and row["farm_id"] is None
    cursor.close(); conn.close()
