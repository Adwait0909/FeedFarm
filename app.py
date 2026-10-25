"""
QR-Based Cow Digital Passport
------------------------------
A demo module of a Smart Farm Management System.

Lets a farmer register a cow, generates a unique QR code that points to
that cow's public profile ("digital passport"), and lets anyone who scans
the QR code view the cow's information from a phone browser.

Run with: python app.py
"""

import hashlib
import io
import json
import logging
import os
import re
import secrets
import sqlite3
import uuid
from datetime import date, timedelta
from functools import wraps

import qrcode
from dotenv import load_dotenv
from PIL import Image
try:
    import psycopg2
except ImportError:
    psycopg2 = None
try:
    # MySQL is optional: the default database is the bundled SQLite file.
    import mysql.connector
    from mysql.connector import Error as MySQLError
except ImportError:  # pragma: no cover - depends on the local install
    mysql = None

    class MySQLError(Exception):
        """Placeholder so `except MySQLError` still works without MySQL."""

if psycopg2 is not None:
    PostgresError = psycopg2.Error
else:  # pragma: no cover - depends on the local install
    class PostgresError(Exception):
        """Placeholder so `except PostgresError` still works without psycopg2."""

# Errors the routes treat as "database rejected this write" on every backend.
DB_ERRORS = (MySQLError, PostgresError, sqlite3.IntegrityError)
from werkzeug.security import check_password_hash, generate_password_hash
from werkzeug.utils import safe_join

from flask import (
    Flask,
    render_template,
    request,
    redirect,
    url_for,
    flash,
    send_from_directory,
    abort,
    session,
    jsonify,
    Response,
)
from services.farmer_access import owns_cow
from services.db_compat import ServerConnection, ensure_server_schema
from services.animal_health import animal_health_bp
from marketplace_api import marketplace_api

load_dotenv()

# ------------------------------------------------------------------
# App configuration
# ------------------------------------------------------------------

app = Flask(__name__)

app.secret_key = os.environ.get("SECRET_KEY") or os.urandom(32).hex()

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
KISAATH_BUILD_DIR = os.path.join(BASE_DIR, "kisanreact_app", "build")
SCHEME_FRONTEND_DIR = os.path.join(
    BASE_DIR, "integrations", "livestock-scheme-advisor", "frontend"
)
VET_FRONTEND_DIST_DIR = os.path.join(
    BASE_DIR, "integrations", "vet-app", "frontend", "dist"
)

# Optional persistent-storage root (e.g. a Render Disk mounted at /var/data). When DATA_DIR is not
# set - local use, tests - everything stays exactly where it always was, inside the project folder.
DATA_DIR = (os.environ.get("DATA_DIR") or "").strip()

UPLOAD_FOLDER = os.path.join(
    DATA_DIR or BASE_DIR,
    "uploads"
)

QR_FOLDER = os.path.join(
    BASE_DIR,
    "static",
    "qr_codes"
)

ALLOWED_IMAGE_EXTENSIONS = {
    "png",
    "jpg",
    "jpeg"
}

os.makedirs(
    UPLOAD_FOLDER,
    exist_ok=True
)

os.makedirs(
    QR_FOLDER,
    exist_ok=True
)

app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

app.config["MAX_CONTENT_LENGTH"] = (
    5 * 1024 * 1024
)
app.config["SESSION_COOKIE_HTTPONLY"] = True
app.config["SESSION_COOKIE_SAMESITE"] = "Lax"


def configured_site_url():
    """Public address of this site, used inside QR codes.

    Order: SITE_BASE_URL (explicit setting, always wins) -> RENDER_EXTERNAL_URL (set automatically
    by Render, so QR codes point at the live site without extra setup) -> "" (local development,
    where the caller falls back to http://localhost:<port>).
    """
    return (
        os.environ.get("SITE_BASE_URL")
        or os.environ.get("RENDER_EXTERNAL_URL")
        or ""
    ).strip().rstrip("/")


# Send the session cookie over HTTPS only when the site is served over HTTPS.
app.config["SESSION_COOKIE_SECURE"] = configured_site_url().lower().startswith("https://")

# ------------------------------------------------------------------
# CSRF protection
#
# Every cookie-authenticated state-changing request (POST/PUT/PATCH/DELETE) must carry the
# per-session token, as the hidden form field "csrf_token" or the "X-CSRF-Token" header, and
# must come from this site (Origin/Referer check).  The marketplace JSON API (/api/..., /upload)
# authenticates with a bearer token held by the React app, never with cookies, so it is exempt.
# Set app.config["CSRF_PROTECT"] = False only in automated tests that post raw forms.
# ------------------------------------------------------------------

CSRF_SAFE_METHODS = frozenset({"GET", "HEAD", "OPTIONS", "TRACE"})
CSRF_EXEMPT_PREFIXES = ("/api/", "/upload")


def get_csrf_token():
    token = session.get("_csrf")
    if not token:
        token = secrets.token_urlsafe(32)
        session["_csrf"] = token
    return token


@app.context_processor
def inject_csrf_token():
    return {"csrf_token": get_csrf_token}


@app.route("/csrf-token")
def csrf_token_endpoint():
    """Same-origin JavaScript (animal-health, scheme advisor) reads the token from here."""
    response = jsonify({"csrf_token": get_csrf_token()})
    response.headers["Cache-Control"] = "no-store"
    return response


@app.before_request
def protect_against_csrf():
    if request.method in CSRF_SAFE_METHODS:
        return None
    if request.path.startswith(CSRF_EXEMPT_PREFIXES):
        return None
    source = request.headers.get("Origin") or request.headers.get("Referer")
    if source:
        from urllib.parse import urlsplit
        source_host = urlsplit(source).netloc.lower()
        allowed = {request.host.lower()}
        forwarded = request.headers.get("X-Forwarded-Host")
        if forwarded:
            allowed.add(forwarded.split(",")[0].strip().lower())
        if source_host and source_host not in allowed:
            abort(403)
    if not app.config.get("CSRF_PROTECT", True):
        return None
    supplied = request.form.get("csrf_token") or request.headers.get("X-CSRF-Token") or ""
    expected = session.get("_csrf") or ""
    if not expected or not supplied or not secrets.compare_digest(supplied, expected):
        return Response(
            "Security check failed: the form is missing a valid token or your session expired. "
            "Go back, reload the page and try again.",
            status=400,
            mimetype="text/plain",
        )
    return None
app.register_blueprint(marketplace_api)
app.register_blueprint(animal_health_bp)

# Register modular routes (after app exists)
# Voice routes removed: feature deprecated and deleted

# ------------------------------------------------------------------
# Public URL used inside QR codes
# ------------------------------------------------------------------

# macOS 12+ (Monterey and later) reserves port 5000 for the AirPlay Receiver,
# so the default is 5001. Override with PORT in .env if you need another one.
PORT = int(os.environ.get("PORT", "5001"))

SITE_BASE_URL = configured_site_url() or f"http://localhost:{PORT}"

# ------------------------------------------------------------------
# Database configuration
# ------------------------------------------------------------------

DB_CONFIG = {
    "host": os.environ.get(
        "DB_HOST",
        "localhost"
    ),

    "user": os.environ.get(
        "DB_USER",
        "root"
    ),

    "password": os.environ.get(
        "DB_PASSWORD",
        ""
    ),

    "database": os.environ.get(
        "DB_NAME",
        "cow_qr_demo"
    ),

    "charset": "utf8mb4",
}
if os.environ.get("DB_PORT"):
    DB_CONFIG["port"] = int(os.environ["DB_PORT"])

# SQLite database path
DB_PATH = os.path.join(
    DATA_DIR or BASE_DIR,
    "cow_qr_demo.sqlite3"
)

# mysql by default; PostgreSQL is also supported when configured
DB_TYPE = os.environ.get(
    "DB_TYPE",
    "sqlite"
).lower()


# ------------------------------------------------------------------
# SQLite Cursor Wrapper
# ------------------------------------------------------------------

class SQLiteCursor:
    """
    Wrap sqlite3 cursor so the app can use the same
    MySQL-style %s placeholders.
    """

    def __init__(self, cursor):
        self._cursor = cursor

    def execute(self, query, params=()):
        if params:
            query = query.replace(
                "%s",
                "?"
            )

        return self._cursor.execute(
            query,
            tuple(params)
        )

    def executemany(
        self,
        query,
        seq_of_params
    ):
        if seq_of_params:
            query = query.replace(
                "%s",
                "?"
            )

        return self._cursor.executemany(
            query,
            seq_of_params
        )

    def fetchall(self):
        rows = self._cursor.fetchall()

        return [
            dict(row)
            for row in rows
        ]

    def fetchone(self):
        row = self._cursor.fetchone()

        if row is not None:
            return dict(row)

        return None

    def close(self):
        return self._cursor.close()

    def __getattr__(self, name):
        return getattr(
            self._cursor,
            name
        )


# ------------------------------------------------------------------
# SQLite Connection Wrapper
# ------------------------------------------------------------------

class SQLiteConnection:
    """
    Provide the subset of the DB API
    expected by the Flask routes.
    """

    def __init__(self, connection):

        self._conn = connection

        self._conn.row_factory = sqlite3.Row

        self._conn.execute(
            "PRAGMA foreign_keys = ON"
        )

        ensure_sqlite_schema(
            self._conn
        )

    def cursor(self, dictionary=False):

        return SQLiteCursor(
            self._conn.cursor()
        )

    def commit(self):
        return self._conn.commit()

    def rollback(self):
        return self._conn.rollback()

    def close(self):
        return self._conn.close()

    def __getattr__(self, name):
        return getattr(
            self._conn,
            name
        )


# ------------------------------------------------------------------
# SQLite Database Schema
# ------------------------------------------------------------------

