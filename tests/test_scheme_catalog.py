import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCHEME_ROOT = ROOT / "integrations" / "livestock-scheme-advisor"


def test_all_catalogue_schemes_have_english_and_marathi_copy():
    schemes = json.loads(
        (SCHEME_ROOT / "frontend" / "schemes.json").read_text(encoding="utf-8")
    )
    entries = {code: value for code, value in schemes.items() if not code.startswith("_")}
    assert len(entries) == 66
    for code, entry in entries.items():
        assert entry["en"]["name"], code
        assert entry["en"]["short"], code
        assert entry["mr"]["name"], code
        assert entry["mr"]["short"], code


def test_compact_model_coverage_is_a_subset_of_the_catalogue():
    schemes = json.loads(
        (SCHEME_ROOT / "frontend" / "schemes.json").read_text(encoding="utf-8")
    )
    catalogue_codes = {code for code in schemes if not code.startswith("_")}
    metadata = json.loads(
        (SCHEME_ROOT / "backend" / "models" / "compact_model_metadata.json").read_text(
            encoding="utf-8"
        )
    )
    model_codes = {
        label.removeprefix("elig_") for label in metadata["model_label_cols"]
    }
    assert len(model_codes) == 16
    assert model_codes <= catalogue_codes
    assert len(catalogue_codes - model_codes) == 50
