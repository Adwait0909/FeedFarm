"""Securely reset doctor passwords (all platforms, any database backend).

Examples (run from the project folder with the virtual environment active):

    python scripts/reset_doctor_passwords.py                 # accounts on a published demo password, or with no password set yet
    python scripts/reset_doctor_passwords.py --all           # every doctor account
    python scripts/reset_doctor_passwords.py --email doctor@farmcare.local --prompt   # choose the password yourself
    python scripts/reset_doctor_passwords.py --dry-run       # show which accounts would change

New random passwords are shown once, on this terminal only. Only salted hashes are stored.
SQLite databases are copied to ``<file>.bak-<timestamp>`` before anything is changed.
"""
import argparse
import getpass
import secrets
import shutil
import sys
from datetime import datetime
from pathlib import Path

from werkzeug.security import check_password_hash, generate_password_hash

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))


def parse_args(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--email", help="reset only this doctor account")
    parser.add_argument("--all", action="store_true", help="reset every doctor account")
    parser.add_argument("--known-defaults-only", action="store_true",
                        help="reset only accounts whose password is a published demo password (default)")
    parser.add_argument("--disable-known-defaults", action="store_true",
                        help="make accounts on a published demo password unusable (no new password is generated or shown)")
    parser.add_argument("--prompt", action="store_true", help="type the new password instead of generating one (needs --email)")
    parser.add_argument("--dry-run", action="store_true", help="report what would change without changing anything")
    parser.add_argument("--db", help="SQLite file to use instead of the configured database")
    parser.add_argument("--no-backup", action="store_true", help="do not copy the SQLite file before changing it")
    return parser.parse_args(argv)


def main(argv=None):
    args = parse_args(argv if argv is not None else sys.argv[1:])
    if args.prompt and not args.email:
        sys.exit("--prompt needs --email so it is clear which account is changed.")

    import app  # noqa: E402  (loads .env and the configured database)

    if args.db:
        app.DB_PATH = str(Path(args.db).resolve())
        app.DB_TYPE = "sqlite"

    known = app.KNOWN_DEFAULT_DOCTOR_PASSWORDS
    conn = app.get_db_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("SELECT id, email, password_hash FROM doctors ORDER BY id")
        doctors = cursor.fetchall()
        if args.email:
            doctors = [d for d in doctors if d["email"].lower() == args.email.strip().lower()]
            if not doctors:
                sys.exit(f"No doctor account with e-mail {args.email!r}.")
        elif args.disable_known_defaults:
            doctors = [d for d in doctors if any(check_password_hash(d["password_hash"], p) for p in known)]
        elif not args.all:
            doctors = [d for d in doctors
                       if d["password_hash"].startswith("unset$")
                       or any(check_password_hash(d["password_hash"], p) for p in known)]

        if not doctors:
            print("No doctor accounts need a new password.")
            return 0
        if args.dry_run:
            for doctor in doctors:
                print(f"would reset: {doctor['email']}")
            return 0

        if app.DB_TYPE == "sqlite" and not args.no_backup:
            backup = Path(app.DB_PATH).with_name(Path(app.DB_PATH).name + ".bak-" + datetime.now().strftime("%Y%m%d%H%M%S"))
            shutil.copy2(app.DB_PATH, backup)
            print(f"Backup written to {backup.name}")

        if args.disable_known_defaults:
            for doctor in doctors:
                cursor.execute("UPDATE doctors SET password_hash = %s WHERE id = %s",
                               ("unset$" + secrets.token_urlsafe(24), doctor["id"]))
                print(f"{doctor['email']}  ->  sign-in disabled until a new password is set")
            conn.commit()
            return 0

        for doctor in doctors:
            if args.prompt:
                password = getpass.getpass(f"New password for {doctor['email']}: ")
                if len(password) < 8 or password in known or password != getpass.getpass("Repeat password: "):
                    sys.exit("Password rejected (min 8 characters, must match, must not be a published demo password).")
            else:
                password = secrets.token_urlsafe(12)
            cursor.execute("UPDATE doctors SET password_hash = %s WHERE id = %s",
                           (generate_password_hash(password), doctor["id"]))
            print(f"{doctor['email']}  ->  {'(the password you typed)' if args.prompt else password}")
        conn.commit()
        if not args.prompt:
            print("\nNote these passwords now: they are shown only once and are not stored anywhere.")
        return 0
    finally:
        cursor.close()
        conn.close()


if __name__ == "__main__":
    sys.exit(main())
