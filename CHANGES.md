# Farm2Feed — corrected project (26 issues)

Everything below was verified on Ubuntu 24.04 / Python 3.12 / Node 22 with the project's own test suite plus
real PostgreSQL 16 and MySQL 8.0 servers. **Windows 10/11 and macOS 12.7.6 could not be run** (see section 5).
Your original archive was never modified. `.env` (real secrets) and `.venv` (a Windows environment built on another
computer, ~385 MB) are intentionally **not** in this ZIP; setup creates both fresh. Keep your own `.env` if you have one.

## 1. Status of the 26 issues

| # | Issue | Status | Evidence |
|---|---|---|---|
| 1 | Unauthorized cow deletion | **Fixed** | `/delete` needs a doctor session (+ CSRF token); anonymous and farmer requests refused, doctor works — `test_security_and_workflows`, `test_csrf` |
| 2 | Default doctor password | **Fixed (incl. shipped database)** | No password in code/scripts. Fresh DB: random `DOCTOR_PASSWORD` in `.env`, or an unusable password until `reset_doctor_passwords.py` is run; nothing is printed or logged. Published demo passwords (`Vet@2026`) are refused at login unless `FARM2FEED_DEMO_MODE=1`. `reset_doctor_passwords.py` resets only accounts still on a published password (or `--all` / `--email` / `--prompt`), backs up SQLite first. Setup scripts run it. **All 10 doctor accounts in the shipped database were on the published password; they are now switched to "no password set" (only `doctors.password_hash` changed, every other value is identical). Run setup or `python scripts/reset_doctor_passwords.py` once to give each a new random password, shown once.** Verified by `test_shipped_database_has_no_doctor_account_on_a_published_password`. |
| 3 | Safe, idempotent demo seed | **Fixed** | Counts only its 100 designated cows, checks duplicates before commit, takes a backup, never overwrites accounts/owned cows, refuses to mix into a foreign `FARM-xx`; repeat run adds nothing — `test_seed_safety` |
| 4 | Help requests / doctor replies | **Fixed** | One table (`farmers_assistance_requests`) for farmer, doctor and dashboard; reply visible to farmer; status-only update keeps the reply; invalid status rejected |
| 5 | Found-cow reports on owner page | **Fixed** | Shown only on the owning farmer's cow page; other farmers get 404 there, public page shows no report/contact data |
| 6 | Public QR page for logged-in farmers | **Fixed** | Farmers get the same minimal public page for cows they do not own |
| 7 | Authenticated image uploads | **Fixed** | Bearer token required; React sends it (bundle rebuilt); content decoded with Pillow, format must match extension, ≤5 MB, pixel cap |
| 8 | Secure KML import | **Fixed** | `X-Admin-Token` = `VET_IMPORT_TOKEN`; missing/invalid/unset → 403; generic 500 text, details only in server log |
| 9 | Unauthenticated `/register` | **Fixed** | Now requires a signed-in farmer or veterinarian (visitors go to the farmer login); farmers' cows join their herd; id/number validation and path-traversal fix kept — `test_security_and_workflows` |
| 10 | Vet-app imports / commands | **Fixed** | `python -m backend.scripts.import_kml`, `uvicorn backend.main:app` from `integrations/vet-app`; UTF-8 console output for Windows |
| 11 | npm lockfile | **Fixed** | 4 unreachable `package-firewall.replit.internal` URLs → registry.npmjs.org; `npm ci --legacy-peer-deps`, production build and 3 React tests pass; bundle byte-identical to a fresh build |
| 12 | MySQL / PostgreSQL | **Fixed (PostgreSQL 16, MySQL 8.0 verified)** | New `services/db_compat.py`, `database/schema_postgres.sql`, `schema_mysql.sql`, `requirements-postgres.txt`. Schema auto-created and idempotent, legacy MySQL schema (`database/schema.sql`) topped up without losing rows, Marathi text round-trips, full farmer/doctor/found-report/delete flow passes on both — `tests/test_server_databases.py`. SQLite unchanged and still the default |
| 13 | Animal-health preprocessing | **Resolved — no defect in the current pipeline** | See section 4 |
| 14 | Broken `.venv` | **Fixed (logic)** | Both setup scripts probe the venv and recreate it when it cannot run; not executed on Windows/macOS |
| 15 | Invalid age/milk values | **Fixed** | Non-numeric/negative → empty (also `health_score` on `/register`); valid values untouched |
| 16 | Scheme confidence | **Fixed** | Always-ineligible labels (`MH_GOSHALA`, `C_DIDF`) now 0.0 instead of 1.0; always-eligible stays 1.0 — checked against the real model through the API |
| 17 | Import counts | **Fixed** | Unchanged re-import → 0 new, 2,178 skipped — `test_vet_import_endpoint` |
| 18 | Missing cow photo | **Handled; the original file itself cannot be restored** | `6bcec0fb8895462caa29116806c1465b.jpg` (cow `COW-2DD6A5B8`) exists nowhere in the supplied project, so nothing was invented or copied from other photos and the database reference is untouched. Cow pages now say "image file is not available" instead of a broken image, and `scripts/repair_missing_photos.py` lists (or, with `--clear`, removes) dead references. To truly fix it, copy the original file into `uploads/` under that exact name — `test_missing_photo_file_is_handled_without_a_broken_image` |
| 19 | CSRF | **Fixed** | Per-session token in all 14 POST forms, `X-CSRF-Token` for animal-health and scheme-advisor requests (`/csrf-token`), Origin/Referer check, Secure cookie flag over HTTPS; bearer-token JSON API (`/api/…`, `/upload`) correctly exempt — forged, token-less, wrong-session and genuine requests tested |
| 20 | Doctor logout | **Fixed** | Removes only doctor keys |
| 21 | Help request cow ownership | **Fixed** | Cow must belong to the logged-in farmer |
| 22 | `weights_only=True` | **Fixed (static check)** | Set on both loaders; both checkpoints verified to contain only objects the safe loader allows. `torch.load` itself was not run (no PyTorch in the test machine) |
| 23 | Vet-app dependencies | **Fixed** | Pins aligned with the main requirements; every pinned package has a wheel for Windows x64 and macOS 12 Intel/ARM (PyPI metadata) |
| 24 | Tests never touch real data | **Fixed** | `tests/conftest.py` redirects the cow DB, QR/photo folders, marketplace JSON/uploads and the vet DB to temp locations; a checksum of every database/JSON/QR/upload file was identical before and after the full run |
| 25 | English/Marathi voice navigation | **Fixed (logic + simulated browser)** | See section 4 |
| 26 | Live doctor dashboard | **Fixed (API + simulated browser)** | See section 4 |

