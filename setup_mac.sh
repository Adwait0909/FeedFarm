#!/usr/bin/env bash
# One-time setup for macOS 12 (Monterey) and later, Intel or Apple Silicon.
# Creates a private virtual environment (.venv) and installs everything into it.
set -e
cd "$(dirname "$0")"

echo "==> Looking for a compatible Python (3.11 or 3.12)..."
PYBIN=""
for candidate in python3.12 python3.11 \
    /Library/Frameworks/Python.framework/Versions/3.12/bin/python3 \
    /Library/Frameworks/Python.framework/Versions/3.11/bin/python3 \
    /usr/local/bin/python3.12 /usr/local/bin/python3.11 \
    /opt/homebrew/bin/python3.12 /opt/homebrew/bin/python3.11; do
  if command -v "$candidate" >/dev/null 2>&1; then
    PYBIN="$(command -v "$candidate")"
    break
  fi
done

if [ -z "$PYBIN" ]; then
  echo ""
  echo "No Python 3.11 or 3.12 found. (Python 3.13+ and 3.10 will NOT work.)"
  echo "Install Python 3.12 from https://www.python.org/downloads/release/python-3128/"
  echo "(choose the 'macOS 64-bit universal2 installer'), then run ./setup_mac.sh again."
  exit 1
fi
echo "    Using: $PYBIN ($("$PYBIN" --version))"

if [ -d .venv ] && ! .venv/bin/python -c "import sys" >/dev/null 2>&1; then
  echo "==> Existing .venv is broken or was created on another computer - recreating it ..."
  rm -rf .venv
fi
if [ ! -x .venv/bin/python ]; then
  echo "==> Creating virtual environment in .venv ..."
  "$PYBIN" -m venv .venv
else
  echo "==> Reusing existing virtual environment in .venv ..."
fi
# shellcheck disable=SC1091
source .venv/bin/activate

echo "==> Installing packages (PyTorch is large; this can take several minutes)..."
python -m pip install --upgrade pip setuptools wheel
python -m pip install -r requirements.txt

echo "==> Preparing .env ..."
python scripts/make_env.py

echo "==> Securing doctor accounts that still use a published demo password..."
python scripts/reset_doctor_passwords.py --known-defaults-only || echo "    (could not reset doctor passwords; run scripts/reset_doctor_passwords.py later)"

echo "==> Verifying the installation..."
python scripts/verify_install.py || echo "    (see the message above; the app may still start)"

echo ""
echo "Setup complete. Start the app with:  ./run_mac.sh   (or: bash run_mac.sh)"
