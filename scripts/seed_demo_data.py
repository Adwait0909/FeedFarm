"""Add repeatable, clearly synthetic Farm2Feed demonstration records.

Run after installing requirements:
    python scripts/seed_demo_data.py

The script preserves existing records, tops the cow registry up to 100 designated
demonstration cows (COW001-COW003 and COW-DEMO-0004 ... COW-DEMO-0100), and
creates 10 farms, farmer accounts, doctor accounts, and linked clinical
history entries on the supplied SQLite database.

It is safe to run repeatedly: nothing is deleted, existing accounts keep their
passwords, cows that already have an owner keep it, and the SQLite file is
copied to ``<file>.bak-<timestamp>`` before the first change.

    python scripts/seed_demo_data.py                  # seed the configured database
    python scripts/seed_demo_data.py --db temp.sqlite3  # try it on a throw-away copy first
"""

from __future__ import annotations

import argparse
import os
import secrets
import shutil
import sqlite3
import sys
from datetime import datetime
from pathlib import Path

from werkzeug.security import generate_password_hash

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import app  # noqa: E402


FARMERS = [
    ("Ramesh Patil", "ramesh.patil", "Shivapur", "Khed", "Pune"),
    ("Sunita Patil", "sunita.patil", "Nandgaon", "Baramati", "Pune"),
    ("Vijay Jadhav", "vijay.jadhav", "Karanjgaon", "Karad", "Satara"),
    ("Meera Shinde", "meera.shinde", "Pimpalwadi", "Rahata", "Ahmednagar"),
    ("Ganesh More", "ganesh.more", "Akluj", "Malshiras", "Solapur"),
    ("Kavita Pawar", "kavita.pawar", "Wai", "Wai", "Satara"),
    ("Nitin Deshmukh", "nitin.deshmukh", "Narayangaon", "Junnar", "Pune"),
    ("Anita Bhosale", "anita.bhosale", "Phaltan", "Phaltan", "Satara"),
    ("Suresh Chavan", "suresh.chavan", "Daund", "Daund", "Pune"),
    ("Lata Gawade", "lata.gawade", "Sangamner", "Sangamner", "Ahmednagar"),
]

DOCTORS = [
    ("Dr. Asha Mehta", "doctor@farmcare.local", "Veterinary Medicine"),
    ("Dr. Rohan Kulkarni", "rohan.kulkarni@demo.example.test", "Dairy Cattle Health"),
    ("Dr. Neha Joshi", "neha.joshi@demo.example.test", "Preventive Veterinary Care"),
    ("Dr. Prakash Shinde", "prakash.shinde@demo.example.test", "Large Animal Medicine"),
    ("Dr. Kavita Rao", "kavita.rao@demo.example.test", "Bovine Reproduction"),
    ("Dr. Imran Shaikh", "imran.shaikh@demo.example.test", "Veterinary Nutrition"),
    ("Dr. Meenal Desai", "meenal.desai@demo.example.test", "Herd Health"),
    ("Dr. Sandeep Pawar", "sandeep.pawar@demo.example.test", "Dairy Animal Medicine"),
    ("Dr. Pooja Nair", "pooja.nair@demo.example.test", "Animal Wellness"),
    ("Dr. Ajay Patil", "ajay.patil@demo.example.test", "Field Veterinary Practice"),
]

BREEDS = ["Gir", "Sahiwal", "Red Sindhi", "Deoni", "Khillari", "Jersey Cross"]
COLORS = ["Reddish Brown", "Light Brown", "Deep Red", "Brown and White", "Grey", "Black"]


def farm_for_cow(number: int) -> int:
    """Keep the three supplied cows in their named farms; fill to 10 per farm."""
    if number <= 2:
        return 0
    if number == 3:
        return 1
    if number <= 11:
        return 0
    if number <= 20:
        return 1
    return 2 + (number - 21) // 10