## 1b. Cow registration photo upload and live review (requested after the first delivery)

Cause found: the file input was hidden by CSS with no script, so nothing showed the chosen photo; the Review panel was static dashes; and farmer / veterinarian / public QR pages never displayed the uploaded photo (the public page did not even load it). Now: photo preview with name/size, type and size checks (browser + server, content verified, 4 MB limit with friendly 413 message), Remove button, keyboard-accessible chooser, a live review panel on both registration forms (fills as you type, shows a required-fields counter, English/Marathi), photo shown on owner, veterinarian and public pages. Files: `static/js/cow_register.js` (new), `static/css/style.css`, `templates/{farmer_cow_new,register_cow,farmer_cow_detail,doctor_cow_profile,cow_profile}.html`, `app.py` (`save_cow_image`, `cow_photo_url`, 413 handler, public page loads `image_path`). Tests: `tests/test_cow_registration_ui.py`, `tests/js/cow_register.test.js` (runs against the real rendered pages).

## 1c. Weather search showed nothing (requested after the second delivery)

The only city/town search is the Weather page (`/kisaath/weather`). The live weather service is not reachable from my test machine, so I could not watch the original failure; I fixed every code path that can leave the page empty and tested them against a local stand-in for the service:
- **Backend (`marketplace_api.py`)** — the place lookup only understood a bare name: "Pune, India", "Baramati, Maharashtra" or "Baramati town" found nothing. It now accepts those forms, Marathi (Devanagari) names, prefers the Indian place for ambiguous names (Hyderabad, Aurangabad) and honours a state hint. Upstream calls retry once, time out after 8 s (they could hang for 12 s x 2), results are cached for 10 minutes (the page makes two requests per search), and certificates are verified with the `certifi` bundle (Python installs for macOS often have no root certificates, which made every search fail with "temporarily unavailable"; `certifi` added to `requirements.txt`). Errors now say what happened (service unreachable / not accepted / unreadable / city not found).
- **Page (`Weather.js`)** — a reply that is not JSON, incomplete or slow no longer leaves an empty or crashed page: it shows a clear message, a 40-second client timeout re-enables the button, a failing 5-day forecast is reported while the current weather stays, and the place shows its state/country ("Baramati, Maharashtra, India"). Layout and every other control are unchanged; React build regenerated (`main.68b38917.js`).
- **Tests:** `tests/test_weather_api.py` (14, including retry, cache, outage, garbage reply, nothing listening), `src/Weather.test.js` (7). Not verified: a search against the real internet service.

