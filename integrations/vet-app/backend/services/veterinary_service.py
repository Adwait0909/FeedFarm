"""
Service layer for veterinary facility operations.
All business logic lives here — routes stay thin.
"""

from typing import List, Optional, Dict, Any

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.dialects.sqlite import insert as sqlite_insert

from ..models.veterinary import VeterinaryFacility
from ..utils.geo import haversine_km, bounding_box
from ..utils.kml_parser import parse_all_kml_files, normalize_district
from ..config import settings


# ── Facility Type Constants ──────────────────────────────────────────────────

VET_DISPENSARY = "veterinary dispensary"
DISTRICT_CLINIC = "district veterinary polyclinic"
TALUKA_CLINIC = "taluka veterinary clinic"


def _normalize_type(value: Optional[str]) -> Optional[str]:
    """
    Normalize facility type input from frontend/API.
    """
    if not value:
        return None

    return " ".join(value.strip().lower().split())


def _facility_type_condition(facility_type: Optional[str]):
    """
    Build a SQLAlchemy condition for the selected facility type.

    Supported frontend values:
      - Veterinary Dispensary
      - District Veterinary Polyclinic
      - Taluka Veterinary Clinic

    Also supports the old:
      - District/Taluka
    """

    normalized = _normalize_type(facility_type)

    if not normalized:
        return None

    db_type = func.lower(func.trim(VeterinaryFacility.facility_type))
    db_name = func.lower(func.trim(VeterinaryFacility.name))

    # ── Veterinary Dispensary ────────────────────────────────────────────────
    if normalized == VET_DISPENSARY:
        return db_type == VET_DISPENSARY

    # ── District Veterinary Polyclinic ───────────────────────────────────────
    if normalized == DISTRICT_CLINIC:
        return db_type == DISTRICT_CLINIC

    # ── Taluka Veterinary Clinic ─────────────────────────────────────────────
    #
    # Some KML records are currently stored as
    # "District Veterinary Polyclinic" even though their names contain
    # "Taluka". Therefore we support both:
    #
    # 1. Correctly classified records
    # 2. Existing KML records whose name identifies them as Taluka facilities
    #
    if normalized == TALUKA_CLINIC:
        return or_(
            db_type == TALUKA_CLINIC,
            and_(
                db_name.ilike("%taluka%"),
                db_type != VET_DISPENSARY,
            ),
        )

    # ── Backward compatibility ───────────────────────────────────────────────
    if normalized in {
        "district/taluka",
        "district and taluka",
        "district taluka",
    }:
        return or_(
            db_type == DISTRICT_CLINIC,
            db_type == TALUKA_CLINIC,
            db_name.ilike("%taluka%"),
        )

    # Unknown value:
    # Do not silently return everything.
    return db_type == normalized


# ── KML Import ────────────────────────────────────────────────────────────────

async def import_kml_to_db(db: AsyncSession) -> Dict[str, int]:
    """
    Parse both KML files and upsert into the database.

    Uses ON CONFLICT DO NOTHING so re-running the importer
    does not create duplicate facilities.

    Returns:
        {
            "inserted": int,
            "skipped": int,
            "total_parsed": int
        }
    """

    records = parse_all_kml_files(settings.KML_DATA_DIR)

    if not records:
        return {
            "inserted": 0,
            "skipped": 0,
            "total_parsed": 0,
        }

    existing_keys = {
        (name, lat, lon)
        for name, lat, lon in (
            await db.execute(
                select(
                    VeterinaryFacility.name,
                    VeterinaryFacility.latitude,
                    VeterinaryFacility.longitude,
                )
            )
        ).all()
    }
    new_keys = {(r["name"], r["latitude"], r["longitude"]) for r in records} - existing_keys
    inserted = len(new_keys)
    skipped = len(records) - inserted

    # Keep multi-row inserts under SQLite's traditional 999-bind-parameter
    # limit (each facility contributes ten columns).
    batch_size = 50 if db.bind.dialect.name == "sqlite" else 200
    for batch_start in range(0, len(records), batch_size):
        batch = records[batch_start:batch_start + batch_size]

        dialect = db.bind.dialect.name
        if dialect == "sqlite":
            stmt = sqlite_insert(VeterinaryFacility).values(batch).on_conflict_do_update(
                index_elements=["name", "latitude", "longitude"],
                set_={key: getattr(sqlite_insert(VeterinaryFacility).excluded, key)
                      for key in ("facility_type", "district", "taluka", "address", "department")},
            )
        else:
            stmt = pg_insert(VeterinaryFacility).values(batch).on_conflict_do_update(
                constraint="uq_facility_name_coords",
                set_={key: getattr(pg_insert(VeterinaryFacility).excluded, key)
                      for key in ("facility_type", "district", "taluka", "address", "department")},
            )

        await db.execute(stmt)

    await db.commit()

    return {
        "inserted": inserted,
        "skipped": skipped,
        "total_parsed": len(records),
    }


