import os

import pytest

try:
    import mysql.connector as mysql_connector
except ImportError:  # MySQL driver is optional (see requirements-mysql.txt)
    mysql_connector = None

import app


@pytest.mark.skipif(mysql_connector is None, reason="mysql-connector-python not installed")
def test_get_db_connection_falls_back_to_sqlite(monkeypatch):
    def raise_interface_error(**kwargs):
        raise mysql_connector.InterfaceError("Can't connect to MySQL server")

    monkeypatch.setattr(app, "DB_CONFIG", {"host": "localhost", "user": "root", "password": "", "database": "cow_qr_demo"})
    monkeypatch.setattr(app, "DB_TYPE", "mysql")
    monkeypatch.setattr(app.mysql.connector, "connect", raise_interface_error)

    conn = app.get_db_connection()

    try:
        row = conn.execute("SELECT 1 AS value").fetchone()
        assert row[0] == 1
    finally:
        conn.close()


def test_doctor_can_update_health_record_without_changing_cow_id():
    client = app.app.test_client()

    login_response = client.post(
        "/doctor/login",
        data={
            "email": "doctor@farmcare.local",
            "password": os.environ["DOCTOR_PASSWORD"],
        },
        follow_redirects=True,
    )
    assert login_response.status_code == 200

    response = client.get("/doctor/update/COW001")
    assert response.status_code == 200

    updated = client.post(
        "/doctor/update/COW001",
        data={
            "doctor_name": "Dr. Sharma",
            "health_status": "Healthy",
            "health_score": "96",
            "vaccination_status": "Up to date",
            "last_vaccination_date": "2026-09-10",
            "last_health_check": "2026-09-15",
            "disease_history": "No illness reported",
            "milk_production": "13.4",
            "notes": "Improved appetite after treatment.",
            "medical_record": "Routine consultation completed.",
            "treatment_history": "Vitamin supplements given.",
            "last_treatment_date": "2026-09-14",
            "next_checkup_date": "2026-10-14",
            "body_temperature": "38.2",
            "weight_kg": "420",
            "pregnancy_status": "Open",
        },
        follow_redirects=True,
    )

    assert updated.status_code == 200
    body = updated.get_data(as_text=True)
    assert "COW001" in body
    assert "Dr. Sharma" in body
    assert "Routine consultation completed." in body
    assert "No illness reported" in body