def ensure_farmer_and_farm(conn, farmer_index: int, password_hash: str):
    name, email_prefix, village, taluka, district = FARMERS[farmer_index]
    email = f"{email_prefix}@demo.example.test"
    conn.execute(
        """
        INSERT OR IGNORE INTO farmers
            (full_name, email, phone, password_hash, village, taluka, district, state)
        VALUES (?, ?, ?, ?, ?, ?, ?, 'Maharashtra')
        """,
        (
            name,
            email,
            f"90000000{farmer_index + 1:02d}",
            password_hash,
            village,
            taluka,
            district,
        ),
    )
    farmer_id = conn.execute(
        "SELECT id FROM farmers WHERE email = ?", (email,)
    ).fetchone()[0]
    farm_id = f"FARM-{farmer_index + 1:02d}"
    owner = conn.execute("SELECT farmer_id FROM farms WHERE farm_id = ?", (farm_id,)).fetchone()
    if owner is not None and owner[0] != farmer_id:
        raise RuntimeError(
            f"Farm id {farm_id} already belongs to a different farmer; refusing to mix demo and real data."
        )
    conn.execute(
        """
        INSERT OR IGNORE INTO farms
            (farmer_id, farm_id, farm_name, village, taluka, district, state, service_area)
        VALUES (?, ?, ?, ?, ?, ?, 'Maharashtra', ?)
        """,
        (
            farmer_id,
            farm_id,
            f"{name.split()[0]}'s {['Green Valley', 'Meadow', 'Sunrise'][farmer_index % 3]} Farm",
            village,
            taluka,
            district,
            f"{district}, Maharashtra",
        ),
    )
    return farmer_id, farm_id, name, f"90000000{farmer_index + 1:02d}", village, district


def parse_args(argv=None):
    parser = argparse.ArgumentParser(description="Seed synthetic Farm2Feed demonstration data (SQLite).")
    parser.add_argument("--db", help="SQLite file to seed instead of the configured database")
    parser.add_argument("--no-backup", action="store_true", help="skip the timestamped backup copy")
    parser.add_argument("--no-qr", action="store_true", help="do not generate QR images")
    return parser.parse_args(argv)


