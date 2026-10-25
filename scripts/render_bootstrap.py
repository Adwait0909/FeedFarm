"""Prepare persistent storage before the server starts (used by the Render start command).

    python scripts/render_bootstrap.py

What it does - and only when the DATA_DIR environment variable is set (on Render this is the
mount path of the persistent disk, /var/data); with DATA_DIR unset it does nothing at all:

  1. Creates DATA_DIR and checks that it is writable.
  2. Copies data that ships inside the deployed code into DATA_DIR **only where nothing exists yet**
     (database, cow photos, marketplace data). Existing files are never overwritten or deleted, so
     redeploys keep everything that users created.
  3. Optionally (SEED_DEMO_DATA=1) loads the synthetic demo data once. A marker file in DATA_DIR
     stops it from running again, because the seed insists on exactly 100 demonstration cows.

It never stops the server from starting: every problem is printed to the deploy log and the script
still exits with status 0.
"""
from __future__ import annotations

import os
import shutil
import sys
import traceback
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SEED_MARKER = ".demo_data_seeded"


def log(message: str) -> None:
    print(f"[render-bootstrap] {message}", flush=True)


def truthy(value: str | None) -> bool:
    return (value or "").strip().lower() in {"1", "true", "yes", "on"}


def copy_file_if_missing(source: Path, target: Path) -> bool:
    if not source.is_file() or target.exists():
        return False
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, target)
    return True


def copy_tree_if_missing(source: Path, target: Path) -> int:
    """Copy every file below `source` that has no counterpart below `target` yet."""
    copied = 0
    if not source.is_dir():
        return copied
    for item in source.rglob("*"):
        if item.is_file() and copy_file_if_missing(item, target / item.relative_to(source)):
            copied += 1
    return copied


def prepare_storage(data_dir: Path) -> None:
    data_dir.mkdir(parents=True, exist_ok=True)
    probe = data_dir / ".write_test"
    probe.write_text("ok", encoding="utf-8")
    probe.unlink()
    log(f"Persistent storage ready at {data_dir}")

    if copy_file_if_missing(ROOT / "cow_qr_demo.sqlite3", data_dir / "cow_qr_demo.sqlite3"):
        log("Copied the bundled database to persistent storage (first boot only).")
    else:
        log("Database: nothing to copy (already on the disk, or none bundled - a fresh one is created on demand).")

    copied = copy_tree_if_missing(ROOT / "uploads", data_dir / "uploads")
    log(f"Cow photos: {copied} bundled file(s) copied to persistent storage.")

    if copy_file_if_missing(ROOT / "server" / "data.json", data_dir / "server" / "data.json"):
        log("Copied the bundled marketplace data to persistent storage (first boot only).")


def seed_demo_data_once(data_dir: Path) -> None:
    if not truthy(os.environ.get("SEED_DEMO_DATA")):
        return
    marker = data_dir / SEED_MARKER
    if marker.exists():
        log("SEED_DEMO_DATA is on, but the demo data was already loaded earlier - skipping.")
        return
    log("SEED_DEMO_DATA is on: loading the synthetic demo data (runs once).")
    sys.path.insert(0, str(ROOT / "scripts"))
    sys.path.insert(0, str(ROOT))
    try:
        import seed_demo_data  # imports app, which already reads DATA_DIR

        # QR pictures are redrawn whenever a cow's QR page is opened, so skip writing 100 of them now.
        seed_demo_data.main(["--no-backup", "--no-qr"])
        marker.write_text("done\n", encoding="utf-8")
        log("Demo data loaded.")
    except SystemExit as exit_request:
        if exit_request.code not in (None, 0):
            log(f"Demo data was NOT loaded (seed exited with {exit_request.code!r}).")
        else:
            marker.write_text("done\n", encoding="utf-8")
    except Exception:
        log("Demo data was NOT loaded; the seed rolled back. Details:")
        traceback.print_exc()


def main() -> int:
    data_dir_value = (os.environ.get("DATA_DIR") or "").strip()
    if not data_dir_value:
        log("DATA_DIR is not set - using the project folder for data (nothing to prepare).")
        return 0
    data_dir = Path(data_dir_value)
    try:
        prepare_storage(data_dir)
    except Exception:
        log("Could not prepare persistent storage; the app will still try to start. Details:")
        traceback.print_exc()
        return 0
    try:
        seed_demo_data_once(data_dir)
    except Exception:
        traceback.print_exc()
    return 0


if __name__ == "__main__":
    sys.exit(main())