## 1d. Weather page: wind, rain, humidity, evapotranspiration and irrigation guide (requested after the third delivery)

Additive only: every existing weather field, control and layout stays; the new data is extra keys in the existing API answers (`farm` in `/api/weather/current`, `pop` and `farm` on each `/api/weather/forecast` day), so older clients keep working.
- **Wind:** speed, gusts, direction (16-point compass and degrees, "from the NW", with an arrow showing where it blows), today's strongest wind and prevailing direction, plus a spraying/sprinkler tip.
- **Rain:** chance (%) and expected amount today (mm), rain falling now, and rain chance per day in the 5-day outlook.
- **Humidity:** now, **morning (6-10 am)** vs **afternoon (1-5 pm)** relative humidity, with a plain-language reading (dry afternoon air, humid/fungal risk, big morning-to-afternoon drop).
- **Evapotranspiration:** reference ET₀ in mm/day (FAO-56 Penman-Monteith, from the same provider) with a Low/Moderate/High/Very high class, and ET₀ per day in the outlook.
- **Irrigation guide:** choose a crop stage (just planted 0.4, growing fast 0.75, peak 1.15, ripening 0.7, or reference 1.0); the page estimates crop water use = ET₀ x crop factor, counts only real rain (showers under 2 mm ignored, larger rain at 80 %), says irrigate / wait / hold off, converts mm to litres per m² and per hectare, and adds a 3-day total. It is an estimate: your crop, soil and recent irrigation also matter.
- **Files:** `marketplace_api.py`, `kisanreact_app/src/{Weather.js,FarmConditions.js,farmWeather.js,wea.css}` (new: `FarmConditions.js`, `farmWeather.js`), tests `tests/test_weather_api.py`, `src/farmWeather.test.js`, `src/Weather.test.js`, rebuilt `kisanreact_app/build/`.
- **Verified:** 18 weather API tests, 22 React tests (helpers, panel, crop-stage change, old answer shape without farm data). **Not verified:** the numbers against the live Open-Meteo service (not reachable from my test machine) and the visual layout in a real browser; the field names follow Open-Meteo's published API.

## 2. Files changed (reason)

