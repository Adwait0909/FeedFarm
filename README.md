# Farm2Feed

Farm2Feed combines the Cow QR digital-passport app and the KisanSaathi farming tools (weather, crop calendar, marketplace, schemes, veterinary finder, animal-health AI) behind **one server and one port**.

- `/` — Farm2Feed home page
- `/scan`, `/register`, `/farmer/...`, `/doctor/...` — Cow QR flows
- `/kisaath/` — KisanSaathi farming tools (weather, crop calendar, marketplace, government schemes, modern farming)
- `/animal-health/` — AI cattle-image screening and PDF report (no login)
- `/farmer/schemes/` — livestock-scheme advisor (farmer login required)
- `/veterinary/` — veterinary facility finder (no login)
- `/api/...` — same-origin APIs used by the pages above

The React frontends are pre-built and served by the server, so **Node.js is not needed to run the project**.


## Home page (redesigned)

The `/` page (`templates/cow_home.html`, `static/css/portal-home.css`, `static/js/home.js`) is now a mobile-first, bilingual (English / मराठी) landing page for farmers:

- Big touch-friendly shortcuts (scan QR, sick-animal check, find a vet) and a mobile bottom quick-bar
- "What do you need today?" guide that routes to the right tool
- Tool finder with typed and **voice** search (Chrome/Edge/Android) plus category filters
- Live weather card with farm advice (Open-Meteo, needs internet; falls back gracefully)
- Larger-text toggle, keyboard/screen-reader friendly, reduced-motion support
- FAQ and a Kisan Call Centre helpline link (verify the number/hours before publishing)

## Requirements

| | Windows 10 / 11 | macOS 12.7.6 (Monterey) and later |
|---|---|---|
| Python | **3.11 or 3.12** — 64-bit | **3.11 or 3.12** — universal2 where available |
| Free disk | ~3 GB (PyTorch) | ~3 GB |
| Internet | needed once for install; weather lookups need it at run time | same |

> Python 3.11 and 3.12 are the tested installation targets in the included scripts. Other versions are not supported by this package; Intel Macs in particular need a PyTorch release with Intel wheels.

## Windows 10 / 11 — step by step

1. Install **Python 3.12 (64-bit)** from <https://www.python.org/downloads/release/python-3128/> ("Windows installer (64-bit)").
   On the first installer screen **tick "Add python.exe to PATH"**, then Install.
2. Install the **Microsoft Visual C++ Redistributable** if you do not already have it (PyTorch needs it): <https://aka.ms/vs/17/release/vc_redist.x64.exe>
3. Unzip `Farm2Feed.zip` (right-click → Extract All). Keep the path short, e.g. `C:\Farm2Feed`.
4. Open the unzipped folder, then run the one-time setup — double-click **`setup_windows.bat`**, or in Command Prompt / PowerShell:

   ```bat
   cd C:\Farm2Feed
   setup_windows.bat
   ```

   (wait several minutes; PyTorch is large)
5. Start the app — double-click **`run_windows.bat`**, or:

   ```bat
   run_windows.bat
   ```

6. Open **http://localhost:5001** in your browser. Press `Ctrl+C` in the window to stop.

If Windows SmartScreen warns about the `.bat` files, choose *More info → Run anyway*.

## macOS 12.7.6 (Monterey) — step by step

1. Install **Python 3.12** from <https://www.python.org/downloads/release/python-3128/> (macOS universal2 installer). Do not use the system Python.
2. Unzip `Farm2Feed.zip` (double-click it), then open **Terminal** and run:

   ```bash
   cd ~/Downloads/Farm2Feed        # adjust to wherever you unzipped it
   bash setup_mac.sh               # one-time: creates .venv, installs everything (several minutes)
   bash run_mac.sh                 # starts the server
   ```

3. Open **http://localhost:5001**. Press `Ctrl+C` in Terminal to stop.

macOS uses port 5000 for *AirPlay Receiver*, which is why Farm2Feed defaults to **5001**. Change `PORT` in `.env` to use another port (and `SITE_BASE_URL` to match).

## Optional: load the 100-cow demo data

```bash
# Windows (after setup_windows.bat)
.venv\Scripts\activate
python scripts\seed_demo_data.py

# macOS
source .venv/bin/activate
python scripts/seed_demo_data.py
```

Sample logins are in `DEMO_ACCOUNTS.md`. The seed script is safe to repeat: it never deletes or overwrites existing cows, accounts or passwords, and it makes a timestamped backup of the SQLite file first. Try it on a copy with `python scripts/seed_demo_data.py --db copy.sqlite3`.

