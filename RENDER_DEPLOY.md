# Deploying Farm2Feed on Render

One Render **web service** serves everything from a single address: the cow-passport and
farmer/doctor portals, Kisaath tools (`/kisaath/`), the veterinary locator (`/veterinary/`), the scheme
advisor (`/farmer/schemes/`), Animal Health AI (`/animal-health/`) and all APIs. Nothing points at
localhost: QR codes use the service's public address automatically.

## What was added for Render (nothing existing was removed or changed in behaviour)

| File | Purpose |
|---|---|
| `render.yaml` | Blueprint: build/start commands, health check, persistent disk, environment variables |
| `.python-version` | Pins Python 3.12.8. Render otherwise picks a newer Python, and `Pillow==10.4.0` has no wheels for it |
| `scripts/render_bootstrap.py` | Runs before the server starts: prepares the disk, copies bundled data **only if missing**, optional one-time demo seed. Never blocks startup |
| `app.py`, `marketplace_api.py` | Read an optional `DATA_DIR` (the disk) for the database, cow photos and marketplace data, and `RENDER_EXTERNAL_URL` for QR codes. With neither set, everything works exactly as before |

## Option A - Blueprint (new service)

1. Push the project to GitHub/GitLab (`.env` and the local database are git-ignored on purpose).
2. Render dashboard -> **New** -> **Blueprint** -> pick the repository. Render reads `render.yaml`.
3. Enter **`DOCTOR_PASSWORD`** when asked (any strong password, 8+ characters). It becomes the password of
   `doctor@farmcare.local` on the new database.
4. Apply. The first build is long (PyTorch is large). When the service is **Live**, open its `onrender.com` address.

## Option B - Settings for a service you already created by hand

| Setting | Value |
|---|---|
| Runtime | Python 3 |
| Build Command | `pip install --upgrade pip && pip install -r requirements.txt` |
| Start Command | `python scripts/render_bootstrap.py && uvicorn asgi:application --host 0.0.0.0 --port $PORT --proxy-headers --forwarded-allow-ips='*'` |
| Health Check Path | `/` |
| Instance type | **2 GB RAM or more** (PyTorch + AI models; 512 MB is not enough) |
| Disk (paid instances) | Mount path `/var/data`, 1 GB |

Environment variables: the same list as in `render.yaml` - `PYTHON_VERSION=3.12.8`, `PYTHONUTF8=1`,
`DB_TYPE=sqlite`, `DATA_DIR=/var/data`, `DATABASE_URL=sqlite+aiosqlite:////var/data/veterinary.sqlite3`,
`SECRET_KEY`, `MARKETPLACE_JWT_SECRET`, `VET_IMPORT_TOKEN` (three long random strings), `DOCTOR_PASSWORD`,
`SEED_DEMO_DATA=0`.

## After it is live

- **QR codes** point at your service address. Nothing to configure. For a custom domain add
  `SITE_BASE_URL=https://your-domain` (no trailing slash). QR pictures are redrawn each time a cow's QR
  page is opened, so old pictures fix themselves; **printed** tags made earlier still contain the old address.
- **Doctor login:** `doctor@farmcare.local` with the `DOCTOR_PASSWORD` you entered. That variable only applies
  when the database has no doctor yet; to change a password later, open the service **Shell** and run
  `python scripts/reset_doctor_passwords.py --email doctor@farmcare.local --prompt`.
- **Farmer login:** farmers create their own account on the Farmer page.
- **Demo data (optional):** `SEED_DEMO_DATA=1` (plus `DEMO_FARMER_PASSWORD` and `DEMO_DOCTOR_PASSWORD` in
  the dashboard) loads 100 synthetic cows, 10 demo farmers and 10 demo doctors **once**. The farmer demo
  password defaults to the published `FarmDemo@2026`, so set your own and do not enable this on a site with
  real users. Set it back to `0` afterwards.
- **Your data is kept** across restarts and redeploys: the database, cow photos and marketplace data live on
  the disk. The bootstrap script never overwrites or deletes anything there.

## Running without a disk (free / no persistence)

Delete the `disk:` block and the `DATA_DIR` and `DATABASE_URL` variables (and use a plan with enough RAM).
Everything still works, but Render's filesystem is wiped on every restart and deploy, so registered cows,
farmers and photos disappear. Use this only for a throw-away demo.

## Troubleshooting

| Symptom | Cause / fix |
|---|---|
| Build fails compiling Pillow/numpy | Python is not 3.12: check `.python-version` / `PYTHON_VERSION` |
| Service restarts, log says "Out of memory" | Instance too small; use 2 GB or more |
| "Security check failed" on every form | `SECRET_KEY` missing or changing between restarts; set it once |
| QR still shows localhost | Service not redeployed with this version, or `SITE_BASE_URL` set to a localhost value |
| `/kisaath/` or `/veterinary/` is a 404/503 | The prebuilt `kisanreact_app/build` or `integrations/vet-app/frontend/dist` folder was not committed |