def ensure_sqlite_schema(conn):

    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS cows (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            cow_id TEXT NOT NULL UNIQUE,
            cow_name TEXT NOT NULL,
            breed TEXT,
            cow_type TEXT,
            gender TEXT,
            age INTEGER,
            date_of_birth TEXT,
            color TEXT,
            registered_location TEXT,
            owner_name TEXT,
            owner_contact TEXT,
            local_cow_number TEXT,
            farm_identity TEXT,
            qr_code_value TEXT,
            health_status TEXT,
            health_score INTEGER,
            vaccination_status TEXT,
            last_vaccination_date TEXT,
            next_vaccination_date TEXT,
            last_health_check TEXT,
            disease_history TEXT,
            milk_production REAL,
            notes TEXT,
            doctor_name TEXT,
            medical_record TEXT,
            treatment_history TEXT,
            last_treatment_date TEXT,
            next_checkup_date TEXT,
            body_temperature REAL,
            weight_kg REAL,
            pregnancy_status TEXT,
            image_path TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
        """
    )

    table_sql = conn.execute(
        "SELECT sql FROM sqlite_master WHERE type = 'table' AND name = 'cows'"
    ).fetchone()

    if table_sql and "local_cow_number TEXT UNIQUE" in (table_sql[0] or ""):
        conn.execute("ALTER TABLE cows RENAME TO cows_old")
        conn.execute(
            """
            CREATE TABLE cows (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                cow_id TEXT NOT NULL UNIQUE,
                cow_name TEXT NOT NULL,
                breed TEXT,
                cow_type TEXT,
                gender TEXT,
                age INTEGER,
                date_of_birth TEXT,
                color TEXT,
                registered_location TEXT,
                owner_name TEXT,
                owner_contact TEXT,
                local_cow_number TEXT,
                farm_identity TEXT,
                qr_code_value TEXT,
                health_status TEXT,
                health_score INTEGER,
                vaccination_status TEXT,
                last_vaccination_date TEXT,
                next_vaccination_date TEXT,
                last_health_check TEXT,
                disease_history TEXT,
                milk_production REAL,
                notes TEXT,
                doctor_name TEXT,
                medical_record TEXT,
                treatment_history TEXT,
                last_treatment_date TEXT,
                next_checkup_date TEXT,
                body_temperature REAL,
                weight_kg REAL,
                pregnancy_status TEXT,
                image_path TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        conn.execute(
            """
            INSERT INTO cows (
                id, cow_id, cow_name, breed, cow_type, gender, age, date_of_birth, color,
                registered_location, owner_name, owner_contact, local_cow_number, farm_identity,
                qr_code_value, health_status, health_score, vaccination_status,
                last_vaccination_date, next_vaccination_date, last_health_check,
                disease_history, milk_production, notes, doctor_name, medical_record,
                treatment_history, last_treatment_date, next_checkup_date, body_temperature,
                weight_kg, pregnancy_status, image_path, created_at
            )
            SELECT
                id, cow_id, cow_name, breed, cow_type, gender, age, date_of_birth, color,
                registered_location, owner_name, owner_contact, local_cow_number, farm_identity,
                qr_code_value, health_status, health_score, vaccination_status,
                last_vaccination_date, next_vaccination_date, last_health_check,
                disease_history, milk_production, notes, doctor_name, medical_record,
                treatment_history, last_treatment_date, next_checkup_date, body_temperature,
                weight_kg, pregnancy_status, image_path, created_at
            FROM cows_old
            """
        )
        conn.execute("DROP TABLE cows_old")
        conn.commit()

    for column_sql in [
        "ALTER TABLE cows ADD COLUMN local_cow_number TEXT",
        "ALTER TABLE cows ADD COLUMN farm_identity TEXT",
        "ALTER TABLE cows ADD COLUMN qr_code_value TEXT",
        "ALTER TABLE cows ADD COLUMN next_vaccination_date TEXT",
        "ALTER TABLE cows ADD COLUMN doctor_name TEXT",
        "ALTER TABLE cows ADD COLUMN medical_record TEXT",
        "ALTER TABLE cows ADD COLUMN treatment_history TEXT",
        "ALTER TABLE cows ADD COLUMN last_treatment_date TEXT",
        "ALTER TABLE cows ADD COLUMN next_checkup_date TEXT",
        "ALTER TABLE cows ADD COLUMN body_temperature REAL",
        "ALTER TABLE cows ADD COLUMN weight_kg REAL",
        "ALTER TABLE cows ADD COLUMN pregnancy_status TEXT",
        "ALTER TABLE cows ADD COLUMN farm_id TEXT",
        "ALTER TABLE cows ADD COLUMN farmer_id INTEGER",
    ]:
        try:
            conn.execute(column_sql)
        except sqlite3.OperationalError:
            pass

    for index_row in conn.execute("PRAGMA index_list('cows')").fetchall():
        index_name = index_row[1]
        if index_name.startswith("sqlite_autoindex_"):
            columns = [
                info_row[2]
                for info_row in conn.execute(f"PRAGMA index_info('{index_name}')").fetchall()
            ]
            if columns == ["local_cow_number"]:
                conn.execute(f"DROP INDEX IF EXISTS '{index_name}'")

    conn.execute(
        """
        CREATE UNIQUE INDEX IF NOT EXISTS idx_cows_farm_local_number
        ON cows (farm_id, local_cow_number)
        """
    )

    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS farmers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            full_name TEXT NOT NULL,
            email TEXT NOT NULL UNIQUE,
            phone TEXT,
            password_hash TEXT NOT NULL,
            village TEXT,
            taluka TEXT,
            district TEXT,
            state TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
        """
    )

    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS farms (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            farmer_id INTEGER NOT NULL,
            farm_id TEXT NOT NULL UNIQUE,
            farm_name TEXT NOT NULL,
            village TEXT,
            taluka TEXT,
            district TEXT,
            state TEXT,
            service_area TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (farmer_id) REFERENCES farmers(id) ON DELETE CASCADE
        )
        """
    )

    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS veterinary_directory (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            full_name TEXT NOT NULL,
            clinic_name TEXT,
            specialization TEXT,
            district TEXT,
            city TEXT,
            phone TEXT,
            email TEXT,
            service_area TEXT,
            location_note TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
        """
    )

    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS farmers_assistance_requests (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            farmer_id INTEGER NOT NULL,
            cow_id TEXT,
            request_type TEXT,
            description TEXT,
            status TEXT DEFAULT 'pending',
            veterinarian_name TEXT,
            veterinarian_contact TEXT,
            doctor_response TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (farmer_id) REFERENCES farmers(id) ON DELETE CASCADE,
            FOREIGN KEY (cow_id) REFERENCES cows(cow_id) ON DELETE SET NULL
        )
        """
    )

    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS doctors (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            full_name TEXT NOT NULL,
            email TEXT NOT NULL UNIQUE,
            password_hash TEXT NOT NULL,
            specialization TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
        """
    )

    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS cow_medical_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            cow_id TEXT NOT NULL,
            doctor_id INTEGER,
            doctor_name TEXT,
            record_type TEXT,
            title TEXT,
            summary TEXT,
            diagnosis TEXT,
            treatment TEXT,
            medications TEXT,
            vitals TEXT,
            temperature_c REAL,
            weight_kg REAL,
            health_status TEXT,
            next_follow_up TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (cow_id) REFERENCES cows(cow_id) ON DELETE CASCADE
        )
        """
    )

    # Doctors answer farmer requests in the same table; upgrade older databases in place.
    request_columns = {
        row[1] for row in conn.execute("PRAGMA table_info(farmers_assistance_requests)").fetchall()
    }
    if "doctor_response" not in request_columns:
        conn.execute("ALTER TABLE farmers_assistance_requests ADD COLUMN doctor_response TEXT")

    # Keep the medical timeline tied to a doctor account as well as a
    # display-name snapshot. Existing databases are upgraded in place.
    history_columns = {
        row[1] for row in conn.execute("PRAGMA table_info(cow_medical_history)").fetchall()
    }
    if "doctor_id" not in history_columns:
        conn.execute("ALTER TABLE cow_medical_history ADD COLUMN doctor_id INTEGER")
    conn.execute(
        "CREATE INDEX IF NOT EXISTS idx_medical_history_doctor_cow "
        "ON cow_medical_history (doctor_id, cow_id)"
    )

    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS veterinary_assistance_requests (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            cow_id TEXT NOT NULL,
            farmer_name TEXT,
            farmer_contact TEXT,
            request_type TEXT,
            description TEXT,
            status TEXT DEFAULT 'pending',
            doctor_response TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (cow_id) REFERENCES cows(cow_id) ON DELETE CASCADE
        )
        """
    )

    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS found_reports (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            cow_id TEXT NOT NULL,
            finder_name TEXT NOT NULL,
            finder_contact TEXT NOT NULL,
            current_area TEXT,
            message TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (cow_id)
                REFERENCES cows(cow_id)
                ON DELETE CASCADE
        )
        """
    )

    conn.commit()

    seed_default_data(conn)


