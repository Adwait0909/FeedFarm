"""
One-time KML import script.

Usage (from integrations/vet-app):
    python -m backend.scripts.import_kml
    (or simply: python backend/scripts/import_kml.py)

Run this ONCE after setting up the database.
Safe to re-run — duplicates are automatically skipped.
"""

import asyncio
import sys
import os

# Windows consoles default to a legacy code page; keep the status symbols printable.
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

# The backend uses package-relative imports, so make its parent folder importable
# and import it as the package "backend".
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from backend.database import init_db, AsyncSessionLocal
from backend.services.veterinary_service import import_kml_to_db


async def main():
    print("=" * 55)
    print("Maharashtra Veterinary Facilities — KML Import")
    print("=" * 55)

    # Ensure tables exist
    print("\n[1/3] Initialising database tables…")
    await init_db()
    print("      ✅ Tables ready")

    # Import KML data
    print("\n[2/3] Parsing KML files…")
    async with AsyncSessionLocal() as db:
        result = await import_kml_to_db(db)

    print("\n[3/3] Import complete!")
    print(f"      Total parsed : {result['total_parsed']}")
    print(f"      Inserted     : {result['inserted']}")
    print(f"      Skipped (dup): {result['skipped']}")
    print()
    print("You can now start the FastAPI server:")
    print("  uvicorn backend.main:app --reload --port 8000")
    print("=" * 55)


if __name__ == "__main__":
    asyncio.run(main())
