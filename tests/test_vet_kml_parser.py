import importlib.util
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PARSER_PATH = ROOT / "integrations" / "vet-app" / "backend" / "utils" / "kml_parser.py"
spec = importlib.util.spec_from_file_location("farm2feed_kml_parser", PARSER_PATH)
kml_parser = importlib.util.module_from_spec(spec)
spec.loader.exec_module(kml_parser)


def test_taluka_markers_accept_period_hyphen_and_multiword_locations():
    assert kml_parser._extract_taluka_from_text("Dispensary Tal. Akole") == "Akole"
    assert kml_parser._extract_taluka_from_text("Tal-Karjat, Dist Pune") == "Karjat"
    assert kml_parser._extract_taluka_from_text("Taluka Seloo Dist Wardha") == "Seloo"


def test_facility_type_word_mini_is_not_returned_as_taluka():
    name = "Taluka Mini Veterinary Polyclinic, AKOLE"
    assert kml_parser._extract_taluka_from_text(name) is None
    assert kml_parser._extract_taluka_from_clinic_name(name) == "Akole"


def test_official_clinic_address_taluka_takes_precedence_over_facility_name():
    name = "Taluka Mini Veterinary Polyclinic, Sangli."
    address = "Taluka Mini veterinary Polyclinic, Sangli taluka Miraj Dist Sangli"
    assert kml_parser._extract_taluka_from_address(address) == "Miraj"


def test_bundled_clinic_kml_import_has_no_mini_taluka_and_fills_named_clinic_locations():
    data_dir = ROOT / "integrations" / "vet-app" / "backend" / "data"
    records = kml_parser.parse_all_kml_files(str(data_dir))
    assert records
    assert all((record["taluka"] or "").casefold() != "mini" for record in records)

    akole = next(
        record for record in records
        if record["name"] == "Taluka Mini Veterinary Polyclinic, AKOLE"
    )
    assert akole["taluka"] == "Akole"
