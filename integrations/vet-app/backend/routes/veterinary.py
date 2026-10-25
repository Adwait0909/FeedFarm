"""
Veterinary facility API routes.

Endpoints:
  POST /api/veterinary/import          — Import KML data into DB
  GET  /api/veterinary/nearby          — Nearest facilities by coordinates
  GET  /api/veterinary/search/district — Search by district/taluka
  GET  /api/veterinary/districts       — All unique districts
  GET  /api/veterinary/talukas         — Talukas for a district
  GET  /api/veterinary/{id}            — Single facility detail
  GET  /api/veterinary/stats           — Facility count stats
"""

import logging
import os
import secrets

from fastapi import APIRouter, Depends, Header, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional

from ..database import get_db
from ..models.schemas import (
    FacilityOut, NearbyResponse, DistrictResponse,
    ImportResponse, StatsResponse,
)
from ..services import veterinary_service as svc

router = APIRouter(prefix="/api/veterinary", tags=["Veterinary"])
logger = logging.getLogger(__name__)


# ── Import KML ────────────────────────────────────────────────────────────────

@router.post("/import", response_model=ImportResponse, status_code=status.HTTP_200_OK)
async def import_kml(
    x_admin_token: Optional[str] = Header(default=None),
    db: AsyncSession = Depends(get_db),
):
    """
    Parse the KML files and load facilities into the database.
    Safe to run multiple times — duplicates are skipped automatically.
    """
    expected = os.environ.get("VET_IMPORT_TOKEN", "")
    if not expected or not x_admin_token or not secrets.compare_digest(x_admin_token, expected):
        raise HTTPException(
            status_code=403,
            detail="Import is disabled or the X-Admin-Token header is missing or invalid.",
        )
    try:
        result = await svc.import_kml_to_db(db)
        return ImportResponse(
            success=True,
            message=f"Import complete. {result['inserted']} new records added.",
            **result,
        )
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=f"KML file not found: {e}")
    except Exception as e:
        logger.exception("KML import failed")
        raise HTTPException(status_code=500, detail="Import failed. See the server log.")


# ── Nearby Search ─────────────────────────────────────────────────────────────

@router.get("/nearby", response_model=NearbyResponse)
async def nearby_facilities(
    latitude:      float           = Query(..., ge=-90,  le=90,  description="User latitude"),
    longitude:     float           = Query(..., ge=-180, le=180, description="User longitude"),
    radius:        float           = Query(25.0, ge=1,   le=200, description="Search radius in km"),
    limit:         int             = Query(10,   ge=1,   le=100, description="Max results"),
    facility_type: Optional[str]   = Query(None, description="Filter: 'Veterinary Dispensary' or 'District/Taluka'"),
    db:            AsyncSession    = Depends(get_db),
):
    """
    Return veterinary facilities sorted by distance from the given coordinates.
    Default radius: 25 km | Default limit: 10
    """
    # Loose Maharashtra bounds check — let frontend handle user-friendly msg
    if not (15.0 <= latitude <= 23.0 and 72.0 <= longitude <= 81.0):
        raise HTTPException(
            status_code=422,
            detail="Coordinates appear to be outside Maharashtra. Please verify your location."
        )

    facilities = await svc.get_nearby_facilities(
        db, latitude, longitude, radius, limit, facility_type
    )

    return NearbyResponse(
        count=len(facilities),
        facilities=facilities,
        radius_km=radius,
        latitude=latitude,
        longitude=longitude,
    )


# ── District / Taluka Search ──────────────────────────────────────────────────

@router.get("/search/district", response_model=DistrictResponse)
async def search_by_district(
    district:      str           = Query(..., min_length=2, description="District name"),
    taluka:        Optional[str] = Query(None, description="Taluka name (optional)"),
    facility_type: Optional[str] = Query(None),
    limit:         int           = Query(50, ge=1, le=200),
    db:            AsyncSession  = Depends(get_db),
):
    """Search facilities by district and optional taluka name."""
    facilities = await svc.get_facilities_by_district(
        db, district, taluka, facility_type, limit
    )
    return DistrictResponse(
        count=len(facilities),
        district=district,
        taluka=taluka,
        facilities=facilities,
    )


# ── Lists for Dropdowns ───────────────────────────────────────────────────────

@router.get("/districts", response_model=list[str])
async def list_districts(db: AsyncSession = Depends(get_db)):
    """Return all unique district names (for dropdown)."""
    return await svc.get_all_districts(db)


@router.get("/talukas", response_model=list[str])
async def list_talukas(
    district: str = Query(..., description="District to get talukas for"),
    db: AsyncSession = Depends(get_db),
):
    """Return unique talukas for a given district."""
    return await svc.get_talukas_by_district(db, district)


# ── Stats ─────────────────────────────────────────────────────────────────────

@router.get("/stats", response_model=StatsResponse)
async def facility_stats(db: AsyncSession = Depends(get_db)):
    """Return total count and breakdown by facility type."""
    return await svc.get_facility_stats(db)


# ── Single Facility ───────────────────────────────────────────────────────────

@router.get("/{facility_id}", response_model=FacilityOut)
async def get_facility(
    facility_id: int,
    db: AsyncSession = Depends(get_db),
):
    """Return full details for a single facility by ID."""
    facility = await svc.get_facility_by_id(db, facility_id)
    if not facility:
        raise HTTPException(status_code=404, detail="Facility not found")
    return facility