def seed_default_data(conn):
    """Insert the bundled sample cows, vet directory and first doctor account when those tables are empty.

    Works with a sqlite3 connection or the placeholder adapter used for MySQL / PostgreSQL.
    """

    # --------------------------------------------------------------
    # Add sample cows only if database is empty
    # --------------------------------------------------------------

    cow_count = conn.execute(
        "SELECT COUNT(*) AS total FROM cows"
    ).fetchone()[0]

    if cow_count == 0:

        sample_cows = [

            (
                "COW001",
                "Ganga",
                "Gir",
                "Dairy",
                "Female",
                4,
                "2022-03-14",
                "Reddish Brown",
                "Shivapur Dairy Farm, Pune",
                "Ramesh Patil",
                "9876543210",
                "C-001",
                "Farm-01",
                f"{SITE_BASE_URL}/cow/COW001",
                "Healthy",
                92,
                "Up to date",
                "2026-05-10",
                "2026-10-10",
                "2026-08-20",
                "None reported",
                12.50,
                "Calm temperament, good milk yield through the year.",
                "Dr. Sharma",
                "Routine consultation completed.",
                "Vitamin support provided.",
                "2026-09-14",
                "2026-10-15",
                38.2,
                420,
                "Open",
                None,
            ),

            (
                "COW002",
                "Lakshmi",
                "Sahiwal",
                "Dairy",
                "Female",
                5,
                "2021-07-02",
                "Light Brown",
                "Shivapur Dairy Farm, Pune",
                "Ramesh Patil",
                "9876543210",
                "C-002",
                "Farm-01",
                f"{SITE_BASE_URL}/cow/COW002",
                "Healthy",
                88,
                "Up to date",
                "2026-04-22",
                "2026-09-30",
                "2026-08-15",
                "Minor mastitis (treated, 2024)",
                10.80,
                "Requires slightly warmer shelter in winter.",
                "Dr. Sharma",
                "Normal routine follow-up.",
                "No treatment required.",
                "2026-08-12",
                "2026-09-25",
                38.0,
                405,
                "Open",
                None,
            ),

            (
                "COW003",
                "Radha",
                "Red Sindhi",
                "Dairy",
                "Female",
                3,
                "2023-01-19",
                "Deep Red",
                "Shivapur Dairy Farm, Pune",
                "Sunita Patil",
                "9876501234",
                "C-003",
                "Farm-02",
                f"{SITE_BASE_URL}/cow/COW003",
                "Under Observation",
                75,
                "Pending",
                "2025-11-05",
                "2026-10-01",
                "2026-08-25",
                "Recovering from foot infection",
                8.20,
                "Vaccination booster due next month.",
                "Dr. Mehta",
                "Recovery under observation after infection.",
                "Foot wash and antibiotic course.",
                "2026-09-01",
                "2026-10-05",
                39.1,
                360,
                "Open",
                None,
            ),
        ]

        conn.executemany(
            """
            INSERT INTO cows
            (
                cow_id,
                cow_name,
                breed,
                cow_type,
                gender,
                age,
                date_of_birth,
                color,
                registered_location,
                owner_name,
                owner_contact,
                local_cow_number,
                farm_identity,
                qr_code_value,
                health_status,
                health_score,
                vaccination_status,
                last_vaccination_date,
                next_vaccination_date,
                last_health_check,
                disease_history,
                milk_production,
                notes,
                doctor_name,
                medical_record,
                treatment_history,
                last_treatment_date,
                next_checkup_date,
                body_temperature,
                weight_kg,
                pregnancy_status,
                image_path
            )
            VALUES (
                ?,
                ?,
                ?,
                ?,
                ?,
                ?,
                ?,
                ?,
                ?,
                ?,
                ?,
                ?,
                ?,
                ?,
                ?,
                ?,
                ?,
                ?,
                ?,
                ?,
                ?,
                ?,
                ?,
                ?,
                ?,
                ?,
                ?,
                ?,
                ?,
                ?,
                ?,
                ?
            )
            """,
            sample_cows
        )

        conn.commit()

    provider_count = conn.execute(
        "SELECT COUNT(*) AS total FROM veterinary_directory"
    ).fetchone()[0]

    if provider_count == 0:
        conn.executemany(
            """
            INSERT INTO veterinary_directory (
                full_name,
                clinic_name,
                specialization,
                district,
                city,
                phone,
                email,
                service_area,
                location_note
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            [
                (
                    "Dr. Asha Mehta",
                    "Asha Veterinary Clinic",
                    "General Veterinary Medicine",
                    "Pune",
                    "Pune",
                    "9822045678",
                    "asha@vetcare.in",
                    "Pune, Khed, Chakan",
                    "Near district veterinary hospital",
                ),
                (
                    "Dr. Rohan Kulkarni",
                    "Green Valley Animal Care",
                    "Dairy Health",
                    "Satara",
                    "Satara",
                    "9867123456",
                    "rohank@greenvalleyvet.in",
                    "Satara, Koregaon",
                    "Primary care for dairy cattle",
                ),
            ],
        )
        conn.commit()

    doctor_count = conn.execute(
        "SELECT COUNT(*) AS total FROM doctors"
    ).fetchone()[0]

    if doctor_count == 0:
        _doctor_password = os.environ.get("DOCTOR_PASSWORD")
        if not _doctor_password or _doctor_password in {"replace-with-a-strong-password", "Vet@2026"}:
            _doctor_password = None
        _doctor_unusable = not _doctor_password
        if not _doctor_password:
            # Nobody knows this value: the account stays unusable until a password is set
            # with `python scripts/reset_doctor_passwords.py`.
            _doctor_password = secrets.token_urlsafe(32)
            logging.getLogger("farm2feed").warning(
                "DOCTOR_PASSWORD is not set. The initial doctor account was created without a "
                "usable password; run `python scripts/reset_doctor_passwords.py` to set one."
            )
        conn.execute(
            """
            INSERT INTO doctors (full_name, email, password_hash, specialization)
            VALUES (?, ?, ?, ?)
            """,
            (
                "Dr. Asha Mehta",
                "doctor@farmcare.local",
                ("unset$" + secrets.token_urlsafe(24)) if _doctor_unusable else generate_password_hash(_doctor_password),
                "Veterinary Medicine",
            )
        )
        conn.commit()


# ------------------------------------------------------------------
# SQLite Connection
# ------------------------------------------------------------------

def get_sqlite_connection():

    return SQLiteConnection(
        sqlite3.connect(
            DB_PATH
        )
    )


# ------------------------------------------------------------------
# Database Connection
# ------------------------------------------------------------------

def get_db_connection():

    global DB_TYPE

    if DB_TYPE == "sqlite":
        return get_sqlite_connection()

    if DB_TYPE in ("postgres", "postgresql"):
        if psycopg2 is None:
            app.logger.warning("psycopg2 is not installed. Using SQLite fallback instead.")
            DB_TYPE = "sqlite"
            return get_sqlite_connection()
        try:
            pg_config = {
                "host": os.environ.get("PG_HOST", "localhost"),
                "port": os.environ.get("PG_PORT", "5432"),
                "user": os.environ.get("PG_USER", "postgres"),
                "password": os.environ.get("PG_PASSWORD", "postgres"),
                "dbname": os.environ.get("PG_NAME", "cow_qr_demo"),
            }
            raw = psycopg2.connect(**pg_config)
            try:
                ensure_server_schema(raw, "postgres", BASE_DIR, seed_default_data)
            except Exception:
                raw.close()
                raise
            return ServerConnection(raw, "postgres")
        except Exception as err:
            app.logger.warning("PostgreSQL unavailable. Using SQLite fallback instead. Details: %s", err)
            DB_TYPE = "sqlite"
            return get_sqlite_connection()

    if mysql is None:
        app.logger.warning("mysql-connector-python is not installed. Using SQLite fallback instead.")
        DB_TYPE = "sqlite"
        return get_sqlite_connection()

    try:
        raw = mysql.connector.connect(**DB_CONFIG)
        try:
            ensure_server_schema(raw, "mysql", BASE_DIR, seed_default_data)
        except Exception:
            raw.close()
            raise
        return ServerConnection(raw, "mysql")

    except Exception as err:
        app.logger.warning(
            "MySQL unavailable at %s. Using SQLite fallback instead. Details: %s",
            DB_CONFIG.get("host"),
            err,
        )
        DB_TYPE = "sqlite"
        return get_sqlite_connection()


# ------------------------------------------------------------------
# Image Validation
# ------------------------------------------------------------------

def allowed_image(filename):

    return (
        "." in filename
        and
        filename.rsplit(
            ".",
            1
        )[1].lower()
        in ALLOWED_IMAGE_EXTENSIONS
    )


def to_int_or_none(value):
    """Return a non-negative int, or None when the value is blank or not numeric."""
    try:
        text = str(value).strip() if value is not None else ""
        if not text:
            return None
        number = int(float(text))
        return number if number >= 0 else None
    except (TypeError, ValueError, OverflowError):
        return None


def to_float_or_none(value):
    """Return a non-negative float, or None when the value is blank or not numeric."""
    try:
        text = str(value).strip() if value is not None else ""
        if not text:
            return None
        number = float(text)
        return number if number >= 0 and number == number and number != float("inf") else None
    except (TypeError, ValueError):
        return None


def require_doctor_login(view):
    @wraps(view)
    def wrapped_view(*args, **kwargs):
        if not session.get("doctor_id"):
            flash("Please log in as a veterinarian to continue.", "error")
            return redirect(url_for("doctor_login"))
        return view(*args, **kwargs)
    return wrapped_view


def generate_farm_id():
    return f"FARM-{uuid.uuid4().hex[:8].upper()}"


def generate_cow_uid():
    return f"COW-{uuid.uuid4().hex[:8].upper()}"


def require_farmer_login(view):
    @wraps(view)
    def wrapped_view(*args, **kwargs):
        if not session.get("farmer_id"):
            flash("Please log in as a farmer to continue.", "error")
            return redirect(url_for("farmer_login"))
        return view(*args, **kwargs)
    return wrapped_view


def require_farmer_or_doctor_login(view):
    """Cow registration needs a signed-in farmer (cow joins their herd) or veterinarian."""
    @wraps(view)
    def wrapped_view(*args, **kwargs):
        if not (session.get("farmer_id") or session.get("doctor_id")):
            flash("Please sign in as a farmer or veterinarian to register a cow.", "error")
            return redirect(url_for("farmer_login"))
        return view(*args, **kwargs)
    return wrapped_view


def current_lang():
    return (session.get("lang") or "en").lower()


def t(key, default=None):
    lang = current_lang()
    lookup = {
        "en": {
            "Dashboard": "Dashboard",
            "My Farm": "My Farm",
            "My Cows": "My Cows",
            "Farm Profile": "Farm Profile",
            "Register Cow": "Register Cow",
            "Vet Help": "Vet Help",
            "Find Vet": "Find Vet",
            "Logout": "Logout",
            "Login": "Login",
            "Register": "Register",
            "Farm Details": "Farm Details",
            "Farmer Dashboard": "Farmer Dashboard",
            "Welcome back": "Welcome back",
            "Farm ID": "Farm ID",
            "Cow UID": "Cow UID",
            "QR Code": "QR Code",
            "Health Alerts": "Health Alerts",
            "Total cows": "Total cows",
            "Set language": "Set language",
            "English": "English",
            "Marathi": "Marathi",
        },
        "mr": {
            "Dashboard": "डॅशबोर्ड",
            "My Farm": "माझे शेत",
            "My Cows": "माझ्या गायी",
            "Farm Profile": "शेत प्रोफाइल",
            "Register Cow": "गाय नोंदणी",
            "Vet Help": "पशुवैद्यकीय मदत",
            "Find Vet": "वैद्य शोधा",
            "Logout": "बाहेर पडा",
            "Login": "लॉगिन",
            "Register": "नोंदणी",
            "Farm Details": "शेत तपशील",
            "Farmer Dashboard": "शेतकरी डॅशबोर्ड",
            "Welcome back": "पुन्हा स्वागत",
            "Farm ID": "शेत आयडी",
            "Cow UID": "गायी UID",
            "QR Code": "क्यूआर कोड",
            "Health Alerts": "आरोग्य सूचना",
            "Total cows": "एकूण गाय",
            "Set language": "भाषा निवडा",
            "English": "इंग्रजी",
            "Marathi": "मराठी",
        },
    }
    data = lookup.get(lang, lookup["en"])
    return data.get(key, default or key)


def normalize_cow_search(term):
    if term is None:
        return ""
    return term.strip()


def parse_qr_reference(value):
    if not value:
        return None
    candidate = value.strip()
    if not candidate:
        return None
    if "/cow/" in candidate:
        pos = candidate.rfind("/cow/")
        candidate = candidate[pos + 5:]
    if "?" in candidate:
        candidate = candidate.split("?", 1)[0]
    if "&" in candidate:
        candidate = candidate.split("&", 1)[0]
    if candidate.startswith("http://") or candidate.startswith("https://"):
        return None
    return candidate.strip()


def get_ai_screening(cow):
    risk_score = 0
    reasons = []
    recommendations = []

    if cow.get("health_score") is not None:
        score = int(cow["health_score"])
        if score < 50:
            risk_score += 35
            reasons.append("Low health score")
            recommendations.append("Arrange immediate examination and review treatment plan.")
        elif score < 75:
            risk_score += 18
            reasons.append("Moderate health score")
            recommendations.append("Monitor health closely and schedule a follow-up check.")
        else:
            risk_score += 5

    if cow.get("health_status") in ("Under Observation", "Sick"):
        risk_score += 25
        reasons.append("Current health status requires monitoring")
        recommendations.append("Follow clinician review protocol and observe for worsening signs.")

    if cow.get("vaccination_status") in ("Pending", "Overdue"):
        risk_score += 20
        reasons.append("Vaccination is not current")
        recommendations.append("Schedule vaccination and check due dates.")

    if cow.get("disease_history") and "none" not in str(cow["disease_history"]).lower():
        risk_score += 15
        reasons.append("Disease history is present")
        recommendations.append("Review previous disease history before discharge or follow-up.")

    if cow.get("body_temperature") is not None:
        temp = float(cow["body_temperature"])
        if temp > 39.5 or temp < 37.0:
            risk_score += 20
            reasons.append("Temperature indicates possible concern")
            recommendations.append("Check vital signs and consider additional clinical review.")

    if not reasons:
        risk_level = "Low"
    elif risk_score >= 70:
        risk_level = "High"
    elif risk_score >= 40:
        risk_level = "Moderate"
    else:
        risk_level = "Low"

    return {
        "risk_level": risk_level,
        "score": min(risk_score, 100),
        "reasons": reasons or ["No major issues detected in the current record."],
        "recommendations": recommendations or ["Maintain regular monitoring and routine follow-up."],
        "note": "This is an AI-assisted screening support tool and should not be treated as a definitive diagnosis.",
    }


# ------------------------------------------------------------------
# Save Cow Image
# ------------------------------------------------------------------

MAX_COW_PHOTO_BYTES = 4 * 1024 * 1024  # stays under the 5 MB request limit together with the form fields


def cow_photo_url(filename):
    """URL of an uploaded cow photo, or None when there is no photo or its file is missing."""
    if not filename or "/" in filename or "\\" in filename or ".." in filename:
        return None
    if not os.path.isfile(os.path.join(app.config["UPLOAD_FOLDER"], filename)):
        return None
    return url_for("uploaded_file", filename=filename)


@app.context_processor
def inject_cow_photo_helper():
    return {"cow_photo_url": cow_photo_url}


@app.errorhandler(413)
def upload_too_large(_error):
    return Response(
        "That upload is too large (limit 5 MB). Go back and choose a smaller photo.",
        status=413,
        mimetype="text/plain",
    )


def save_cow_image(file_storage):

    """
    Validate and save uploaded cow photo.

    Returns:
        filename if valid image uploaded
        None if no image uploaded
    """

    if (
        not file_storage
        or
        file_storage.filename == ""
    ):
        return None

    if not allowed_image(
        file_storage.filename
    ):
        raise ValueError(
            "Only PNG, JPG or JPEG images are allowed."
        )

    ext = file_storage.filename.rsplit(
        ".",
        1
    )[1].lower()

    # Check the real content (not just the extension) before anything is written to disk.
    data = file_storage.stream.read(MAX_COW_PHOTO_BYTES + 1)
    if not data:
        raise ValueError("The selected photo is empty.")
    if len(data) > MAX_COW_PHOTO_BYTES:
        raise ValueError("The photo is larger than 5 MB. Please choose a smaller image.")
    try:
        with Image.open(io.BytesIO(data)) as probe:
            detected = (probe.format or "").upper()
            probe.verify()
    except Exception:
        raise ValueError("That file is not a valid image.")
    if detected not in {"JPEG", "PNG"}:
        raise ValueError("Only PNG, JPG or JPEG images are allowed.")
    file_storage.stream.seek(0)

    unique_name = (
        f"{uuid.uuid4().hex}.{ext}"
    )

    file_storage.save(
        os.path.join(
            app.config["UPLOAD_FOLDER"],
            unique_name
        )
    )

    return unique_name


# ------------------------------------------------------------------
# Generate QR Code
# ------------------------------------------------------------------

def row_value(row, key, index=0):
    """Read a column from a dict-like row or a plain tuple row (cursor styles differ by backend)."""
    return row[key] if hasattr(row, "keys") else row[index]


COW_ID_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,63}$")


def is_safe_cow_id(cow_id):
    """Cow ids end up in URLs and in the QR file name, so keep them to letters, digits, . _ -"""
    return bool(COW_ID_PATTERN.match(cow_id or "")) and ".." not in cow_id


def generate_qr_for_cow(cow_id):

    """
    Create QR code for a cow.

    QR contains only the public profile URL.
    """

    if not is_safe_cow_id(cow_id):
        raise ValueError("Unsafe cow id; refusing to build a file path from it.")

    profile_url = (
        f"{SITE_BASE_URL}/cow/{cow_id}"
    )

    qr_img = qrcode.make(
        profile_url
    )

    qr_path = os.path.join(
        QR_FOLDER,
        f"{cow_id}.png"
    )

    qr_img.save(
        qr_path
    )

    return f"{cow_id}.png"


# ==================================================================
# ROUTES
# ==================================================================


# ------------------------------------------------------------------
# Home
# ------------------------------------------------------------------

@app.route("/")
def index():
    return render_template(
        "cow_home.html",
        lang=current_lang(),
    )


@app.route("/kisaath", defaults={"path": ""})
@app.route("/kisaath/", defaults={"path": ""})
@app.route("/kisaath/<path:path>")
def kisaath(path):
    """Serve the Kisaath React application and its static assets on this port."""
    if not os.path.isdir(KISAATH_BUILD_DIR):
        abort(503, description="Kisaath frontend build is missing. Run npm run build in kisanreact_app.")
    built_file = safe_join(KISAATH_BUILD_DIR, path) if path else None
    if built_file and os.path.isfile(built_file):
        return send_from_directory(KISAATH_BUILD_DIR, path)
    return send_from_directory(KISAATH_BUILD_DIR, "index.html")


@app.route("/farmer/schemes/", defaults={"asset": "index.html"})
@app.route("/farmer/schemes/<path:asset>")
@require_farmer_login
def livestock_scheme_advisor(asset):
    """Serve the scheme advisor only to authenticated farmer accounts."""
    if not os.path.isfile(os.path.join(SCHEME_FRONTEND_DIR, asset)):
        abort(404)
    return send_from_directory(SCHEME_FRONTEND_DIR, asset)


@app.route("/veterinary/", defaults={"asset": ""})
@app.route("/veterinary/<path:asset>")
def veterinary_assistance(asset):
    """Public veterinary locator UI; API data is served by the unified ASGI app."""
    if not os.path.isdir(VET_FRONTEND_DIST_DIR):
        abort(503, description="Veterinary frontend build is missing. Rebuild integrations/vet-app/frontend.")
    requested = os.path.join(VET_FRONTEND_DIST_DIR, asset) if asset else ""
    if asset and os.path.isfile(requested):
        return send_from_directory(VET_FRONTEND_DIST_DIR, asset)
    return send_from_directory(VET_FRONTEND_DIST_DIR, "index.html")


# ------------------------------------------------------------------
# Uploaded Images
# ------------------------------------------------------------------

@app.route("/uploads/<path:filename>")
def uploaded_file(filename):

    return send_from_directory(
        app.config["UPLOAD_FOLDER"],
        filename
    )


# ------------------------------------------------------------------
# Doctor Portal
# ------------------------------------------------------------------

# Passwords that were published in earlier releases / demo documentation. They are never
# accepted for a doctor login unless demo mode is switched on explicitly (FARM2FEED_DEMO_MODE=1).
KNOWN_DEFAULT_DOCTOR_PASSWORDS = frozenset({"Vet@2026", "replace-with-a-strong-password"})


def demo_mode_enabled():
    return os.environ.get("FARM2FEED_DEMO_MODE", "").strip().lower() in {"1", "true", "yes", "on"}


@app.route("/doctor/login", methods=["GET", "POST"])
def doctor_login():
    if session.get("doctor_id"):
        return redirect(url_for("doctor_dashboard"))

    if request.method == "GET":
        return render_template("doctor_login.html")

    email = (request.form.get("email") or "").strip().lower()
    password = request.form.get("password") or ""

    if not email or not password:
        flash("Email and password are required.", "error")
        return render_template("doctor_login.html")

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute(
            "SELECT * FROM doctors WHERE email = %s",
            (email,)
        )
        doctor = cursor.fetchone()
    finally:
        cursor.close()
        conn.close()

    if not doctor or not check_password_hash(doctor["password_hash"], password):
        flash("Invalid doctor credentials.", "error")
        return render_template("doctor_login.html")

    if password in KNOWN_DEFAULT_DOCTOR_PASSWORDS and not demo_mode_enabled():
        app.logger.warning("Doctor login refused: account %s still uses a published demo password.", doctor["id"])
        flash(
            "This account still uses a published demo password, so sign-in is blocked. "
            "Ask the administrator to run: python scripts/reset_doctor_passwords.py",
            "error",
        )
        return render_template("doctor_login.html")

    session["doctor_id"] = doctor["id"]
    session["doctor_name"] = doctor["full_name"]
    flash("Welcome back to the veterinary dashboard.", "success")
    return redirect(url_for("doctor_dashboard"))


@app.route("/doctor/logout")
def doctor_logout():
    session.pop("doctor_id", None)
    session.pop("doctor_name", None)
    flash("You have been logged out.", "success")
    return redirect(url_for("doctor_login"))


@app.route("/farmer/register", methods=["GET", "POST"])
def farmer_register():
    if session.get("farmer_id"):
        session.pop("farmer_id", None)
        session.pop("farmer_name", None)

    if request.method == "GET":
        return render_template("farmer_register.html")

    full_name = (request.form.get("full_name") or "").strip()
    email = (request.form.get("email") or "").strip().lower()
    phone = (request.form.get("phone") or "").strip()
    password = request.form.get("password") or ""
    confirm = request.form.get("confirm_password") or ""

    if not full_name or not email or not phone or not password:
        flash("Please complete all required farmer fields.", "error")
        return render_template("farmer_register.html")

    if len(password) < 6:
        flash("Password must be at least 6 characters long.", "error")
        return render_template("farmer_register.html")

    if password != confirm:
        flash("Passwords do not match. Please re-enter them.", "error")
        return render_template("farmer_register.html")

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("SELECT * FROM farmers WHERE email = %s", (email,))
        existing = cursor.fetchone()
        if existing:
            flash("A farmer profile with this email already exists.", "error")
            return render_template("farmer_register.html")

        cursor.execute(
            """
            INSERT INTO farmers (full_name, email, phone, password_hash)
            VALUES (%s, %s, %s, %s)
            """,
            (full_name, email, phone, generate_password_hash(password)),
        )
        conn.commit()
        farmer_id = cursor.lastrowid
    finally:
        cursor.close()
        conn.close()

    session["farmer_id"] = farmer_id
    session["farmer_name"] = full_name
    flash("Farmer account created successfully.", "success")
    return redirect(url_for("farmer_dashboard"))


@app.route("/farmer/login", methods=["GET", "POST"])
def farmer_login():
    if session.get("farmer_id"):
        return redirect(url_for("farmer_dashboard"))

    if request.method == "GET":
        return render_template("farmer_login.html")

    email = (request.form.get("email") or "").strip().lower()
    password = request.form.get("password") or ""

    if not email or not password:
        flash("Email and password are required.", "error")
        return render_template("farmer_login.html")

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("SELECT * FROM farmers WHERE email = %s", (email,))
        farmer = cursor.fetchone()
    finally:
        cursor.close()
        conn.close()

    if not farmer or not check_password_hash(farmer["password_hash"], password):
        flash("Invalid farmer credentials.", "error")
        return render_template("farmer_login.html")

    session["farmer_id"] = farmer["id"]
    session["farmer_name"] = farmer["full_name"]
    flash("Welcome to your farm dashboard.", "success")
    return redirect(url_for("farmer_dashboard"))


@app.route("/farmer/logout")
def farmer_logout():
    session.pop("farmer_id", None)
    session.pop("farmer_name", None)
    flash("You have been logged out.", "success")
    return redirect(url_for("farmer_login"))


@app.route("/set_language/<lang>")
def set_language(lang):
    if lang in {"en", "mr"}:
        session["lang"] = lang
    return redirect(request.referrer or url_for("index"))


@app.route("/farmer")
@require_farmer_login
def farmer_dashboard():
    farmer_id = session["farmer_id"]
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        # Load farmer profile
        cursor.execute("SELECT * FROM farmers WHERE id = %s", (farmer_id,))
        farmer = cursor.fetchone()

        # Farms belonging to this farmer only
        cursor.execute("SELECT * FROM farms WHERE farmer_id = %s ORDER BY created_at DESC", (farmer_id,))
        farms = cursor.fetchall()

        if farms:
            active_farm_id = session.get("farm_id")
            farm = next((entry for entry in farms if entry.get("farm_id") == active_farm_id), farms[0])
            session["farm_id"] = farm["farm_id"]
        else:
            farm = None
            session.pop("farm_id", None)

        # Only query cows owned by this farmer (and optionally restricted to active farm)
        if farm:
            cursor.execute(
                "SELECT * FROM cows WHERE farmer_id = %s AND farm_id = %s ORDER BY created_at DESC",
                (farmer_id, farm["farm_id"]),
            )
        else:
            cursor.execute(
                "SELECT * FROM cows WHERE farmer_id = %s ORDER BY created_at DESC",
                (farmer_id,),
            )
        cows = cursor.fetchall()
    finally:
        cursor.close()
        conn.close()

    alerts = []
    for cow in cows:
        if cow.get("health_status") in ("Under Observation", "Sick"):
            alerts.append({"cow_id": cow["cow_id"], "message": f"{cow['cow_name']} needs veterinary attention."})
        elif cow.get("vaccination_status") in ("Pending", "Overdue"):
            alerts.append({"cow_id": cow["cow_id"], "message": f"{cow['cow_name']} has vaccination due."})
        elif cow.get("next_checkup_date") and cow.get("next_checkup_date") <= str(date.today()):
            alerts.append({"cow_id": cow["cow_id"], "message": f"{cow['cow_name']} requires follow-up checkup."})

    return render_template(
        "farmer_dashboard.html",
        farmer=farmer,
        farm=farm,
        farms=farms,
        cows=cows,
        alerts=alerts,
        total=len(cows),
    )


@app.route("/farmer/farm", methods=["GET", "POST"])
@require_farmer_login
def farmer_farm():
    farmer_id = session["farmer_id"]
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("SELECT * FROM farmers WHERE id = %s", (farmer_id,))
        farmer = cursor.fetchone()
        cursor.execute("SELECT * FROM farms WHERE farmer_id = %s ORDER BY created_at DESC", (farmer_id,))
        farms = cursor.fetchall()
        farm = None
        if farms:
            active_farm_id = request.form.get("farm_id") or session.get("farm_id") or farms[0]["farm_id"]
            farm = next((entry for entry in farms if entry.get("farm_id") == active_farm_id), farms[0])
            session["farm_id"] = farm["farm_id"]
    finally:
        cursor.close()
        conn.close()

    if request.method == "GET":
        return render_template("farmer_farm.html", farmer=farmer, farm=farm, farms=farms)

    required = ["farm_name", "village", "taluka", "district", "state"]
    missing = [field for field in required if not (request.form.get(field) or "").strip()]
    if missing:
        flash("Please fill in the required farm details.", "error")
        return render_template("farmer_farm.html", farmer=farmer, farm=farm, farms=farms)

    farm_values = {
        "farm_name": (request.form.get("farm_name") or "").strip(),
        "village": (request.form.get("village") or "").strip(),
        "taluka": (request.form.get("taluka") or "").strip(),
        "district": (request.form.get("district") or "").strip(),
        "state": (request.form.get("state") or "").strip(),
        "service_area": (request.form.get("service_area") or "").strip(),
    }

    selected_farm_id = request.form.get("farm_id")
    conn = get_db_connection(); cursor = conn.cursor()
    try:
        if selected_farm_id:
            cursor.execute(
                """
                UPDATE farms
                SET farm_name = %s, village = %s, taluka = %s, district = %s, state = %s, service_area = %s
                WHERE farmer_id = %s AND farm_id = %s
                """,
                (farm_values["farm_name"], farm_values["village"], farm_values["taluka"], farm_values["district"], farm_values["state"], farm_values["service_area"], farmer_id, selected_farm_id),
            )
            if cursor.rowcount:
                session["farm_id"] = selected_farm_id
            else:
                selected_farm_id = None
        if not selected_farm_id:
            generated_farm_id = generate_farm_id()
            cursor.execute(
                """
                INSERT INTO farms (farmer_id, farm_id, farm_name, village, taluka, district, state, service_area)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                """,
                (farmer_id, generated_farm_id, farm_values["farm_name"], farm_values["village"], farm_values["taluka"], farm_values["district"], farm_values["state"], farm_values["service_area"]),
            )
            session["farm_id"] = generated_farm_id
        conn.commit()
        flash("Farm profile saved successfully.", "success")
    except DB_ERRORS:
        conn.rollback(); flash("Unable to save the farm profile. Please try again.", "error")
    finally:
        cursor.close(); conn.close()

    return redirect(url_for("farmer_dashboard"))


@app.route("/farmer/cows/new", methods=["GET", "POST"])
@require_farmer_login
def farmer_register_cow():
    farmer_id = session["farmer_id"]
    conn = get_db_connection(); cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("SELECT * FROM farms WHERE farmer_id = %s ORDER BY created_at DESC", (farmer_id,))
        farms = cursor.fetchall()
        active_farm_id = session.get("farm_id")
        farm = next((entry for entry in farms if entry.get("farm_id") == active_farm_id), farms[0] if farms else None)
        if farm:
            session["farm_id"] = farm["farm_id"]
        cursor.execute("SELECT * FROM farmers WHERE id = %s", (farmer_id,))
        farmer = cursor.fetchone()
    finally:
        cursor.close(); conn.close()

    if not farm:
        flash("Please create your farm profile before registering a cow.", "error")
        return redirect(url_for("farmer_farm"))

    if request.method == "GET":
        return render_template("farmer_cow_new.html", farm=farm, farmer=farmer)

    required = ["cow_name", "breed", "cow_type", "gender"]
    missing = [field for field in required if not (request.form.get(field) or "").strip()]
    if missing:
        flash("Please fill in the required cow details.", "error")
        return render_template("farmer_cow_new.html", farm=farm, farmer=farmer)

    try:
        image_filename = save_cow_image(request.files.get("cow_image"))
    except ValueError as err:
        flash(str(err), "error")
        return render_template("farmer_cow_new.html", farm=farm, farmer=farmer)

    farm_identity = (farm.get("farm_id") if farm else None)
    local_cow_number = (request.form.get("local_cow_number") or "").strip()
    if local_cow_number:
        conn = get_db_connection(); cursor = conn.cursor(dictionary=True)
        try:
            cursor.execute(
                "SELECT id FROM cows WHERE farm_id = %s AND local_cow_number = %s LIMIT 1",
                (farm_identity, local_cow_number),
            )
            if cursor.fetchone():
                flash("This cow number is already used on this farm. Please enter another number.", "error")
                return render_template("farmer_cow_new.html", farm=farm, farmer=farmer)
        finally:
            cursor.close(); conn.close()

    cow_id = generate_cow_uid()
    form = request.form
    conn = get_db_connection(); cursor = conn.cursor()
    try:
        cursor.execute(
            """
            INSERT INTO cows (
                cow_id,
                cow_name,
                breed,
                cow_type,
                gender,
                age,
                date_of_birth,
                color,
                registered_location,
                owner_name,
                owner_contact,
                local_cow_number,
                farm_identity,
                qr_code_value,
                health_status,
                health_score,
                vaccination_status,
                last_vaccination_date,
                next_vaccination_date,
                last_health_check,
                disease_history,
                milk_production,
                notes,
                image_path,
                farm_id,
                farmer_id
            ) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
            """,
            (
                cow_id,
                (form.get("cow_name") or "").strip(),
                (form.get("breed") or "").strip(),
                (form.get("cow_type") or "").strip(),
                (form.get("gender") or "").strip(),
                to_int_or_none(form.get("age")),
                (form.get("date_of_birth") or None),
                (form.get("color") or "").strip() or None,
                (farm.get("village") if farm else None) or (farmer.get("village") if farmer else None),
                (farmer.get("full_name") if farmer else None),
                (farmer.get("phone") if farmer else None),
                local_cow_number or None,
                farm_identity,
                f"{SITE_BASE_URL}/cow/{cow_id}",
                "Healthy",
                90,
                "Up to date",
                None,
                None,
                None,
                None,
                to_float_or_none(form.get("milk_production")),
                (form.get("notes") or "").strip() or None,
                image_filename,
                farm_identity,
                farmer_id,
            ),
        )
        conn.commit()
    except DB_ERRORS:
        conn.rollback(); flash("This cow number is already used on this farm. Please enter another number.", "error"); return render_template("farmer_cow_new.html", farm=farm, farmer=farmer)
    finally:
        cursor.close(); conn.close()

    generate_qr_for_cow(cow_id)
    return redirect(url_for("farmer_cow_success", cow_id=cow_id))


@app.route("/farmer/cows/<cow_id>/success")
@require_farmer_login
def farmer_cow_success(cow_id):
    farmer_id = session["farmer_id"]
    conn = get_db_connection(); cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("SELECT * FROM cows WHERE cow_id = %s AND farmer_id = %s LIMIT 1", (cow_id, farmer_id))
        cow = cursor.fetchone()
    finally:
        cursor.close(); conn.close()

    if not cow:
        abort(404)

    return render_template("farmer_cow_success.html", cow=cow)


@app.route("/farmer/cows/<cow_id>")
@require_farmer_login
def farmer_cow_detail(cow_id):
    farmer_id = session["farmer_id"]
    conn = get_db_connection(); cursor = conn.cursor(dictionary=True)
    try:
        # Enforce ownership: only return cow if it belongs to logged-in farmer
        cursor.execute("SELECT * FROM cows WHERE cow_id = %s AND farmer_id = %s LIMIT 1", (cow_id, farmer_id))
        cow = cursor.fetchone()
        if cow:
            cursor.execute("SELECT * FROM cow_medical_history WHERE cow_id = %s ORDER BY created_at DESC", (cow_id,))
            history = cursor.fetchall()
            cursor.execute("SELECT * FROM found_reports WHERE cow_id = %s ORDER BY created_at DESC", (cow_id,))
            found_reports = cursor.fetchall()
        else:
            history = []
            found_reports = []
    finally:
        cursor.close(); conn.close()

    if not cow:
        abort(404)

    return render_template(
        "farmer_cow_detail.html", cow=cow, history=history,
        found_reports=found_reports, screening=get_ai_screening(cow),
    )


@app.route("/farmer/help", methods=["GET", "POST"])
@require_farmer_login
def farmer_help():
    farmer_id = session["farmer_id"]
    conn = get_db_connection(); cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("SELECT * FROM farms WHERE farmer_id = %s LIMIT 1", (farmer_id,))
        farm = cursor.fetchone()
        cursor.execute("SELECT * FROM cows WHERE farmer_id = %s ORDER BY created_at DESC", (farmer_id,))
        cows = cursor.fetchall()
        cursor.execute("SELECT * FROM farmers_assistance_requests WHERE farmer_id = %s ORDER BY created_at DESC", (farmer_id,))
        requests = cursor.fetchall()
    finally:
        cursor.close(); conn.close()

    if request.method == "POST":
        cow_id = request.form.get("cow_id") or None
        request_type = (request.form.get("request_type") or "General help").strip()
        description = (request.form.get("description") or "").strip()
        if cow_id and cow_id not in {c["cow_id"] for c in cows}:
            flash("Please choose one of your own cows.", "error")
            return render_template("farmer_help.html", farm=farm, cows=cows, requests=requests)
        if not description:
            flash("Please describe the veterinary issue before submitting the request.", "error")
            return render_template("farmer_help.html", farm=farm, cows=cows, requests=requests)

        conn = get_db_connection(); cursor = conn.cursor()
        try:
            cursor.execute(
                """
                INSERT INTO farmers_assistance_requests (farmer_id, cow_id, request_type, description, status)
                VALUES (%s,%s,%s,%s,'pending')
                """,
                (farmer_id, cow_id, request_type, description),
            )
            conn.commit()
            flash("Veterinary assistance request submitted successfully.", "success")
        except DB_ERRORS:
            conn.rollback(); flash("Unable to submit the request right now.", "error")
        finally:
            cursor.close(); conn.close()
        return redirect(url_for("farmer_help"))

    vets = []
    if farm:
        conn = get_db_connection(); cursor = conn.cursor(dictionary=True)
        try:
            cursor.execute(
                "SELECT * FROM veterinary_directory WHERE district = %s OR service_area LIKE %s ORDER BY full_name ASC",
                (farm.get("district"), f"%{farm.get('district') or ''}%"),
            )
            vets = cursor.fetchall()
        finally:
            cursor.close(); conn.close()

    return render_template("farmer_help.html", farm=farm, cows=cows, requests=requests, vets=vets)


@app.route("/farmer/assistance/<int:request_id>", methods=["POST"])
@require_farmer_login
def farmer_assistance_status(request_id):
    status = (request.form.get("status") or "pending").strip()
    conn = get_db_connection(); cursor = conn.cursor()
    try:
        cursor.execute("UPDATE farmers_assistance_requests SET status = %s, updated_at = CURRENT_TIMESTAMP WHERE id = %s AND farmer_id = %s", (status, request_id, session["farmer_id"]))
        conn.commit()
    except DB_ERRORS:
        conn.rollback(); flash("Unable to update request status.", "error")
    else:
        flash("Request status updated.", "success")
    finally:
        cursor.close(); conn.close()
    return redirect(url_for("farmer_help"))


@app.route("/farmer/health/<cow_id>")
@require_farmer_login
def farmer_health_report(cow_id):
    farmer_id = session["farmer_id"]
    conn = get_db_connection(); cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("SELECT * FROM cows WHERE cow_id = %s AND farmer_id = %s LIMIT 1", (cow_id, farmer_id))
        cow = cursor.fetchone()
        cursor.execute("SELECT * FROM cow_medical_history WHERE cow_id = %s ORDER BY created_at DESC", (cow_id,))
        history = cursor.fetchall()
    finally:
        cursor.close(); conn.close()

    if not cow:
        abort(404)

    return render_template("farmer_health_report.html", cow=cow, history=history)


ASSISTANCE_STATUSES = frozenset({"pending", "in_progress", "resolved", "rejected"})


def is_demo_cow_id(cow_id):
    """Sample / demonstration records are recognisable by their reserved ids."""
    cow_id = cow_id or ""
    return cow_id in {"COW001", "COW002", "COW003"} or cow_id.startswith("COW-DEMO-")


def collect_doctor_dashboard(search="", include_cows=True):
    """One place that reads everything the doctor dashboard shows (real database rows only)."""
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    try:
        cows = []
        if include_cows and search:
            like = f"%{search}%"
            cursor.execute(
                """
                SELECT *
                FROM cows
                WHERE cow_id LIKE %s
                   OR cow_name LIKE %s
                   OR local_cow_number LIKE %s
                   OR owner_name LIKE %s
                ORDER BY created_at DESC
                """,
                (like, like, like, like)
            )
            cows = cursor.fetchall()
        elif include_cows:
            cursor.execute(
                "SELECT * FROM cows ORDER BY created_at DESC"
            )
            cows = cursor.fetchall()

        cursor.execute(
            "SELECT COUNT(*) AS total FROM cows WHERE next_checkup_date IS NOT NULL AND next_checkup_date <= date('now', '+7 days')"
        )
        follow_up_count = cursor.fetchone()["total"]

        cursor.execute(
            "SELECT COUNT(*) AS total FROM cows WHERE vaccination_status IN ('Pending', 'Overdue') OR next_vaccination_date IS NOT NULL AND next_vaccination_date <= date('now')"
        )
        vaccination_count = cursor.fetchone()["total"]

        cursor.execute(
            "SELECT COUNT(*) AS total FROM farmers_assistance_requests WHERE status = 'pending'"
        )
        request_count = cursor.fetchone()["total"]

        # Changes whenever a request is created, answered or its status is edited.
        cursor.execute(
            "SELECT COUNT(*) AS total, MAX(updated_at) AS latest FROM farmers_assistance_requests"
        )
        request_row = cursor.fetchone()
    finally:
        cursor.close()
        conn.close()

    return {
        "cows": cows,
        "follow_up_count": follow_up_count,
        "vaccination_count": vaccination_count,
        "request_count": request_count,
        "request_version": f"{request_row['total']}:{request_row['latest'] or ''}",
        "demo_count": sum(1 for cow in cows if is_demo_cow_id(cow["cow_id"])),
    }


@app.route("/doctor")
@require_doctor_login
def doctor_dashboard():
    search = normalize_cow_search(request.args.get("q", ""))
    data = collect_doctor_dashboard(search)
    return render_template(
        "doctor_dashboard.html",
        search=search,
        is_demo_cow_id=is_demo_cow_id,
        **data,
    )


@app.route("/doctor/api/dashboard")
def doctor_dashboard_api():
    """JSON feed polled by the dashboard so counts and the cow table stay current."""
    if not session.get("doctor_id"):
        return jsonify({"error": "Sign in as a veterinarian to see live data."}), 401
    search = normalize_cow_search(request.args.get("q", ""))
    summary_only = request.args.get("summary") == "1"
    data = collect_doctor_dashboard(search, include_cows=not summary_only)
    payload = {
        "source": "database",
        "follow_up_count": data["follow_up_count"],
        "vaccination_count": data["vaccination_count"],
        "request_count": data["request_count"],
        "request_version": data["request_version"],
        "demo_count": data["demo_count"],
        "total": len(data["cows"]),
        "cows": [] if summary_only else [
            {
                "cow_id": cow["cow_id"],
                "local_cow_number": cow.get("local_cow_number"),
                "cow_name": cow.get("cow_name"),
                "breed": cow.get("breed"),
                "health_status": cow.get("health_status"),
                "health_score": cow.get("health_score"),
                "next_checkup_date": cow.get("next_checkup_date"),
                "is_demo": is_demo_cow_id(cow["cow_id"]),
            }
            for cow in data["cows"]
        ],
    }
    body = json.dumps(payload, sort_keys=True, default=str)
    etag = '"' + hashlib.sha1(body.encode("utf-8")).hexdigest() + '"'
    if request.headers.get("If-None-Match") == etag:
        response = Response(status=304)
    else:
        response = Response(body, mimetype="application/json")
    response.headers["ETag"] = etag
    response.headers["Cache-Control"] = "no-cache, private"
    return response


@app.route("/doctor/scan", methods=["GET", "POST"])
@require_doctor_login
def doctor_scan():
    cow = None
    error = None
    if request.method == "POST":
        raw = (request.form.get("qr_value") or "").strip()
        lookup = parse_qr_reference(raw)
        if not lookup:
            error = "Please scan or paste the cow QR result, a Cow UID, or a valid QR URL."
        else:
            conn = get_db_connection()
            cursor = conn.cursor(dictionary=True)
            try:
                cursor.execute(
                    """
                    SELECT * FROM cows
                    WHERE cow_id = %s OR local_cow_number = %s OR cow_name = %s
                    LIMIT 1
                    """,
                    (lookup, lookup, lookup)
                )
                cow = cursor.fetchone()
            finally:
                cursor.close()
                conn.close()
            if not cow:
                error = f"No cow found for '{lookup}'."
    return render_template("doctor_scan.html", cow=cow, error=error)


@app.route("/doctor/cow/<cow_id>")
@require_doctor_login
def doctor_cow_profile(cow_id):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("SELECT * FROM cows WHERE cow_id = %s", (cow_id,))
        cow = cursor.fetchone()

        cursor.execute(
            """
            SELECT *
            FROM cow_medical_history
            WHERE cow_id = %s
            ORDER BY created_at DESC
            """,
            (cow_id,)
        )
        history = cursor.fetchall()
    finally:
        cursor.close()
        conn.close()

    if not cow:
        abort(404)

    screening = get_ai_screening(cow)
    return render_template(
        "doctor_cow_profile.html",
        cow=cow,
        history=history,
        screening=screening,
    )


@app.route("/doctor/update/<cow_id>", methods=["GET", "POST"])
@require_doctor_login
def doctor_update(cow_id):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("SELECT * FROM cows WHERE cow_id = %s", (cow_id,))
        cow = cursor.fetchone()
    finally:
        cursor.close()
        conn.close()

    if not cow:
        abort(404)

    if request.method == "GET":
        return render_template("doctor_update.html", cow=cow)

    form = request.form

    doctor_name = (form.get("doctor_name") or "").strip() or session.get("doctor_name") or "Veterinarian"
    health_status = (form.get("health_status") or "").strip() or cow.get("health_status")
    vaccination_status = (form.get("vaccination_status") or "").strip() or cow.get("vaccination_status")
    disease_history = (form.get("disease_history") or "").strip() or cow.get("disease_history")
    medical_record = (form.get("medical_record") or "").strip() or cow.get("medical_record")
    treatment_history = (form.get("treatment_history") or "").strip() or cow.get("treatment_history")
    notes = (form.get("notes") or "").strip() or cow.get("notes")

    def parse_float(value):
        if value in (None, ""):
            return None
        try:
            return float(value)
        except ValueError:
            return None

    def parse_int(value):
        if value in (None, ""):
            return None
        try:
            return int(value)
        except ValueError:
            return None

    health_score = parse_int(form.get("health_score"))
    milk_production = parse_float(form.get("milk_production"))
    body_temperature = parse_float(form.get("body_temperature"))
    weight_kg = parse_float(form.get("weight_kg"))
    next_follow_up = (form.get("next_checkup_date") or "").strip() or None
    last_vaccination = (form.get("last_vaccination_date") or "").strip() or None
    next_vaccination = (form.get("next_vaccination_date") or "").strip() or None
    last_treatment_date = (form.get("last_treatment_date") or "").strip() or None

    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            """
            UPDATE cows
            SET
                doctor_name = %s,
                health_status = %s,
                health_score = %s,
                vaccination_status = %s,
                last_vaccination_date = %s,
                next_vaccination_date = %s,
                last_health_check = %s,
                disease_history = %s,
                milk_production = %s,
                notes = %s,
                medical_record = %s,
                treatment_history = %s,
                last_treatment_date = %s,
                next_checkup_date = %s,
                body_temperature = %s,
                weight_kg = %s,
                pregnancy_status = %s
            WHERE cow_id = %s
            """,
            (
                doctor_name,
                health_status,
                health_score,
                vaccination_status,
                last_vaccination,
                next_vaccination,
                form.get("last_health_check") or None,
                disease_history,
                milk_production,
                notes,
                medical_record,
                treatment_history,
                last_treatment_date,
                next_follow_up,
                body_temperature,
                weight_kg,
                form.get("pregnancy_status") or None,
                cow_id,
            ),
        )

        cursor.execute(
            """
            INSERT INTO cow_medical_history
            (
                cow_id,
                doctor_id,
                doctor_name,
                record_type,
                title,
                summary,
                diagnosis,
                treatment,
                medications,
                vitals,
                temperature_c,
                weight_kg,
                health_status,
                next_follow_up,
                created_at
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, datetime('now'))
            """,
            (
                cow_id,
                session.get("doctor_id"),
                doctor_name,
                "medical_update",
                "Veterinary medical update",
                medical_record or disease_history or treatment_history or "Updated cow health record.",
                form.get("diagnosis") or "Routine evaluation",
                treatment_history or "No active treatment recorded",
                form.get("medications") or "",
                (
                    f"Temp: {body_temperature}C | Weight: {weight_kg}kg | "
                    f"Health: {health_status} | Vaccination: {vaccination_status}"
                ) if body_temperature or weight_kg or health_status or vaccination_status else "Routine observation",
                body_temperature,
                weight_kg,
                health_status,
                next_follow_up,
            ),
        )
        conn.commit()
    except DB_ERRORS:
        conn.rollback()
        flash("The medical record could not be saved. Please try again.", "error")
        return render_template("doctor_update.html", cow=cow, form=form)
    finally:
        cursor.close()
        conn.close()

    flash(f"Medical record updated for {cow['cow_name']} ({cow_id}).", "success")
    return redirect(url_for("doctor_cow_profile", cow_id=cow_id))


@app.route("/doctor/assistance", methods=["GET", "POST"])
@require_doctor_login
def doctor_assistance():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute(
            """
            SELECT r.id, r.cow_id, r.request_type, r.description, r.status,
                   r.doctor_response, r.created_at, r.updated_at,
                   f.full_name AS farmer_name, f.phone AS farmer_contact,
                   c.cow_name
            FROM farmers_assistance_requests r
            JOIN farmers f ON f.id = r.farmer_id
            LEFT JOIN cows c ON c.cow_id = r.cow_id
            ORDER BY r.created_at DESC
            """
        )
        requests = cursor.fetchall()
    finally:
        cursor.close()
        conn.close()

    if request.method == "POST":
        request_id = request.form.get("request_id")
        status = request.form.get("status")
        doctor_response = (request.form.get("doctor_response") or "").strip()
        if not request_id:
            flash("No assistance request was selected.", "error")
            return render_template("doctor_assistance.html", requests=requests)
        if status not in ASSISTANCE_STATUSES:
            flash("Please choose a valid status.", "error")
            return redirect(url_for("doctor_assistance"))

        conn = get_db_connection()
        cursor = conn.cursor()
        try:
            cursor.execute(
                """
                UPDATE farmers_assistance_requests
                SET status = %s,
                    doctor_response = COALESCE(%s, doctor_response),
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = %s
                """,
                (status, doctor_response or None, request_id),
            )
            conn.commit()
        except DB_ERRORS:
            conn.rollback()
            flash("The assistance request could not be updated.", "error")
        else:
            flash("Assistance request status updated successfully.", "success")
        finally:
            cursor.close()
            conn.close()
        return redirect(url_for("doctor_assistance"))

    return render_template(
        "doctor_assistance.html",
        requests=requests,
        request_version=collect_doctor_dashboard("", include_cows=False)["request_version"],
    )


@app.route("/doctor/requests/<int:request_id>/contact", methods=["POST"])
@require_doctor_login
def doctor_contact_farmer(request_id):
    doctor_response = (request.form.get("doctor_response") or "").strip()
    if not doctor_response:
        flash("Please add a message before contacting the farmer.", "error")
        return redirect(url_for("doctor_assistance"))

    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            """
            UPDATE farmers_assistance_requests
            SET doctor_response = %s,
                status = 'in_progress',
                updated_at = CURRENT_TIMESTAMP
            WHERE id = %s
            """,
            (doctor_response, request_id),
        )
        conn.commit()
    except DB_ERRORS:
        conn.rollback()
        flash("Unable to contact the farmer at this time.", "error")
    else:
        flash("Farmer contact note saved and the case is now in progress.", "success")
    finally:
        cursor.close()
        conn.close()

    return redirect(url_for("doctor_assistance"))


# ------------------------------------------------------------------
# Dashboard
# ------------------------------------------------------------------

@app.route("/dashboard")
def dashboard():

    search = request.args.get(
        "q",
        ""
    ).strip()

    # Admin/doctor dashboard - limit visibility to doctors/admins only
    if not session.get('doctor_id'):
        # For farmers, redirect to their personalized farmer dashboard
        if session.get('farmer_id'):
            return redirect(url_for('farmer_dashboard'))
        # Public users should not see global cow list
        flash('Please log in to access the dashboard.', 'error')
        return redirect(url_for('index'))

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        if search:
            like = f"%{search}%"
            cursor.execute(
                """
                SELECT *
                FROM cows
                WHERE cow_id LIKE %s
                   OR cow_name LIKE %s
                ORDER BY created_at DESC
                """,
                (like, like),
            )
        else:
            cursor.execute(
                "SELECT * FROM cows ORDER BY created_at DESC"
            )
        cows = cursor.fetchall()
        cursor.execute("SELECT COUNT(*) AS total FROM cows")
        total = cursor.fetchone()["total"]
    finally:
        cursor.close(); conn.close()

    return render_template("dashboard.html", cows=cows, total=total, search=search)


# ------------------------------------------------------------------
# Delete Cow
# ------------------------------------------------------------------

@app.route(
    "/delete/<cow_id>",
    methods=["POST"]
)
@require_doctor_login
def delete_cow(cow_id):

    conn = get_db_connection()

    cursor = conn.cursor(
        dictionary=True
    )

    row = None

    try:

        cursor.execute(
            """
            SELECT image_path
            FROM cows
            WHERE cow_id = %s
            """,
            (cow_id,)
        )

        row = cursor.fetchone()

        cursor.execute(
            """
            DELETE FROM cows
            WHERE cow_id = %s
            """,
            (cow_id,)
        )

        conn.commit()

    finally:

        cursor.close()
        conn.close()

    # --------------------------------------------------------------
    # Delete stored image
    # --------------------------------------------------------------

    if row and row.get(
        "image_path"
    ):

        img_path = os.path.join(
            app.config["UPLOAD_FOLDER"],
            row["image_path"]
        )

        if os.path.exists(
            img_path
        ):

            os.remove(
                img_path
            )

    # --------------------------------------------------------------
    # Delete QR image
    # --------------------------------------------------------------

    qr_path = os.path.join(
        QR_FOLDER,
        f"{cow_id}.png"
    )

    if os.path.exists(
        qr_path
    ):

        os.remove(
            qr_path
        )

    flash(
        f"Cow {cow_id} was removed from the registry.",
        "success"
    )

    return redirect(
        url_for("dashboard")
    )


# ==================================================================
# REGISTER COW
# ==================================================================

@app.route(
    "/register",
    methods=["GET", "POST"]
)
@require_farmer_or_doctor_login
def register_cow():

    # --------------------------------------------------------------
    # Display form
    # --------------------------------------------------------------

    if request.method == "GET":

        return render_template(
            "register_cow.html"
        )

    form = request.form

    # --------------------------------------------------------------
    # Required fields
    # --------------------------------------------------------------

    required_fields = [
        "cow_id",
        "cow_name",
        "breed",
        "cow_type",
        "gender",
        "owner_name",
        "owner_contact",
    ]

    missing = [
        field
        for field in required_fields
        if not form.get(
            field,
            ""
        ).strip()
    ]

    if missing:

        flash(
            "Please fill in required field(s): "
            + ", ".join(missing),
            "error"
        )

        return render_template(
            "register_cow.html",
            form=form
        )

    # --------------------------------------------------------------
    # Get Cow ID
    # --------------------------------------------------------------

    cow_id = form.get(
        "cow_id",
        ""
    ).strip()

    cow_name = form.get(
        "cow_name",
        ""
    ).strip()

    if not is_safe_cow_id(cow_id):
        flash(
            "Cow ID may contain only letters, numbers, dots, dashes and underscores (maximum 64 characters).",
            "error"
        )
        return render_template(
            "register_cow.html",
            form=form
        )

    # --------------------------------------------------------------
    # Save image
    # --------------------------------------------------------------

    try:

        image_filename = save_cow_image(
            request.files.get(
                "cow_image"
            )
        )

    except ValueError as error:

        flash(
            str(error),
            "error"
        )

        return render_template(
            "register_cow.html",
            form=form
        )

    # --------------------------------------------------------------
    # Convert blank values to None
    # --------------------------------------------------------------

    def none_if_blank(value):

        if value in (
            None,
            ""
        ):
            return None

        return value

    # --------------------------------------------------------------
    # Prepare data
    # --------------------------------------------------------------

    data = (

        cow_id,

        cow_name,

        form.get(
            "breed",
            ""
        ).strip(),

        form.get(
            "cow_type",
            ""
        ).strip(),

        form.get(
            "gender",
            ""
        ).strip(),

        to_int_or_none(
            form.get("age")
        ),

        none_if_blank(
            form.get("date_of_birth")
        ),

        none_if_blank(
            form.get("color")
        ),

        none_if_blank(
            form.get("registered_location")
        ),

        form.get(
            "owner_name",
            ""
        ).strip(),

        form.get(
            "owner_contact",
            ""
        ).strip(),

        none_if_blank(
            form.get("health_status")
        ),

        to_int_or_none(
            form.get("health_score")
        ),

        none_if_blank(
            form.get("vaccination_status")
        ),

        none_if_blank(
            form.get("last_vaccination_date")
        ),

        none_if_blank(
            form.get("last_health_check")
        ),

        none_if_blank(
            form.get("disease_history")
        ),

        to_float_or_none(
            form.get("milk_production")
        ),

        none_if_blank(
            form.get("notes")
        ),

        image_filename,
    )

    # --------------------------------------------------------------
    # Connect to database
    # --------------------------------------------------------------

    conn = get_db_connection()

    cursor = conn.cursor()

    try:

        # ----------------------------------------------------------
        # Check duplicate Cow ID BEFORE INSERT
        # ----------------------------------------------------------

        cursor.execute(
            """
            SELECT cow_id
            FROM cows
            WHERE cow_id = %s
            """,
            (cow_id,)
        )

        existing_cow = cursor.fetchone()

        if existing_cow:

            flash(
                f"Cow ID '{cow_id}' is already registered. "
                "Please choose a different Cow ID.",
                "error"
            )

            return render_template(
                "register_cow.html",
                form=form
            )

        # ----------------------------------------------------------
        # Insert Cow
        # ----------------------------------------------------------

        cursor.execute(
            """
            INSERT INTO cows
            (
                cow_id,
                cow_name,
                breed,
                cow_type,
                gender,
                age,
                date_of_birth,
                color,
                registered_location,
                owner_name,
                owner_contact,
                health_status,
                health_score,
                vaccination_status,
                last_vaccination_date,
                last_health_check,
                disease_history,
                milk_production,
                notes,
                image_path
            )
            VALUES
            (
                %s,
                %s,
                %s,
                %s,
                %s,
                %s,
                %s,
                %s,
                %s,
                %s,
                %s,
                %s,
                %s,
                %s,
                %s,
                %s,
                %s,
                %s,
                %s,
                %s
            )
            """,
            data
        )

        # A logged-in farmer who uses this public form owns the cow, so it shows up in their herd.
        # Anonymous registrations keep working exactly as before (no owner account).
        if session.get("farmer_id"):
            cursor.execute(
                "SELECT farm_id FROM farms WHERE farmer_id = %s ORDER BY id LIMIT 1",
                (session["farmer_id"],)
            )
            farm_row = cursor.fetchone()
            cursor.execute(
                "UPDATE cows SET farmer_id = %s, farm_id = %s WHERE cow_id = %s",
                (session["farmer_id"], row_value(farm_row, "farm_id") if farm_row else None, cow_id)
            )

        # ----------------------------------------------------------
        # Save database changes
        # ----------------------------------------------------------

        conn.commit()

    except DB_ERRORS as error:

        conn.rollback()

        # ----------------------------------------------------------
        # Duplicate Cow ID
        # ----------------------------------------------------------

        if (
            isinstance(
                error,
                sqlite3.IntegrityError
            )
            or
            getattr(
                error,
                "errno",
                None
            ) == 1062
            or
            getattr(
                error,
                "pgcode",
                None
            ) == "23505"
        ):

            flash(
                f"Cow ID '{cow_id}' is already registered. "
                "Please choose a different Cow ID.",
                "error"
            )

        else:

            app.logger.exception(
                "Error while registering cow"
            )

            flash(
                "Could not save the cow. "
                "Please check the database and try again.",
                "error"
            )

        return render_template(
            "register_cow.html",
            form=form
        )

    finally:

        cursor.close()

        conn.close()

    # --------------------------------------------------------------
    # Generate QR AFTER successful registration
    # --------------------------------------------------------------

    generate_qr_for_cow(
        cow_id
    )

    # --------------------------------------------------------------
    # Success message
    # --------------------------------------------------------------

    flash(
        f"{cow_name} ({cow_id}) was registered successfully.",
        "success"
    )

    # --------------------------------------------------------------
    # Show QR page
    # --------------------------------------------------------------

    return redirect(
        url_for(
            "show_qr",
            cow_id=cow_id
        )
    )


# ==================================================================
# QR CODE
# ==================================================================

@app.route(
    "/qr/<cow_id>"
)
def show_qr(cow_id):

    conn = get_db_connection()

    cursor = conn.cursor(
        dictionary=True
    )

    try:

        # Public QR page: only expose minimal public fields
        cursor.execute(
            "SELECT cow_id, cow_name FROM cows WHERE cow_id = %s",
            (cow_id,)
        )
        cow = cursor.fetchone()

    finally:

        cursor.close()
        conn.close()

    if not cow:

        abort(404)

    qr_filename = generate_qr_for_cow(cow_id)

    profile_url = (
        f"{SITE_BASE_URL}/cow/{cow_id}"
    )

    return render_template(
        "qr.html",
        cow=cow,
        qr_filename=qr_filename,
        profile_url=profile_url
    )


# ==================================================================
# QR SCANNER
# ==================================================================

@app.route("/scan")
def scan():

    return render_template(
        "scan.html"
    )


# ==================================================================
# COW DIGITAL PASSPORT
# ==================================================================

@app.route(
    "/cow/<cow_id>"
)
def cow_profile(cow_id):

    conn = get_db_connection()

    cursor = conn.cursor(
        dictionary=True
    )

    try:

        # Only expose full cow profile if the request comes from the owning farmer or an authenticated doctor
        if session.get('farmer_id'):
            farmer_id = session.get('farmer_id')
            cursor.execute("SELECT * FROM cows WHERE cow_id = %s AND farmer_id = %s LIMIT 1", (cow_id, farmer_id))
            cow = cursor.fetchone()
            if not cow:
                cursor.execute("SELECT cow_id, cow_name, breed, gender, image_path FROM cows WHERE cow_id = %s", (cow_id,))
                cow = cursor.fetchone()
        elif session.get('doctor_id'):
            cursor.execute("SELECT * FROM cows WHERE cow_id = %s", (cow_id,))
            cow = cursor.fetchone()
        else:
            # public view - only minimal public fields
            cursor.execute("SELECT cow_id, cow_name, breed, gender, image_path FROM cows WHERE cow_id = %s", (cow_id,))
            cow = cursor.fetchone()

    finally:

        cursor.close()
        conn.close()

    if not cow:

        abort(404)

    return render_template(
        "cow_profile.html",
        cow=cow
    )


# ==================================================================
# REPORT FOUND COW
# ==================================================================

@app.route(
    "/report_found/<cow_id>",
    methods=["GET", "POST"]
)
def report_found(cow_id):

    # --------------------------------------------------------------
    # Find cow
    # --------------------------------------------------------------

    conn = get_db_connection()

    cursor = conn.cursor(
        dictionary=True
    )

    try:

        cursor.execute(
            """
            SELECT
                cow_id,
                cow_name,
                registered_location
            FROM cows
            WHERE cow_id = %s
            """,
            (cow_id,)
        )

        cow = cursor.fetchone()

    finally:

        cursor.close()
        conn.close()

    if not cow:

        abort(404)

    # --------------------------------------------------------------
    # Display report form
    # --------------------------------------------------------------

    if request.method == "GET":

        return render_template(
            "report_found.html",
            cow=cow
        )

    # --------------------------------------------------------------
    # Process report
    # --------------------------------------------------------------

    form = request.form

    required_fields = [
        "finder_name",
        "finder_contact"
    ]

    missing = [
        field
        for field in required_fields
        if not form.get(
            field,
            ""
        ).strip()
    ]

    if missing:

        flash(
            "Please fill in required field(s): "
            + ", ".join(missing),
            "error"
        )

        return render_template(
            "report_found.html",
            cow=cow,
            form=form
        )

    # --------------------------------------------------------------
    # Save found report
    # --------------------------------------------------------------

    conn = get_db_connection()

    cursor = conn.cursor()

    try:

        cursor.execute(
            """
            INSERT INTO found_reports
            (
                cow_id,
                finder_name,
                finder_contact,
                current_area,
                message
            )
            VALUES
            (
                %s,
                %s,
                %s,
                %s,
                %s
            )
            """,
            (
                cow_id,

                form.get(
                    "finder_name",
                    ""
                ).strip(),

                form.get(
                    "finder_contact",
                    ""
                ).strip(),

                form.get(
                    "current_area",
                    ""
                ).strip() or None,

                form.get(
                    "message",
                    ""
                ).strip() or None,
            )
        )

        conn.commit()

    except DB_ERRORS:

        conn.rollback()

        flash(
            "Could not submit the found-cow report. "
            "Please try again.",
            "error"
        )

        return render_template(
            "report_found.html",
            cow=cow,
            form=form
        )

    finally:

        cursor.close()
        conn.close()

    flash(
        "The owner has been notified about the found cow.",
        "success"
    )

    return redirect(
        url_for(
            "cow_profile",
            cow_id=cow_id
        )
    )


# ==================================================================
# ERROR HANDLER
# ==================================================================

@app.errorhandler(404)
def not_found(_error):

    return render_template(
        "404.html"
    ), 404


# ==================================================================
# START APPLICATION
# ==================================================================

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "asgi:application",
        host="0.0.0.0",
        port=PORT,
        reload=False,
    )