**Security / correctness (Python):** `app.py` (auth on delete, DB layer, CSRF, login block, doctor API, register hardening, assistance flow, validation, seed split), `services/db_compat.py` *(new)*, `marketplace_api.py`, `asgi.py`, `integrations/vet-app/backend/{routes/veterinary.py,services/veterinary_service.py,scripts/import_kml.py,requirements.txt}`, `integrations/livestock-scheme-advisor/backend/app.py`, `services/animal_health.py` (documentation of the verified preprocessing only).
**Database:** `database/schema_postgres.sql`, `database/schema_mysql.sql`, `requirements-postgres.txt` *(new)*.
**Scripts / setup:** `scripts/seed_demo_data.py`, `scripts/make_env.py`, `scripts/reset_doctor_passwords.py` *(new)*, `scripts/verify_animal_health_preprocessing.py` *(new)*, `setup_mac.sh`, `setup_windows.bat`, `.env.example`, `.gitignore`.
**Weather:** `marketplace_api.py`, `kisanreact_app/src/{Weather.js,Weather.test.js,wea.css}`, rebuilt `kisanreact_app/build/` (`main.3b59bc2c.*` replaced by `main.68b38917.*`), `requirements.txt` (`certifi`), `tests/test_weather_api.py`.
**Front end:** all 14 form templates (CSRF token), `templates/{base,cow_home,doctor_dashboard,doctor_assistance,farmer_help,farmer_cow_detail}.html`, `static/js/{voice-nav.js,doctor_live.js}` *(new)*, `static/js/home.js`, `static/css/{style,portal-home}.css`, `animal_health_ai/{templates/animal_health.html,static/script.js}`, scheme advisor `frontend/app.js`, React `src/KisanSaathiMarketplace.js` + rebuilt `kisanreact_app/build/` (the three superseded `main.5beedc6a.*` bundle files were replaced by `main.3b59bc2c.*`), `kisanreact_app/package-lock.json`.
**Docs / tests:** `README.md`, `DEMO_ACCOUNTS.md`, `integrations/vet-app/README.md`, `CHANGES.md`; `tests/conftest.py` + 9 new test files (`tests/js/*` for the browser scripts); `tests/test_db_fallback.py` and `tests/test_unified_routes.py` updated (no hard-coded password, authenticated upload).
Nothing else was removed or renamed; no table or column was dropped.

## 3. Test results

| Area | Result |
|---|---|
| Whole suite, default environment | **77 passed, 11 skipped** (skips = server DB tests without servers, DOM tests without jsdom, torch test) |
| Whole suite with PostgreSQL 16 + MySQL 8.0 + Node/jsdom | **87 passed, 1 skipped** (torch runtime test) |
| Backend / DB | SQLite, PostgreSQL, MySQL (fresh DB, repeat start, legacy MySQL schema upgrade) |
| Frontend | React: build OK, 3 tests pass; doctor-dashboard script: success / error / session-ended / empty / 304 / no HTML injection |
| Voice navigation | 78 English + Marathi phrases → expected page (incl. ambiguity, refusals, noise); 15 end-to-end simulated-browser checks (retry in other language, mic denied, cancel, missing target) |
| ML | Checkpoint parsed without PyTorch, ResNet18 re-implemented in NumPy and run on sample photos; PyTorch itself **not** run |

## 4. Details for issues 9, 13, 25, 26

**9 – `/register`.** Implications: anyone can create cow records; ids were client-chosen and went unchecked into the QR **file path** (a value like `../../x` could write a PNG outside `static/qr_codes` — fixed); non-numeric values were stored as text; anonymous cows have no owner so no farmer sees them; with issue 1 fixed they can no longer be deleted by anyone. Changes made: id restricted to letters/digits/`._-` (≤64), numeric validation, CSRF, a logged-in farmer who uses the form now owns the cow. Left as is: anonymous registration still works (public QR workflow preserved). *Proposed, not implemented because it changes who may register:* require farmer or doctor login for `/register`, or accept anonymous cows into a "pending" state a doctor approves.
**13.** Checkpoint = ResNet18, classes `foot-and-mouth, healthy, lumpy`, no metadata. The first BatchNorm layer's stored statistics reproduce under plain `Resize(224,224)+ToTensor` (variance ratio ≈1, channel-mean correlation 0.99) and are ~15× off under ImageNet normalisation; with ImageNet normalisation the network answers "lumpy 100%" for every image. The existing pipeline is therefore correct and was **not** changed. `python scripts/verify_animal_health_preprocessing.py` repeats the check (re-run it if weights are replaced). Limits: training data/accuracy unknown; sample photos were cows/farm photos, not diseased animals.
**25.** `static/js/voice-nav.js` + `home.js`. Understands English and Marathi (Devanagari) and common variants, picks the best of 3 recognizer alternatives, retries once in the other language, opens only links present on the page, offers tap-able choices for ambiguous commands ("schemes"), refuses delete/remove/log-out words, 0.8 s cancellable "Opening …" step. Existing search-by-voice remains the fallback. Needs Chrome/Edge/Safari + internet + mic permission (the button stays hidden in browsers without Web Speech, e.g. Firefox).
**26.** `/doctor/api/dashboard` (doctor-only, 401 otherwise, ETag/304, `?summary=1`) feeds the three counters and cow table every 30 s while the tab is visible (back-off on errors, status line for loading / live / error / session ended, "Refresh now"). Rows come only from the database; sample/demo cows (`COW001-003`, `COW-DEMO-*`) carry a **Demo** tag and a note counts them. Assistance page shows a banner when requests change. The existing cards/layout are unchanged.

