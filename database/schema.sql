-- ============================================================
-- QR-Based Cow Digital Passport
-- Database schema + sample data
-- ============================================================

CREATE DATABASE IF NOT EXISTS cow_qr_demo;
USE cow_qr_demo;

-- ------------------------------------------------------------
-- Table: cows
-- Stores every registered cow's profile information
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS cows (
    id INT AUTO_INCREMENT PRIMARY KEY,
    cow_id VARCHAR(20) NOT NULL UNIQUE,
    cow_name VARCHAR(100) NOT NULL,
    breed VARCHAR(100),
    cow_type VARCHAR(50),
    gender VARCHAR(10),
    age INT,
    date_of_birth DATE,
    color VARCHAR(50),
    registered_location VARCHAR(150),
    owner_name VARCHAR(100),
    owner_contact VARCHAR(20),
    health_status VARCHAR(50),
    health_score INT,
    vaccination_status VARCHAR(50),
    last_vaccination_date DATE,
    last_health_check DATE,
    disease_history TEXT,
    milk_production DECIMAL(5,2),
    notes TEXT,
    image_path VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ------------------------------------------------------------
-- Table: found_reports
-- Stores "Found This Cow" submissions from the public
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS found_reports (
    id INT AUTO_INCREMENT PRIMARY KEY,
    cow_id VARCHAR(20) NOT NULL,
    finder_name VARCHAR(100) NOT NULL,
    finder_contact VARCHAR(20) NOT NULL,
    current_area VARCHAR(150),
    message TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_found_cow FOREIGN KEY (cow_id) REFERENCES cows(cow_id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ------------------------------------------------------------
-- Sample data so the demo works immediately
-- ------------------------------------------------------------
INSERT INTO cows
(cow_id, cow_name, breed, cow_type, gender, age, date_of_birth, color, registered_location,
 owner_name, owner_contact, health_status, health_score, vaccination_status,
 last_vaccination_date, last_health_check, disease_history, milk_production, notes, image_path)
VALUES
('COW001', 'Ganga', 'Gir', 'Dairy', 'Female', 4, '2022-03-14', 'Reddish Brown',
 'Shivapur Dairy Farm, Pune', 'Ramesh Patil', '9876543210', 'Healthy', 92, 'Up to date',
 '2026-05-10', '2026-08-20', 'None reported', 12.50,
 'Calm temperament, good milk yield through the year.', NULL),

('COW002', 'Lakshmi', 'Sahiwal', 'Dairy', 'Female', 5, '2021-07-02', 'Light Brown',
 'Shivapur Dairy Farm, Pune', 'Ramesh Patil', '9876543210', 'Healthy', 88, 'Up to date',
 '2026-04-22', '2026-08-15', 'Minor mastitis (treated, 2024)', 10.80,
 'Requires slightly warmer shelter in winter.', NULL),

('COW003', 'Radha', 'Red Sindhi', 'Dairy', 'Female', 3, '2023-01-19', 'Deep Red',
 'Shivapur Dairy Farm, Pune', 'Sunita Patil', '9876501234', 'Under Observation', 75, 'Pending',
 '2025-11-05', '2026-08-25', 'Recovering from foot infection', 8.20,
 'Vaccination booster due next month.', NULL);
