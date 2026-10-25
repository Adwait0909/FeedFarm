import sqlite3

import app
from scripts import seed_demo_data


def test_demo_seed_creates_100_cows_and_linked_doctor_histories(tmp_path, monkeypatch):
    database = tmp_path / "seeded.sqlite3"
    monkeypatch.setattr(app, "DB_PATH", str(database))
    conn = sqlite3.connect(database)
    try:
        app.ensure_sqlite_schema(conn)
    finally:
        conn.close()

    seed_demo_data.main()

    conn = sqlite3.connect(database)
    try:
        assert conn.execute("SELECT COUNT(*) FROM cows").fetchone()[0] == 100
        assert conn.execute("SELECT COUNT(*) FROM farms").fetchone()[0] == 10
        assert conn.execute(
            "SELECT COUNT(*) FROM farmers WHERE email LIKE '%@demo.example.test'"
        ).fetchone()[0] == 10
        assert conn.execute(
            "SELECT COUNT(*) FROM doctors WHERE email LIKE '%@demo.example.test' "
            "OR email = 'doctor@farmcare.local'"
        ).fetchone()[0] == 10
        doctor_patient_counts = conn.execute(
            """
            SELECT doctor_id, COUNT(DISTINCT cow_id)
            FROM cow_medical_history
            WHERE record_type = 'demo_seed'
            GROUP BY doctor_id
            """
        ).fetchall()
        assert len(doctor_patient_counts) == 10
        assert all(count > 50 for _, count in doctor_patient_counts)
        assert conn.execute(
            "SELECT COUNT(*) FROM cows WHERE farmer_id IS NOT NULL AND farm_id IS NOT NULL"
        ).fetchone()[0] == 100
        assert conn.execute(
            "SELECT COUNT(*) FROM cow_medical_history WHERE record_type = 'demo_seed'"
        ).fetchone()[0] == 600
    finally:
        conn.close()

    # Running the seed step again must not duplicate the records.
    seed_demo_data.main()
    conn = sqlite3.connect(database)
    try:
        assert conn.execute("SELECT COUNT(*) FROM cows").fetchone()[0] == 100
        assert conn.execute(
            "SELECT COUNT(*) FROM cow_medical_history WHERE record_type = 'demo_seed'"
        ).fetchone()[0] == 600
    finally:
        conn.close()
