"""Create .env from .env.example with fresh random secrets (all platforms)."""
import secrets
from pathlib import Path

root = Path(__file__).resolve().parents[1]
target, example = root / ".env", root / ".env.example"

if target.exists():
    print("    .env already exists - leaving it unchanged.")
else:
    lines = []
    for line in example.read_text(encoding="utf-8").splitlines():
        if line.startswith("SECRET_KEY="):
            line = "SECRET_KEY=" + secrets.token_hex(32)
        elif line.startswith("MARKETPLACE_JWT_SECRET="):
            line = "MARKETPLACE_JWT_SECRET=" + secrets.token_hex(32)
        elif line.startswith("DOCTOR_PASSWORD="):
            line = "DOCTOR_PASSWORD=" + secrets.token_urlsafe(14)
            print("    A random initial doctor password was saved in .env (DOCTOR_PASSWORD).")
            print("    It applies only when the database has no doctor account yet.")
        lines.append(line)
    # UTF-8 without BOM, so python-dotenv reads the first key correctly.
    target.write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")
    print("    Created .env with fresh random secrets.")
