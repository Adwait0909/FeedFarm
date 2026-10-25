"""
KML Parser for Maharashtra Animal Husbandry Department KML files.

Handles:
  - Veterinary_Dispensary.kml
  - District_and_Taluka_Level_Veterinary_Clinics.kml

Only Point placemarks are extracted (polygons/boundaries are skipped).
No data is invented — missing fields are stored as None.
"""

import re
import os
from lxml import etree
from typing import List, Dict, Optional

KML_NS = "http://www.opengis.net/kml/2.2"


def _tag(local: str) -> str:
    return f"{{{KML_NS}}}{local}"


def _get_ext_data(placemark, key: str) -> Optional[str]:
    """Extract value from ExtendedData/Data[@name=key]/value."""
    for data in placemark.findall(f".//{_tag('Data')}"):
        if data.get("name", "").upper() == key.upper():
            val_el = data.find(_tag("value"))
            if val_el is not None and val_el.text:
                return val_el.text.strip()
    return None


# Words that indicate a facility type rather than a taluka name. The source KML
# sometimes prefixes a facility name with "Taluka Mini Veterinary Polyclinic";
# treating the next word ("Mini") as a taluka corrupts the location filters.
_FACILITY_WORDS = {
    "mini", "veterinary", "vet", "dispensary", "polyclinic", "clinic",
    "hospital", "office", "centre", "center", "level", "district",
    "taluka", "tal", "animal", "husbandry", "department",
}

_DISTRICT_ALIASES = {
    "ahmednagar": "Ahilyanagar", "ahilyanagar": "Ahilyanagar",
    "aurangabad": "Chhatrapati Sambhajinagar",
    "chhatrapati sambhajinagar": "Chhatrapati Sambhajinagar",
    "ch. sambhajinagar": "Chhatrapati Sambhajinagar",
    "chh. sambhajinagar": "Chhatrapati Sambhajinagar",
    "chh.sambhajinagar": "Chhatrapati Sambhajinagar",
    "osmanabad": "Dharashiv", "dharashiv": "Dharashiv",
}

def normalize_district(value: Optional[str]) -> Optional[str]:
    """Canonicalize known district aliases and casing without guessing unknown names."""
    if not value:
        return None
    cleaned = " ".join(value.strip().split())
    return _DISTRICT_ALIASES.get(cleaned.casefold(), cleaned.title())

def _extract_taluka_from_text(value: str) -> Optional[str]:
    if not value:
        return None
    # KML addresses use several variants: "Tal. Akole", "Tal-Karjat",
    # "Tq Achalpur", and "Taluka Seloo Dist Wardha". Capture the full
    # administrative name up to the next address marker, rather than just its
    # first word.
    marker = re.compile(
        r"\b(?:Tal(?:uka)?|Tq|Tehsil)\b\.?\s*[:\-]?\s*"
        r"([A-Za-z][A-Za-z .'-]*?)"
        r"(?=\s*(?:,|;|\bDist(?:rict)?\b|\bTq\b|\bTal(?:uka)?\b|"
        r"\bPin\b|\d{5,6}\b|$))",
        re.I,
    )
    for match in marker.finditer(value):
        candidate = " ".join(match.group(1).strip(" .,-").split())
        words = candidate.split()
        if not words or words[0].casefold() in _FACILITY_WORDS:
            continue
        return candidate.title()
    return None


def _extract_taluka_from_clinic_name(name: str) -> Optional[str]:
    """Use the named location only for the KML's explicit Taluka Mini clinic form.

    The source clinic names often say "Taluka Mini Veterinary Polyclinic, AKOLE";
    "Mini" is the facility type, while the text after the comma names the place.
    Prefer explicit taluka markers from the address before calling this fallback.
    """
    match = re.search(
        r"\bTal(?:auka|uka)\s+Mini\s+Veterinary\s+Pol(?:y|u)?clinic"
        r"\s*[, ]+\s*([^,]+)",
        name or "",
        re.I,
    )
    if not match:
        return None
    candidate = " ".join(match.group(1).strip(" .,-").split())
    if not candidate or candidate.casefold() in _FACILITY_WORDS:
        return None
    return candidate.title()

def _extract_taluka_from_name(name: str) -> Optional[str]:
    return _extract_taluka_from_text(name)

def _extract_taluka_from_address(address: str) -> Optional[str]:
    return _extract_taluka_from_text(address)