# ── Nearby Search ─────────────────────────────────────────────────────────────

async def get_nearby_facilities(
    db: AsyncSession,
    latitude: float,
    longitude: float,
    radius_km: float = 25.0,
    limit: int = 10,
    facility_type: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """
    Find veterinary facilities within radius_km of a location.

    Steps:
      1. Apply bounding-box pre-filter.
      2. Apply facility-type filter.
      3. Calculate exact Haversine distance.
      4. Keep facilities within radius.
      5. Sort by nearest first.
      6. Apply limit.

    Returns dictionaries with distance_km included.
    """

    min_lat, max_lat, min_lon, max_lon = bounding_box(
        latitude,
        longitude,
        radius_km,
    )

    q = select(VeterinaryFacility).where(
        and_(
            VeterinaryFacility.latitude.between(min_lat, max_lat),
            VeterinaryFacility.longitude.between(min_lon, max_lon),
        )
    )

    # Apply facility type filter
    type_condition = _facility_type_condition(facility_type)

    if type_condition is not None:
        q = q.where(type_condition)

    result = await db.execute(q)

    candidates = result.scalars().all()

    nearby = []

    for facility in candidates:

        distance = haversine_km(
            latitude,
            longitude,
            facility.latitude,
            facility.longitude,
        )

        if distance <= radius_km:

            nearby.append(
                _facility_to_dict(
                    facility,
                    distance_km=distance,
                )
            )

    # Nearest facilities first
    nearby.sort(
        key=lambda item: item["distance_km"]
    )

    return nearby[:limit]


# ── District / Taluka Search ──────────────────────────────────────────────────

async def get_facilities_by_district(
    db: AsyncSession,
    district: str,
    taluka: Optional[str] = None,
    facility_type: Optional[str] = None,
    limit: int = 50,
) -> List[Dict[str, Any]]:
    """
    Return facilities filtered by district,
    optionally by taluka and facility type.
    """

    requested_district = normalize_district(district) or district.strip()
    district_aliases = {requested_district}
    if requested_district == "Ahilyanagar": district_aliases.add("Ahmednagar")
    if requested_district == "Chhatrapati Sambhajinagar": district_aliases.add("Aurangabad")
    if requested_district == "Dharashiv": district_aliases.add("Osmanabad")
    q = select(VeterinaryFacility).where(
        or_(*(VeterinaryFacility.district.ilike(name) for name in district_aliases))
    )

    # Optional taluka filter
    if taluka:
        q = q.where(
            VeterinaryFacility.taluka.ilike(
                f"%{taluka.strip()}%"
            )
        )

    # Facility type filter
    type_condition = _facility_type_condition(
        facility_type
    )

    if type_condition is not None:
        q = q.where(type_condition)

    q = (
        q.order_by(VeterinaryFacility.name)
        .limit(limit)
    )

    result = await db.execute(q)

    return [
        _facility_to_dict(facility)
        for facility in result.scalars().all()
    ]


# ── District / Taluka Lists ───────────────────────────────────────────────────

async def get_all_districts(
    db: AsyncSession,
) -> List[str]:
    """
    Return sorted list of unique district names.
    """

    result = await db.execute(
        select(VeterinaryFacility.district)
        .where(
            VeterinaryFacility.district.isnot(None)
        )
        .distinct()
        .order_by(VeterinaryFacility.district)
    )

    # Merge casing variants and known historic district names so the dropdown
    # does not show AKOLA and Akola as separate choices.
    return sorted({normalize_district(row[0]) for row in result.all() if row[0]}, key=str.casefold)


async def get_talukas_by_district(
    db: AsyncSession,
    district: str,
) -> List[str]:
    """
    Return sorted list of unique talukas
    belonging to a district.
    """

    requested_district = normalize_district(district) or district.strip()
    aliases = {requested_district}
    if requested_district == "Ahilyanagar": aliases.add("Ahmednagar")
    if requested_district == "Chhatrapati Sambhajinagar": aliases.add("Aurangabad")
    if requested_district == "Dharashiv": aliases.add("Osmanabad")
    result = await db.execute(
        select(VeterinaryFacility.taluka)
        .where(and_(or_(*(VeterinaryFacility.district.ilike(name) for name in aliases)),
                    VeterinaryFacility.taluka.isnot(None)))
        .distinct().order_by(VeterinaryFacility.taluka)
    )
    bad_values = {"mini", "veterinary", "dispensary", "polyclinic", "clinic", "hospital", "taluka", "tal"}
    cleaned = {" ".join(str(row[0]).split()).title() for row in result.all() if row[0] and str(row[0]).strip().casefold() not in bad_values}
    return sorted(cleaned, key=str.casefold)


# ── Single Facility ───────────────────────────────────────────────────────────

async def get_facility_by_id(
    db: AsyncSession,
    facility_id: int,
) -> Optional[Dict[str, Any]]:
    """
    Get one veterinary facility by ID.
    """

    result = await db.execute(
        select(VeterinaryFacility).where(
            VeterinaryFacility.id == facility_id
        )
    )

    facility = result.scalar_one_or_none()

    if not facility:
        return None

    return _facility_to_dict(facility)


# ── Stats ─────────────────────────────────────────────────────────────────────

async def get_facility_stats(
    db: AsyncSession,
) -> Dict[str, Any]:
    """
    Return total facilities and counts by stored facility type.
    """

    total_result = await db.execute(
        select(
            func.count(VeterinaryFacility.id)
        )
    )

    total = total_result.scalar() or 0

    type_result = await db.execute(
        select(
            VeterinaryFacility.facility_type,
            func.count(VeterinaryFacility.id),
        )
        .group_by(
            VeterinaryFacility.facility_type
        )
        .order_by(
            VeterinaryFacility.facility_type
        )
    )

    by_type = {
        row[0]: row[1]
        for row in type_result.all()
    }

    return {
        "total": total,
        "by_type": by_type,
    }


# ── Helpers ───────────────────────────────────────────────────────────────────

def _get_display_facility_type(
    facility: VeterinaryFacility,
) -> str:
    """
    Determine the display type.

    Some existing KML records have:
        facility_type = "District Veterinary Polyclinic"

    while their name clearly identifies them as a
    Taluka facility, e.g.:
        "Taluka Mini veterinary Polyclinic, KALYAN"

    For those records, display them as Taluka Veterinary Clinic.
    """

    stored_type = (
        facility.facility_type
        or "Not available"
    )

    name = (
        facility.name
        or ""
    ).lower()

    if (
        stored_type.lower().strip()
        == DISTRICT_CLINIC
        and "taluka" in name
    ):
        return "Taluka Veterinary Clinic"

    return stored_type


def _facility_to_dict(
    f: VeterinaryFacility,
    distance_km: Optional[float] = None,
) -> Dict[str, Any]:
    """
    Convert SQLAlchemy facility object
    into API response dictionary.
    """

    d = {
        "id": f.id,
        "name": f.name,

        # Correct display classification for
        # currently misclassified Taluka KML records.
        "facility_type": _get_display_facility_type(f),

        "district": (
            f.district
            or "Not available"
        ),

        "taluka": (
            f.taluka
            or "Not available"
        ),

        "address": (
            f.address
            or "Not available"
        ),

        "latitude": f.latitude,
        "longitude": f.longitude,

        "department": (
            f.department
            or "Not available"
        ),

        "contact": (
            "Contact number not available"
        ),

        "opening_hours": (
            "Opening hours not available"
        ),
    }

    if distance_km is not None:
        d["distance_km"] = round(
            distance_km,
            2,
        )

    return d