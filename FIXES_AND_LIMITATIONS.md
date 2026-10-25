# Farm2Feed repair notes and limitations

## Changes in this package

- The scheme advisor returns all 66 entries in the catalogue. The 16 entries with compact-model outputs are marked as **model estimates**; the other 50 are **not evaluated** and are not treated as ineligible.
- Scheme summaries now count model-scored and unscored entries separately. A missing original top-1 ranking model uses a clearly named eligibility-confidence fallback, and recommendations are restricted to model-estimated eligible schemes. It no longer promotes an unscored or model-negative scheme when there are no eligible matches.
- The scheme advisor's English and Marathi interface now explains the coverage gap, model-estimate status, and ranking fallback. Its 66 scheme names and descriptions have English and Marathi entries.
- The KML parser recognizes explicit `Tal.`, `Tal-`, `Tq`, and `Tehsil` address markers, keeps multiword names, and uses the place portion of the source's “Taluka Mini Veterinary Polyclinic, <place>” name only when no explicit taluka appears in the address. It does not return the facility word “Mini” as a taluka. The importer continues to use the bundled KML data and does not invent records.
- Marathi veterinary labels now include normalized district aliases and facility categories in lists, cards, details, and map popups. Facility names, addresses, and taluka names remain in their supplied source text because the archive does not include a verified Marathi translation table for those fields.
- Installer scripts now reuse an existing `.venv` rather than deleting it on each setup run. SQLAlchemy is constrained to the 2.0 series; the supported setup scripts target Python 3.11 and 3.12.
- No existing dataset, user/demo database, image model weights, or app routes were intentionally removed.

## Scheme and model limitations

- The scheme catalogue has 66 codes, but `compact_model_metadata.json` lists only 16 model labels. The other 50 are returned as `unscored`, not as negative predictions.
- The supplied training data is generated from rule-pattern assumptions (`rules_manifest.json` reports 20,000 generated rows). The 2,965-row validation figures describe agreement with that generated data, not measured real-world eligibility accuracy. Some source manifest entries are explicitly marked `verify: true`; current application windows and individual eligibility must be confirmed with the official scheme portal or department.
- The original `top1_model.joblib` and `top1_label_encoder.joblib` are absent. The fallback is based on compact-model confidence and is not represented as the original ranking model.
- The archive does not contain the stated 2.18 GB eligibility model. It contains a compact eligibility artifact and separate animal-health and breed-image weights. This package's checks did not load/infer with either PyTorch image model, so image prediction quality and compatibility are not confirmed here.
- A validated, exhaustive administrative district/taluka translation source was not present in the archive. District aliases are canonicalized from the bundled KML; a full taluka translation list was not fabricated.

## Verification performed for this repair

- Python `compileall`, the scheme JavaScript parse check, shell syntax checks, and JSON parsing passed under the available Python 3.13.11 / Node 24.13 runtime.
- The six focused tests in `tests/test_vet_kml_parser.py` and `tests/test_scheme_catalog.py` passed.
- The compact eligibility artifact loaded and returned all 66 catalogue entries: 16 model estimates, 50 unscored, and no unscored entry falsely marked eligible or ineligible. The missing original ranking artifact triggered the confidence fallback; its picks were restricted to the model's estimated-eligible results.
- The full existing pytest suite ran on a disposable copy: **19 passed, 1 skipped**. The skip is the optional MySQL fallback test because `mysql-connector-python` is not installed.
- A FastAPI `TestClient` run with an in-memory SQLite database completed startup, imported/reconciled 2,178 facilities from the bundled KML files (1,987 dispensaries and 191 clinics), returned 33 distinct districts, and verified that every district's taluka list is deduplicated and excludes `Mini`. The `Ahmednagar` alias returns the same taluka list as `Ahilyanagar`. The nearby endpoint returned HTTP 200 for the sample coordinates (zero results within the requested radius). Scheme routes returned 401 without a farmer session; authenticated catalogue and prediction requests returned 200 with 66 entries and 16/50 coverage.
- Vite successfully rebuilt the veterinary production bundle. A separate model-load attempt confirmed the compact eligibility model loads; the breed classifier could not load because PyTorch is not installed in the verification runtime. The health-image model was not run.
- SQLAlchemy 2.0.54 and the SQLite startup/import path worked in the available Python 3.13.11 environment. The included installer scripts target Python 3.11/3.12; neither target interpreter nor a native Windows/macOS environment was available, so their installation flows were not exercised.
- Image-model inference, live browser interaction, third-party integrations, and native operating-system setup remain unverified.

## Supported installation targets

The bundled setup scripts select Python 3.11 or 3.12. Windows 10/11 and macOS Monterey 12.7.6 (Intel and Apple Silicon) are documented, but were not exercised on native operating systems in this repair environment. PyTorch installation remains platform/architecture dependent and requires internet access. The React production bundle has been rebuilt and is included. Consult `README.md` for setup steps.
