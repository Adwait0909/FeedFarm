-- Farm2Feed schema for MYSQL (generated from the SQLite schema in app.py).
-- Safe to run repeatedly: every statement is idempotent. Dates stay TEXT, exactly as in SQLite.

CREATE TABLE IF NOT EXISTS farmers (
    id INT AUTO_INCREMENT PRIMARY KEY,
    full_name TEXT NOT NULL,
    email VARCHAR(255) NOT NULL UNIQUE,
    phone TEXT,
    password_hash TEXT NOT NULL,
    village TEXT,
    taluka TEXT,
    district TEXT,
    state TEXT,
    created_at VARCHAR(32) DEFAULT (CAST(NOW() AS CHAR))
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS doctors (
    id INT AUTO_INCREMENT PRIMARY KEY,
    full_name TEXT NOT NULL,
    email VARCHAR(255) NOT NULL UNIQUE,
    password_hash TEXT NOT NULL,
    specialization TEXT,
    created_at VARCHAR(32) DEFAULT (CAST(NOW() AS CHAR))
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS cows (
    id INT AUTO_INCREMENT PRIMARY KEY,
    cow_id VARCHAR(255) NOT NULL UNIQUE,
    cow_name TEXT NOT NULL,
    breed TEXT,
    cow_type TEXT,
    gender TEXT,
    age INT,
    date_of_birth TEXT,
    color TEXT,
    registered_location TEXT,
    owner_name TEXT,
    owner_contact TEXT,
    local_cow_number VARCHAR(255),
    farm_identity TEXT,
    qr_code_value TEXT,
    health_status TEXT,
    health_score INT,
    vaccination_status TEXT,
    last_vaccination_date TEXT,
    next_vaccination_date TEXT,
    last_health_check TEXT,
    disease_history TEXT,
    milk_production DOUBLE,
    notes TEXT,
    doctor_name TEXT,
    medical_record TEXT,
    treatment_history TEXT,
    last_treatment_date TEXT,
    next_checkup_date TEXT,
    body_temperature DOUBLE,
    weight_kg DOUBLE,
    pregnancy_status TEXT,
    image_path TEXT,
    created_at VARCHAR(32) DEFAULT (CAST(NOW() AS CHAR)),
    farm_id VARCHAR(255),
    farmer_id INT
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS farms (
    id INT AUTO_INCREMENT PRIMARY KEY,
    farmer_id INT NOT NULL,
    farm_id VARCHAR(255) NOT NULL UNIQUE,
    farm_name TEXT NOT NULL,
    village TEXT,
    taluka TEXT,
    district TEXT,
    state TEXT,
    service_area TEXT,
    created_at VARCHAR(32) DEFAULT (CAST(NOW() AS CHAR)),
    FOREIGN KEY (farmer_id) REFERENCES farmers(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS veterinary_directory (
    id INT AUTO_INCREMENT PRIMARY KEY,
    full_name TEXT NOT NULL,
    clinic_name TEXT,
    specialization TEXT,
    district TEXT,
    city TEXT,
    phone TEXT,
    email VARCHAR(255),
    service_area TEXT,
    location_note TEXT,
    created_at VARCHAR(32) DEFAULT (CAST(NOW() AS CHAR))
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS farmers_assistance_requests (
    id INT AUTO_INCREMENT PRIMARY KEY,
    farmer_id INT NOT NULL,
    cow_id VARCHAR(255),
    request_type TEXT,
    description TEXT,
    status VARCHAR(50) DEFAULT 'pending',
    veterinarian_name TEXT,
    veterinarian_contact TEXT,
    doctor_response TEXT,
    created_at VARCHAR(32) DEFAULT (CAST(NOW() AS CHAR)),
    updated_at VARCHAR(32) DEFAULT (CAST(NOW() AS CHAR)),
    FOREIGN KEY (farmer_id) REFERENCES farmers(id) ON DELETE CASCADE,
    FOREIGN KEY (cow_id) REFERENCES cows(cow_id) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS cow_medical_history (
    id INT AUTO_INCREMENT PRIMARY KEY,
    cow_id VARCHAR(255) NOT NULL,
    doctor_id INT,
    doctor_name TEXT,
    record_type TEXT,
    title TEXT,
    summary TEXT,
    diagnosis TEXT,
    treatment TEXT,
    medications TEXT,
    vitals TEXT,
    temperature_c DOUBLE,
    weight_kg DOUBLE,
    health_status TEXT,
    next_follow_up TEXT,
    created_at VARCHAR(32) DEFAULT (CAST(NOW() AS CHAR)),
    FOREIGN KEY (cow_id) REFERENCES cows(cow_id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS veterinary_assistance_requests (
    id INT AUTO_INCREMENT PRIMARY KEY,
    cow_id VARCHAR(255) NOT NULL,
    farmer_name TEXT,
    farmer_contact TEXT,
    request_type TEXT,
    description TEXT,
    status VARCHAR(50) DEFAULT 'pending',
    doctor_response TEXT,
    created_at VARCHAR(32) DEFAULT (CAST(NOW() AS CHAR)),
    updated_at VARCHAR(32) DEFAULT (CAST(NOW() AS CHAR)),
    FOREIGN KEY (cow_id) REFERENCES cows(cow_id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS found_reports (
    id INT AUTO_INCREMENT PRIMARY KEY,
    cow_id VARCHAR(255) NOT NULL,
    finder_name TEXT NOT NULL,
    finder_contact TEXT NOT NULL,
    current_area TEXT,
    message TEXT,
    created_at VARCHAR(32) DEFAULT (CAST(NOW() AS CHAR)),
    FOREIGN KEY (cow_id)
    REFERENCES cows(cow_id)
    ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE UNIQUE INDEX idx_cows_farm_local_number ON cows (farm_id, local_cow_number);
CREATE INDEX idx_medical_history_doctor_cow ON cow_medical_history (doctor_id, cow_id);
