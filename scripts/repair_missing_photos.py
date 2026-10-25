"""List cows whose recorded photo file is missing from uploads/ (and optionally clear the dead reference).

    python scripts/repair_missing_photos.py            # report only, changes nothing
    python scripts/repair_missing_photos.py --clear    # set image_path to empty for those cows (SQLite backup first)

The original image cannot be recreated by this script. To restore a photo, copy the original file back into
uploads/ under the exact name shown here (the database reference then works again), or upload a new photo.
"""
import argparse
import shutil
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--clear", action="store_true", help="clear the dead image reference for the cows listed")
    parser.add_argument("--db", help="SQLite file to use instead of the configured database")
    args = parser.parse_args(argv if argv is not None else sys.argv[1:])

    import app
    if args.db:
        app.DB_PATH, app.DB_TYPE = str(Path(args.db).resolve()), "sqlite"
    uploads = Path(app.app.config["UPLOAD_FOLDER"])
    conn = app.get_db_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("SELECT cow_id, cow_name, image_path FROM cows WHERE image_path IS NOT NULL AND image_path <> ''")
        missing = [row for row in cursor.fetchall() if not (uploads / row["image_path"]).is_file()]
        if not missing:
            print("Every recorded cow photo exists.")
            return 0
        for row in missing:
            print(f"{row['cow_id']} ({row['cow_name']}): missing file {row['image_path']}")
        if not args.clear:
            print("\nNothing was changed. Restore the files above into uploads/, or re-run with --clear.")
            return 0
        if app.DB_TYPE == "sqlite":
            backup = Path(app.DB_PATH).with_name(Path(app.DB_PATH).name + ".bak-" + datetime.now().strftime("%Y%m%d%H%M%S"))
            shutil.copy2(app.DB_PATH, backup)
            print(f"Backup written to {backup.name}")
        for row in missing:
            cursor.execute("UPDATE cows SET image_path = NULL WHERE cow_id = %s", (row["cow_id"],))
        conn.commit()
        print(f"Cleared the photo reference of {len(missing)} cow(s).")
        return 0
    finally:
        cursor.close()
        conn.close()


if __name__ == "__main__":
    sys.exit(main())
