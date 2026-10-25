"""The demo seed script must be repeatable and must never overwrite real data."""
import importlib.util
import pathlib
import sqlite3

import pytest

import app


def _seed_module():
    spec = importlib.util.spec_from_file_location("seed_demo_data", pathlib.Path(app.BASE_DIR) / "scripts" / "seed_demo_data.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _counts(db):
    conn = sqlite3.connect(db)
    try:
        return {t: conn.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0]
                for t in ("cows", "farmers", "farms", "doctors", "cow_medical_history", "veterinary_directory")}
    finally:
        conn.close()


def test_seed_is_idempotent_and_preserves_real_records(tmp_path, capsys):
    db = tmp_path / "seed.sqlite3"
    conn = sqlite3.connect(db)
    app.ensure_sqlite_schema(conn)
    # real records that already exist
    conn.execute("INSERT INTO farmers (full_name,email,password_hash) VALUES ('Real Farmer','real@example.test','real-hash')")
    farmer_id = conn.execute("SELECT id FROM farmers WHERE email='real@example.test'").fetchone()[0]
    conn.execute("INSERT INTO cows (cow_id,cow_name,breed,cow_type,gender,farmer_id,farm_id,local_cow_number) "
                 "VALUES ('REAL-1','Mine','Gir','Dairy','Female',?, 'REAL-FARM','R1')", (farmer_id,))
    conn.execute("UPDATE cows SET farmer_id=?, farm_id='REAL-FARM' WHERE cow_id='COW001'", (farmer_id,))   # a real owner took COW001
    conn.execute("INSERT INTO found_reports (cow_id, finder_name, finder_contact) VALUES ('REAL-1','F','1')")
    doctor_hash_before = dict(conn.execute("SELECT email, password_hash FROM doctors"))
    conn.commit(); conn.close()

    seed = _seed_module()
    assert seed.main(["--db", str(db), "--no-qr", "--no-backup"]) in (None, 0)
    first = _counts(db)
    assert seed.main(["--db", str(db), "--no-qr", "--no-backup"]) in (None, 0)
    assert _counts(db) == first                                                      # second run adds nothing

    conn = sqlite3.connect(db)
    assert conn.execute("SELECT COUNT(*) FROM cows WHERE cow_id='COW001' OR cow_id='COW002' OR cow_id='COW003' "
                        "OR cow_id LIKE 'COW-DEMO-%'").fetchone()[0] == 100
    assert conn.execute("SELECT cow_name, farmer_id, farm_id FROM cows WHERE cow_id='REAL-1'").fetchone() == ("Mine", farmer_id, "REAL-FARM")
    assert conn.execute("SELECT farmer_id, farm_id FROM cows WHERE cow_id='COW001'").fetchone() == (farmer_id, "REAL-FARM")  # not taken over
    assert conn.execute("SELECT COUNT(*) FROM found_reports WHERE cow_id='REAL-1'").fetchone()[0] == 1
    assert conn.execute("SELECT password_hash FROM farmers WHERE email='real@example.test'").fetchone()[0] == "real-hash"
    after = dict(conn.execute("SELECT email, password_hash FROM doctors"))
    assert all(after[email] == hashed for email, hashed in doctor_hash_before.items())      # existing doctors untouched
    assert conn.execute("SELECT cow_id FROM cows GROUP BY cow_id HAVING COUNT(*) > 1").fetchall() == []
    conn.close()


def test_seed_makes_a_backup_and_refuses_to_mix_with_foreign_farms(tmp_path):
    db = tmp_path / "seed2.sqlite3"
    conn = sqlite3.connect(db); app.ensure_sqlite_schema(conn)
    conn.execute("INSERT INTO farmers (full_name,email,password_hash) VALUES ('Other','other@example.test','h')")
    other = conn.execute("SELECT id FROM farmers").fetchone()[0]
    conn.execute("INSERT INTO farms (farm_id, farmer_id, farm_name) VALUES ('FARM-01', ?, 'Not a demo farm')", (other,))
    conn.commit(); conn.close()
    seed = _seed_module()
    before = _counts(db)
    with pytest.raises(RuntimeError, match="already belongs to a different farmer"):
        seed.main(["--db", str(db), "--no-qr"])
    assert list(tmp_path.glob("seed2.sqlite3.bak-*"))                                  # backup taken before the attempt
    assert _counts(db) == before                                                       # nothing was committed
