-- Migration 001: Create veterinary_facilities table
-- Run this once against your PostgreSQL database.
-- The FastAPI app will also auto-create this via SQLAlchemy on startup.

CREATE TABLE IF NOT EXISTS veterinary_facilities (
    id            SERIAL PRIMARY KEY,
    name          VARCHAR(500)  NOT NULL,
    facility_type VARCHAR(100)  NOT NULL,
    district      VARCHAR(200),
    taluka        VARCHAR(200),
    address       VARCHAR(1000),
    latitude      DOUBLE PRECISION NOT NULL,
    longitude     DOUBLE PRECISION NOT NULL,
    department    VARCHAR(300),
    created_at    TIMESTAMPTZ DEFAULT NOW(),
    updated_at    TIMESTAMPTZ,

    -- Unique constraint to prevent duplicates on re-import
    CONSTRAINT uq_facility_name_coords UNIQUE (name, latitude, longitude)
);

-- Indexes for fast search
CREATE INDEX IF NOT EXISTS idx_vet_district      ON veterinary_facilities (district);
CREATE INDEX IF NOT EXISTS idx_vet_taluka        ON veterinary_facilities (taluka);
CREATE INDEX IF NOT EXISTS idx_vet_type          ON veterinary_facilities (facility_type);
CREATE INDEX IF NOT EXISTS idx_vet_lat           ON veterinary_facilities (latitude);
CREATE INDEX IF NOT EXISTS idx_vet_lon           ON veterinary_facilities (longitude);
-- Composite index for bounding-box queries
CREATE INDEX IF NOT EXISTS idx_vet_latlon        ON veterinary_facilities (latitude, longitude);