### Doctor (veterinarian) passwords

No password is built into the application any more. A fresh database gets the doctor account `doctor@farmcare.local` with the password stored in `.env` as `DOCTOR_PASSWORD` (created by setup with a random value). If your database already contains doctor accounts that still use the old published demo password, they are blocked from signing in until you run (the copy shipped with this project already has those 10 accounts switched to "no password set", so run this once, or just run setup):

```bash
python scripts/reset_doctor_passwords.py            # resets only those accounts and prints new random passwords once
python scripts/reset_doctor_passwords.py --email doctor@farmcare.local --prompt   # choose a password yourself
```

The setup scripts run this automatically and print each new password once. The script also handles accounts that have no password set yet. For a purely local demo you may set `FARM2FEED_DEMO_MODE=1` to allow the demo passwords.

## Troubleshooting

| Problem | Fix |
| --- | --- |
| Windows: `'py' is not recognized` / Python not found | Re-run the Python installer and tick **Add python.exe to PATH**; open a *new* terminal window. |
| Windows: `Microsoft Store` opens when typing `python` | Settings → Apps → Advanced app settings → App execution aliases → turn off the *python.exe* aliases. `setup_windows.bat` uses the `py` launcher so it normally avoids this. |
| Windows: `DLL load failed ... torch` / `c10.dll` | Install the Visual C++ Redistributable (step 2 above), then run `setup_windows.bat` again. |
| `Address already in use` / port 5001 busy | Change `PORT` in `.env` (e.g. `PORT=5050`) and open that port instead. |
| Setup says Python 3.11/3.12 not found | Install Python 3.12 (see above); 3.13+ and 3.10 are not supported. |
| `externally-managed-environment` (macOS) | Never `pip install` into Homebrew/system Python. `setup_mac.sh` uses a private `.venv`. |
| `A module that was compiled using NumPy 1.x cannot be run in NumPy 2.x` | Run `pip install "numpy<2"` inside the `.venv` (macOS). |
| Setup fails while downloading packages | Check your internet / proxy and run the setup script again; it is safe to repeat. |
| Page opens but weather is empty | Weather uses the free Open-Meteo service and needs internet. |
| MySQL driver build errors | MySQL is optional; the bundled SQLite database is the default. Only for `DB_TYPE=mysql`: `pip install -r requirements-mysql.txt`. |
| Want a clean start | Delete the `.venv` folder (and `.env` to regenerate secrets), then run the setup script again. |

## Manual install (any OS)

```bash
python -m venv .venv
# Windows: .venv\Scripts\activate     macOS/Linux: source .venv/bin/activate
python -m pip install -r requirements.txt
python scripts/make_env.py
python -m uvicorn asgi:application --port 5001
```

## Rebuild the Kisaath frontend

```bash
cd kisanreact_app
npm ci --legacy-peer-deps
npm run build
cd ..
```

The build is written to `kisanreact_app/build` and mounted under `/kisaath/` by Flask. The React router and marketplace API are configured for the shared path and host.

## Deployment

