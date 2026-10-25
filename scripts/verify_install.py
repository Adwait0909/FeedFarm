"""Post-install self-check: confirms every part of Farm2Feed can be imported."""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

ok = True
if not ((3, 11) <= sys.version_info[:2] <= (3, 12)):
    print(f"    WARNING: Python {sys.version.split()[0]} is untested; use 3.11 or 3.12.")
    ok = False

try:
    import torch, torchvision
    print("    torch", torch.__version__, "| torchvision", torchvision.__version__)
    ckpt = torch.load(ROOT / "animal_health_ai" / "models" / "best_model.pth",
                      map_location="cpu", weights_only=True)
    print("    AI model classes:", ckpt["classes"])
    import asgi  # Flask app + veterinary API + scheme advisor API
    print("    Application imports OK (Flask, veterinary API, scheme API).")
except Exception as exc:  # noqa: BLE001
    ok = False
    print("    CHECK FAILED:", type(exc).__name__, exc)

sys.exit(0 if ok else 1)