## 5. Cross-platform matrix

| Layer | Windows 10 | Windows 11 | macOS 12.7.6 (Intel) |
|---|---|---|---|
| Python 3.11/3.12 + requirements.txt | Wheels exist for every pinned package (PyPI metadata); **not installed/run** | same | same; pins torch 2.2.2 / torchvision 0.17.2 / numpy<2 (last Intel-Mac builds) — verified to exist; **not run** |
| setup/run scripts | Reviewed (CRLF .bat, `py` launcher); **not run** | same | Reviewed (LF .sh; use `chmod +x`); **not run** |
| Paths, UTF-8, shell calls | No hard-coded separators or non-UTF-8 text opens found; console output forced to UTF-8 in vet script | same | same |
| SQLite (default) | Same code path as tested | same | same |
| PostgreSQL 16 / MySQL 8.0 | Drivers (`psycopg2-binary`, `mysql-connector-python`) have wheels / pure-Python wheel; server tests ran on Linux only | same | same |
| React build / tests | Node 22 on Linux; use Node 18–22 | same | same |
| Browser features (voice, live dashboard) | Simulated only | same | same |

## 6. Setup commands

Windows: delete the shipped `.venv`, double-click `setup_windows.bat`, then `run_windows.bat`.
macOS: `rm -rf .venv && chmod +x setup_mac.sh run_mac.sh && ./setup_mac.sh && ./run_mac.sh`.
Setup creates `.env`, resets any doctor account still on a published password (new passwords are shown once in that window), and checks the install. Open http://localhost:5001.
Optional: `pip install -r requirements-postgres.txt` or `-mysql.txt` and set `DB_TYPE` (see README); demo data: `python scripts/seed_demo_data.py`; tests: `python -m pytest -q`.

## 7. Remaining issues

1. #18 the original photo file cannot be restored (not in any archive); the app now handles its absence cleanly.
2. (resolved) #9 now requires login; #2 shipped accounts disabled until a password is set.
3. Not run on Windows 10/11 or macOS 12.7.6; real browsers (speech recognition, live dashboard) and PyTorch inference not run here.
4. PostgreSQL/MySQL support covers the main Flask app; the vet-app's own optional PostgreSQL mode (`DATABASE_URL=postgresql+asyncpg://…`) was not tested; MariaDB and other server versions untested.
5. Out of scope and unchanged: logout links are GET requests (CSRF-able nuisance), no login rate limiting, demo farmer accounts keep the documented demo password `FarmDemo@2026` (synthetic data only; set `DEMO_FARMER_PASSWORD`).

## 8. Data preserved

`integrations/vet-app/backend/veterinary.sqlite3`, `server/data.json`, all of `uploads/` and `static/qr_codes/` are byte-identical to your archive. `cow_qr_demo.sqlite3` is identical except the `password_hash` of the 10 doctor accounts (issue 2); all cows, farmers, farms, history and the vet directory are unchanged. No existing route, table, column, page or feature was removed.
