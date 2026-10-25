"""Run the browser-script tests (voice navigation, live doctor dashboard) with Node.js.

Skipped automatically when Node.js (or, for the DOM tests, jsdom) is not available.
"""
import pathlib
import shutil
import subprocess

import pytest

JS_DIR = pathlib.Path(__file__).parent / "js"
NODE = shutil.which("node")


@pytest.mark.skipif(NODE is None, reason="Node.js is not installed")
@pytest.mark.parametrize("script", ["voice-nav.test.js", "home_voice.test.js", "doctor_live.test.js"])
def test_browser_script(script):
    result = subprocess.run([NODE, str(JS_DIR / script)], capture_output=True, text=True, timeout=120)
    if result.returncode == 77:
        pytest.skip(result.stdout.strip())
    assert result.returncode == 0, result.stdout + result.stderr
    assert "FAIL" not in result.stdout


@pytest.mark.skipif(NODE is None, reason="Node.js is not installed")
@pytest.mark.parametrize("page", ["farmer", "doctor"])
def test_cow_registration_form_script_on_the_real_pages(page, tmp_path):
    import os
    import app
    client = app.app.test_client()
    if page == "farmer":
        client.post("/farmer/register", data={"full_name": "F", "email": "f@example.test", "phone": "1",
                                              "password": "abcdef", "confirm_password": "abcdef"})
        client.post("/farmer/farm", data={"farm_name": "F", "village": "v", "taluka": "t", "district": "Pune", "state": "MH"})
        html = client.get("/farmer/cows/new").data
    else:
        client.post("/doctor/login", data={"email": "doctor@farmcare.local", "password": os.environ["DOCTOR_PASSWORD"]})
        html = client.get("/register").data
    target = tmp_path / "form.html"
    target.write_bytes(html)
    result = subprocess.run([NODE, str(JS_DIR / "cow_register.test.js"), str(target)], capture_output=True, text=True, timeout=120)
    if result.returncode == 77:
        pytest.skip(result.stdout.strip())
    assert result.returncode == 0, result.stdout + result.stderr