Install `requirements.txt`, configure the environment variables in `.env.example` (or the host's secrets manager), and run the included `Procfile` command:

```bash
uvicorn asgi:application --host 0.0.0.0 --port $PORT
```

For a public deployment, set `SITE_BASE_URL` to the public origin so generated cow QR codes point to the deployed app.

## Data and uploads

- Cow records stay in `cow_qr_demo.sqlite3`; cow photos and QR images are kept in `uploads/` and `static/qr_codes/`.
- Marketplace users and listings are stored in `server/data.json`; marketplace photos are stored in `uploads/marketplace/`.
- Back up the SQLite file, JSON data file, and uploads together before replacing or moving the project.

The included data and demo records were retained from the supplied Cow QR archive. Never commit `.env`; use private secrets for any public deployment (`SECRET_KEY`, `MARKETPLACE_JWT_SECRET`, `DOCTOR_PASSWORD`, `VET_IMPORT_TOKEN`). Set `SITE_BASE_URL=https://...` behind HTTPS so the session cookie is marked Secure.

## Weather page

`/kisaath/weather`: enter a city or town for current weather and a 5-day outlook, plus **farm conditions** (wind speed, gusts and direction; rain chance and amount; humidity now, in the morning and in the afternoon; reference evapotranspiration ET₀) and an **irrigation guide** that turns ET₀ and the rain forecast into an estimated water need for the crop stage you pick. Needs internet access from the server (set `WEATHER_GEOCODING_URL` / `WEATHER_FORECAST_URL` only if you use a proxy).

## Registering cows

Cow registration needs a signed-in farmer (Register Cow in the farmer area, or `/register`; the cow joins that farmer's herd) or a signed-in veterinarian (`/register`). Visitors who are not signed in are sent to the farmer login. Both forms now show a **photo preview** (PNG/JPG up to 4 MB, checked in the browser and again on the server) and a **live review** panel that fills in as you type. The uploaded photo is shown on the owner's, veterinarian's and public QR pages. If a record points to a photo file that is missing, the pages say so instead of showing a broken image; `python scripts/repair_missing_photos.py` lists such cows (add `--clear` to remove the dead reference).

## Databases: SQLite (default), MySQL, PostgreSQL

SQLite needs nothing extra. For a server database create an **empty** database, add the driver and set the variables in `.env`; the tables are created automatically on the first start (an existing, older database is topped up with missing columns, never emptied).

```bash
# PostgreSQL                                     # MySQL 8
pip install -r requirements-postgres.txt        pip install -r requirements-mysql.txt
DB_TYPE=postgres                                 DB_TYPE=mysql
PG_HOST=localhost  PG_PORT=5432                  DB_HOST=localhost  DB_PORT=3306
PG_USER=...  PG_PASSWORD=...  PG_NAME=...        DB_USER=...  DB_PASSWORD=...  DB_NAME=...
```

If the server cannot be reached the app logs a warning and falls back to SQLite, as before. The seed script (`scripts/seed_demo_data.py`) and `cow_qr_demo.sqlite3` are SQLite-only. To test against your own servers: `F2F_TEST_PG_HOST=... F2F_TEST_MYSQL_HOST=... python -m pytest tests/test_server_databases.py` (each test creates and drops its own temporary database).

## Home page voice navigation

The microphone on the home page understands English and Marathi (it listens in the page language and, if nothing matches, once more in the other language). Examples: "weather" / "हवामान", "scan cow QR" / "गायीचा क्यूआर स्कॅन करा", "register a new cow" / "नवीन गाय नोंदवा", "my cow is sick" / "माझी गाय आजारी आहे", "find a vet" / "जवळचा पशुवैद्य शोधा", "marketplace" / "मार्केटप्लेस", "crop calendar" / "पीक दिनदर्शिका". Unclear commands such as "schemes" offer a short list to tap; delete/remove/log-out words are refused; commands only ever open pages that exist on the home page. Browser support: Chrome, Edge and Safari (needs internet and microphone permission).

## Live doctor dashboard

The doctor dashboard refreshes its counters and cow table from `/doctor/api/dashboard` every 30 seconds while the tab is visible (with ETag caching and back-off on errors) and shows a status line (loading / live / error / session ended). Sample and demonstration cows are marked **Demo**. The assistance page shows a banner when requests are created or answered.

## Tests

```bash
python -m pytest -q          # uses temporary databases and folders; your real data is never touched
```

Node.js browser-script tests run automatically when Node is installed (DOM tests also need `npm ci --legacy-peer-deps` in `kisanreact_app`).

## Seed a complete demo herd

The supplied SQLite file contains only three cow records. To load the complete
100-cow demonstration, 10 farm/farmer profiles, 10 veterinarians, and linked
health timelines, run:

```bash
python scripts/seed_demo_data.py
```

This is repeatable and adds demonstration records without replacing existing
ones. Every generated health-history item is marked as synthetic demo data.
The doctor-to-cow links are stored on each medical-history record, with 60
distinct cow profiles linked to every seeded doctor. Sample sign-in details and
the security caveat are in `DEMO_ACCOUNTS.md`.

## Update notes (veterinary data / scheme advisor)

The scheme advisor lists all 66 catalogue entries, but only 16 have outputs from the supplied compact eligibility model. The other 50 are explicitly shown as not evaluated, never as ineligible. Model predictions and validation metrics are estimates from generated, rule-pattern training data, not verified eligibility decisions. See [`FIXES_AND_LIMITATIONS.md`](FIXES_AND_LIMITATIONS.md) for remaining data, model, and platform limitations.

The veterinary startup reconciles imported rows against the bundled official KML files on launch. The parser now prefers explicit taluka markers in addresses and avoids interpreting the facility word “Mini” as a location. Verified Marathi district and facility-type labels are displayed in the locator; facility names, addresses, and taluka names remain in source text where the archive provides no verified translations.