def main(argv=None):
    args = parse_args(argv if argv is not None else [])
    if args.db:
        app.DB_PATH = str(Path(args.db).resolve())
    farmer_password = os.environ.get("DEMO_FARMER_PASSWORD", "FarmDemo@2026")
    # Doctor accounts carry clinical access, so their demo password is never a published constant.
    doctor_password = os.environ.get("DEMO_DOCTOR_PASSWORD")
    generated_doctor_password = None
    if not doctor_password:
        doctor_password = generated_doctor_password = secrets.token_urlsafe(12)
    farmer_hash = generate_password_hash(farmer_password)
    doctor_hash = generate_password_hash(doctor_password)

    if not args.no_backup and Path(app.DB_PATH).exists():
        backup = Path(app.DB_PATH).with_name(Path(app.DB_PATH).name + ".bak-" + datetime.now().strftime("%Y%m%d%H%M%S"))
        shutil.copy2(app.DB_PATH, backup)
        print(f"Backup written to {backup.name}")

    conn = sqlite3.connect(app.DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    app.ensure_sqlite_schema(conn)

    try:
        conn.execute("BEGIN")

        farmers_and_farms = [
            ensure_farmer_and_farm(conn, i, farmer_hash) for i in range(len(FARMERS))
        ]

        created_doctors = 0
        for doctor_index, (name, email, specialization) in enumerate(DOCTORS):
            created_doctors += conn.execute(
                """
                INSERT OR IGNORE INTO doctors (full_name, email, password_hash, specialization)
                VALUES (?, ?, ?, ?)
                """,
                (name, email, doctor_hash, specialization),
            ).rowcount
            conn.execute(
                """
                INSERT INTO veterinary_directory
                    (full_name, clinic_name, specialization, district, city, phone,
                     email, service_area, location_note)
                SELECT ?, ?, ?, ?, ?, ?, ?, ?, ?
                WHERE NOT EXISTS (
                    SELECT 1 FROM veterinary_directory WHERE email = ?
                )
                """,
                (
                    name,
                    f"{name.removeprefix('Dr. ')} Animal Care",
                    specialization,
                    FARMERS[doctor_index % len(FARMERS)][4],
                    FARMERS[doctor_index % len(FARMERS)][4],
                    f"90100000{doctor_index:02d}",
                    email,
                    "Maharashtra",
                    "Demonstration veterinary profile",
                    email,
                ),
            )

        doctor_rows = conn.execute(
            "SELECT id, full_name, email FROM doctors ORDER BY id"
        ).fetchall()
        demo_doctors = []
        for doctor in DOCTORS:
            found = next((row for row in doctor_rows if row["email"] == doctor[1]), None)
            if found:
                demo_doctors.append(found)
        if len(demo_doctors) != 10:
            raise RuntimeError(f"Expected 10 demo doctor profiles; found {len(demo_doctors)}.")

        cow_rows = conn.execute("SELECT cow_id FROM cows ORDER BY cow_id").fetchall()
        existing_ids = {row["cow_id"] for row in cow_rows}
        for number in range(1, 101):
            cow_id = f"COW{number:03d}" if number <= 3 else f"COW-DEMO-{number:04d}"
            farm_index = farm_for_cow(number)
            farmer_id, farm_id, owner_name, phone, village, district = farmers_and_farms[farm_index]
            doctor_index = (number - 1) % len(demo_doctors)
            doctor = demo_doctors[doctor_index]
            if cow_id not in existing_ids:
                breed = BREEDS[(number - 1) % len(BREEDS)]
                age = 2 + (number % 7)
                status = "Under Observation" if number % 13 == 0 else "Healthy"
                health_score = 76 + (number * 7 % 23)
                local_number = f"{farm_index + 1:02d}-{number:03d}"
                if conn.execute(
                    "SELECT 1 FROM cows WHERE farm_id = ? AND local_cow_number = ?", (farm_id, local_number)
                ).fetchone():
                    local_number += "-D"
                location = f"{village}, {district}, Maharashtra"
                conn.execute(
                    """
                    INSERT INTO cows
                        (cow_id, cow_name, breed, cow_type, gender, age, date_of_birth,
                         color, registered_location, owner_name, owner_contact,
                         local_cow_number, farm_identity, qr_code_value, health_status,
                         health_score, vaccination_status, last_vaccination_date,
                         next_vaccination_date, last_health_check, disease_history,
                         milk_production, notes, doctor_name, medical_record,
                         treatment_history, last_treatment_date, next_checkup_date,
                         body_temperature, weight_kg, pregnancy_status, farm_id, farmer_id)
                    VALUES (?, ?, ?, 'Dairy', 'Female', ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?,
                            'Up to date', '2026-08-15', '2027-02-15', '2026-09-18',
                            'No illness recorded in this synthetic demo profile.',
                            ?, 'Synthetic sample record for product demonstration.',
                            ?, 'Routine wellness review (demo data).',
                            'Routine health monitoring; no medication recorded.',
                            '2026-09-18', '2026-12-18', ?, ?, 'Open', ?, ?)
                    """,
                    (
                        cow_id,
                        f"{['Gauri', 'Chandni', 'Sundari', 'Kamadhenu', 'Moti'][number % 5]} {number:02d}",
                        breed,
                        age,
                        f"{2026 - age}-03-{(number % 27) + 1:02d}",
                        COLORS[(number - 1) % len(COLORS)],
                        location,
                        owner_name,
                        phone,
                        local_number,
                        farm_id,
                        f"{app.SITE_BASE_URL}/cow/{cow_id}",
                        status,
                        health_score,
                        round(7.5 + (number % 65) / 10, 1),
                        doctor["full_name"],
                        round(38.0 + (number % 9) / 10, 1),
                        280 + (number * 13 % 240),
                        farm_id,
                        farmer_id,
                    ),
                )

            # Assign all existing animals to the demo farms while keeping the
            # supplied owner/farm labels intact on the three original records.
            conn.execute(
                """
                UPDATE cows
                SET farmer_id = ?, farm_id = ?, registered_location = ?,
                    qr_code_value = COALESCE(qr_code_value, ?)
                WHERE cow_id = ? AND farmer_id IS NULL
                """,
                (
                    farmer_id,
                    farm_id,
                    f"{village}, {district}, Maharashtra",
                    f"{app.SITE_BASE_URL}/cow/{cow_id}",
                    cow_id,
                ),
            )

        # Each clinician has 60 distinct patients. A cow can have multiple
        # clinicians in its timeline; every synthetic entry is visibly marked.
        for number in range(1, 101):
            cow_id = f"COW{number:03d}" if number <= 3 else f"COW-DEMO-{number:04d}"
            first_doctor = (number - 1) % 10
            for offset in range(6):
                doctor = demo_doctors[(first_doctor + offset) % 10]
                conn.execute(
                    """
                    INSERT INTO cow_medical_history
                        (cow_id, doctor_id, doctor_name, record_type, title, summary,
                         diagnosis, treatment, medications, vitals, temperature_c,
                         weight_kg, health_status, next_follow_up, created_at)
                    SELECT ?, ?, ?, 'demo_seed', 'Demonstration wellness review',
                           'Synthetic demo entry. Not a real examination or clinical recommendation.',
                           'No diagnosis recorded; sample wellness review.',
                           'Routine monitoring only; sample data.',
                           'None recorded in this demonstration entry.',
                           ?, ?, ?, ?, '2026-12-18', '2026-09-18 09:00:00'
                    WHERE NOT EXISTS (
                        SELECT 1 FROM cow_medical_history
                        WHERE cow_id = ? AND doctor_id = ? AND record_type = 'demo_seed'
                    )
                    """,
                    (
                        cow_id,
                        doctor["id"],
                        doctor["full_name"],
                        '{"source":"synthetic demo data"}',
                        round(38.0 + (number % 9) / 10, 1),
                        280 + (number * 13 % 240),
                        "Under Observation" if number % 13 == 0 else "Healthy",
                        cow_id,
                        doctor["id"],
                    ),
                )

        # Ensure the count lands at the requested total, rather than silently
        # reporting success if the archive did not contain the expected base.
        cow_count = conn.execute(
            "SELECT COUNT(*) FROM cows WHERE cow_id IN ('COW001','COW002','COW003') "
            "OR cow_id LIKE 'COW-DEMO-%'"
        ).fetchone()[0]
        doctor_count = conn.execute(
            "SELECT COUNT(*) FROM doctors WHERE email IN (%s)" % ",".join("?" * 10),
            [doctor[1] for doctor in DOCTORS],
        ).fetchone()[0]
        duplicates = conn.execute(
            "SELECT cow_id FROM cows GROUP BY cow_id HAVING COUNT(*) > 1"
        ).fetchall()
        duplicate_history = conn.execute(
            "SELECT cow_id, doctor_id FROM cow_medical_history WHERE record_type = 'demo_seed' "
            "GROUP BY cow_id, doctor_id HAVING COUNT(*) > 1"
        ).fetchall()
        if duplicates or duplicate_history:
            conn.rollback()
            raise RuntimeError("Duplicate demonstration records detected; nothing was committed.")
        if cow_count != 100:
            conn.rollback()
            raise RuntimeError(
                f"Expected exactly 100 demonstration cows after seeding; found {cow_count}."
            )
        conn.commit()
        if not args.no_qr:
            for number in range(1, 101):
                cow_id = f"COW{number:03d}" if number <= 3 else f"COW-DEMO-{number:04d}"
                app.generate_qr_for_cow(cow_id)
        print(
            f"Seeded demonstration data: {cow_count} cows, "
            f"{doctor_count} doctor accounts, 10 farms and 10 demo farmer accounts."
        )
        if created_doctors and generated_doctor_password:
            print(
                f"{created_doctors} new demo doctor account(s) were created with this password "
                f"(shown once): {generated_doctor_password}"
            )
        elif not created_doctors:
            print("Doctor accounts already existed; their passwords were left unchanged.")
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


if __name__ == "__main__":
    main(sys.argv[1:])