def parse_dispensary_kml(filepath: str) -> List[Dict]:
    """
    Parse Veterinary_Dispensary.kml.

    Fields available:
      - name (Placemark name)
      - DISTRICT
      - COMPLETE ADDRESS
      - LONGITUDE / LATITUDE (also in <coordinates>)

    Returns list of dicts ready for DB insertion.
    """
    tree = etree.parse(filepath)
    root = tree.getroot()
    records = []

    for placemark in root.findall(f".//{_tag('Placemark')}"):
        # Skip if no Point element (polygon boundaries etc.)
        point = placemark.find(f".//{_tag('Point')}")
        if point is None:
            continue

        name_el = placemark.find(_tag("name"))
        name = name_el.text.strip() if name_el is not None and name_el.text else "Unknown"

        district = normalize_district(_get_ext_data(placemark, "DISTRICT"))
        address  = _get_ext_data(placemark, "COMPLETE ADDRESS")

        # Prefer ExtendedData lat/lon; fallback to <coordinates>
        lat_str = _get_ext_data(placemark, "LATITUDE")
        lon_str = _get_ext_data(placemark, "LONGITUDE")

        if lat_str and lon_str:
            try:
                lat = float(lat_str)
                lon = float(lon_str)
            except ValueError:
                continue
        else:
            coords_el = placemark.find(f".//{_tag('coordinates')}")
            if coords_el is None or not coords_el.text:
                continue
            parts = coords_el.text.strip().split(",")
            if len(parts) < 2:
                continue
            try:
                lon = float(parts[0])
                lat = float(parts[1])
            except ValueError:
                continue

        # Validate coordinates are within Maharashtra bounds
        if not (15.0 <= lat <= 23.0 and 72.0 <= lon <= 81.0):
            continue

        # Try to extract taluka from name or address
        taluka = _extract_taluka_from_address(address or "") or _extract_taluka_from_name(name)

        records.append({
            "name":          name,
            "facility_type": "Veterinary Dispensary",
            "district":      district,
            "taluka":        taluka,
            "address":       address,
            "latitude":      lat,
            "longitude":     lon,
            "department":    "Dept. of Animal Husbandry, Maharashtra State",
        })

    return records


def parse_clinic_kml(filepath: str) -> List[Dict]:
    """
    Parse District_and_Taluka_Level_Veterinary_Clinics.kml.

    Fields available:
      - name (Placemark name)
      - DISTRICT
      - COMPLETE ADDRESS
      - DEPARTMENTS
      - LONGITUDE / LATITUDE
      - SN (serial number)

    Returns list of dicts ready for DB insertion.
    """
    tree = etree.parse(filepath)
    root = tree.getroot()
    records = []

    for placemark in root.findall(f".//{_tag('Placemark')}"):
        point = placemark.find(f".//{_tag('Point')}")
        if point is None:
            continue

        name_el = placemark.find(_tag("name"))
        name = name_el.text.strip() if name_el is not None and name_el.text else "Unknown"

        district   = normalize_district(_get_ext_data(placemark, "DISTRICT"))
        address    = _get_ext_data(placemark, "COMPLETE ADDRESS")
        department = _get_ext_data(placemark, "DEPARTMENTS")

        lat_str = _get_ext_data(placemark, "LATITUDE")
        lon_str = _get_ext_data(placemark, "LONGITUDE")

        if lat_str and lon_str:
            try:
                lat = float(lat_str)
                lon = float(lon_str)
            except ValueError:
                continue
        else:
            coords_el = placemark.find(f".//{_tag('coordinates')}")
            if coords_el is None or not coords_el.text:
                continue
            parts = coords_el.text.strip().split(",")
            if len(parts) < 2:
                continue
            try:
                lon = float(parts[0])
                lat = float(parts[1])
            except ValueError:
                continue

        if not (15.0 <= lat <= 23.0 and 72.0 <= lon <= 81.0):
            continue

        # Determine type from name
        name_lower = name.lower()
        if "polyclinic" in name_lower or "district" in name_lower:
            ftype = "District Veterinary Polyclinic"
        elif "taluka" in name_lower:
            ftype = "Taluka Veterinary Clinic"
        else:
            ftype = "District/Taluka Veterinary Clinic"

        taluka = (
            _extract_taluka_from_address(address or "")
            or _extract_taluka_from_name(name)
            or _extract_taluka_from_clinic_name(name)
        )

        records.append({
            "name":          name,
            "facility_type": ftype,
            "district":      district,
            "taluka":        taluka,
            "address":       address,
            "latitude":      lat,
            "longitude":     lon,
            "department":    department or "Dept. of Animal Husbandry, Maharashtra State",
        })

    return records


def parse_all_kml_files(data_dir: str) -> List[Dict]:
    """Parse both KML files and return combined list."""
    dispensary_path = os.path.join(data_dir, "Veterinary_Dispensary.kml")
    clinic_path     = os.path.join(data_dir, "District_and_Taluka_Level_Veterinary_Clinics.kml")

    all_records = []

    if os.path.exists(dispensary_path):
        dispensaries = parse_dispensary_kml(dispensary_path)
        all_records.extend(dispensaries)
        print(f"[KML] Parsed {len(dispensaries)} dispensaries")
    else:
        print(f"[KML] WARNING: Dispensary KML not found at {dispensary_path}")

    if os.path.exists(clinic_path):
        clinics = parse_clinic_kml(clinic_path)
        all_records.extend(clinics)
        print(f"[KML] Parsed {len(clinics)} district/taluka clinics")
    else:
        print(f"[KML] WARNING: Clinic KML not found at {clinic_path}")

    print(f"[KML] Total records: {len(all_records)}")
    return all_records
