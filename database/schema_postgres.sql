-- Farm2Feed schema for POSTGRES (generated from the SQLite schema in app.py).
-- Safe to run repeatedly: every statement is idempotent. Dates stay TEXT, exactly as in SQLite.

CREATE TABLE IF NOT EXISTS farmers (
    id SERIAL PRIMARY KEY,
    full_name TEXT NOT NULL,
    email TEXT NOT NULL UNIQUE,
    phone TEXT,
    password_hash TEXT NOT NULL,
    village TEXT,
    taluka TEXT,
    district TEXT,
    state TEXT,
    created_at TEXT DEFAULT (to_char(CURRENT_TIMESTAMP, 'YYYY-MM-DD HH24:MI:SS'))
);

CREATE TABLE IF NOT EXISTS doctors (
    id SERIAL PRIMARY KEY,
    full_name TEXT NOT NULL,
    email TEXT NOT NULL UNIQUE,
    password_hash TEXT NOT NULL,
    specialization TEXT,
    created_at TEXT DEFAULT (to_char(CURRENT_TIMESTAMP, 'YYYY-MM-DD HH24:MI:SS'))
);

CREATE TABLE IF NOT EXISTS cows (
    id SERIAL PRIMARY KEY,
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
    milk_production DOUBLE PRECISION,
    notes TEXT,
    doctor_name TEXT,
    medical_record TEXT,
    treatment_history TEXT,
    last_treatment_date TEXT,
    next_checkup_date TEXT,
    body_temperature DOUBLE PRECISION,
    weight_kg DOUBLE PRECISION,
    pregnancy_status TEXT,
    image_path TEXT,
    created_at TEXT DEFAULT (to_char(CURRENT_TIMESTAMP, 'YYYY-MM-DD HH24:MI:SS')),
    farm_id TEXT,
    farmer_id INTEGER
);

CREATE TABLE IF NOT EXISTS farms (
    id SERIAL PRIMARY KEY,
    farmer_id INTEGER NOT NULL,
    farm_id TEXT NOT NULL UNIQUE,
    farm_name TEXT NOT NULL,
    village TEXT,
    taluka TEXT,
    district TEXT,
    state TEXT,
    service_area TEXT,
    created_at TEXT DEFAULT (to_char(CURRENT_TIMESTAMP, 'YYYY-MM-DD HH24:MI:SS')),
    FOREIGN KEY (farmer_id) REFERENCES farmers(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS veterinary_directory (
    id SERIAL PRIMARY KEY,
    full_name TEXT NOT NULL,
    clinic_name TEXT,
    specialization TEXT,
    district TEXT,
    city TEXT,
    phone TEXT,
    email TEXT,
    service_area TEXT,
    location_note TEXT,
    created_at TEXT DEFAULT (to_char(CURRENT_TIMESTAMP, 'YYYY-MM-DD HH24:MI:SS'))
);

CREATE TABLE IF NOT EXISTS farmers_assistance_requests (
    id SERIAL PRIMARY KEY,
    farmer_id INTEGER NOT NULL,
    cow_id TEXT,
    request_type TEXT,
    description TEXT,
    status TEXT DEFAULT 'pending',
    veterinarian_name TEXT,
    veterinarian_contact TEXT,
    doctor_response TEXT,
    created_at TEXT DEFAULT (to_char(CURRENT_TIMESTAMP, 'YYYY-MM-DD HH24:MI:SS')),
    updated_at TEXT DEFAULT (to_char(CURRENT_TIMESTAMP, 'YYYY-MM-DD HH24:MI:SS')),
    FOREIGN KEY (farmer_id) REFERENCES farmers(id) ON DELETE CASCADE,
    FOREIGN KEY (cow_id) REFERENCES cows(cow_id) ON DELETE SET NULL
);

CREATE TABLE IF NOT EXISTS cow_medical_history (
    id SERIAL PRIMARY KEY,
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
    temperature_c DOUBLE PRECISION,
    weight_kg DOUBLE PRECISION,
    health_status TEXT,
    next_follow_up TEXT,
    created_at TEXT DEFAULT (to_char(CURRENT_TIMESTAMP, 'YYYY-MM-DD HH24:MI:SS')),
    FOREIGN KEY (cow_id) REFERENCES cows(cow_id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS veterinary_assistance_requests (
    id SERIAL PRIMARY KEY,
    cow_id TEXT NOT NULL,
    farmer_name TEXT,
    farmer_contact TEXT,
    request_type TEXT,
    description TEXT,
    status TEXT DEFAULT 'pending',
    doctor_response TEXT,
    created_at TEXT DEFAULT (to_char(CURRENT_TIMESTAMP, 'YYYY-MM-DD HH24:MI:SS')),
    updated_at TEXT DEFAULT (to_char(CURRENT_TIMESTAMP, 'YYYY-MM-DD HH24:MI:SS')),
    FOREIGN KEY (cow_id) REFERENCES cows(cow_id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS found_reports (
    id SERIAL PRIMARY KEY,
    cow_id TEXT NOT NULL,
    finder_name TEXT NOT NULL,
    finder_contact TEXT NOT NULL,
    current_area TEXT,
    message TEXT,
    created_at TEXT DEFAULT (to_char(CURRENT_TIMESTAMP, 'YYYY-MM-DD HH24:MI:SS')),
    FOREIGN KEY (cow_id)
    REFERENCES cows(cow_id)
    ON DELETE CASCADE
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_cows_farm_local_number ON cows (farm_id, local_cow_number);
CREATE INDEX IF NOT EXISTS idx_medical_history_doctor_cow ON cow_medical_history (doctor_id, cow_id);
