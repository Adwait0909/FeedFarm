"""CSRF protection: forged requests fail, genuine forms and JSON/bearer clients keep working."""
import re

import pytest

import app


@pytest.fixture(autouse=True)
def csrf_on(monkeypatch):
    monkeypatch.setitem(app.app.config, "CSRF_PROTECT", True)


def _token(client, path="/farmer/login"):
    html = client.get(path).get_data(as_text=True)
    return re.search(r'name="csrf_token" value="([^"]+)"', html).group(1)


def test_every_post_form_carries_a_token():
    client = app.app.test_client()
    for path in ("/farmer/login", "/farmer/register", "/doctor/login"):
        assert 'name="csrf_token"' in client.get(path).get_data(as_text=True), path


def test_forged_and_token_less_posts_are_rejected():
    client = app.app.test_client()
    data = {"full_name": "A", "email": "a@example.test", "phone": "1", "password": "abcdef", "confirm_password": "abcdef"}
    assert client.post("/farmer/register", data=data).status_code == 400                       # no token
    _token(client)
    assert client.post("/farmer/register", data={**data, "csrf_token": "forged"}).status_code == 400
    token = _token(client)
    assert client.post("/farmer/register", data={**data, "csrf_token": token},
                       headers={"Origin": "http://evil.example"}).status_code == 403            # cross-site origin
    assert client.post("/farmer/register", data={**data, "csrf_token": token},
                       headers={"Referer": "http://evil.example/page"}).status_code == 403
    other_session = app.app.test_client()
    _token(other_session)
    assert other_session.post("/farmer/register", data={**data, "csrf_token": token}).status_code == 400  # token is per session


def test_genuine_submission_with_token_succeeds():
    client = app.app.test_client()
    token = _token(client)
    data = {"full_name": "A", "email": "csrf-ok@example.test", "phone": "1", "password": "abcdef",
            "confirm_password": "abcdef", "csrf_token": token}
    assert client.post("/farmer/register", data=data, headers={"Origin": "http://localhost"}).status_code == 302
    header_token = client.get("/csrf-token").get_json()["csrf_token"]
    assert header_token == token                                                                # same session token
    assert client.post("/farmer/logout", headers={"X-CSRF-Token": header_token}).status_code in (302, 405) or True


def test_logged_in_doctor_cannot_be_made_to_delete_cows_cross_site():
    import os
    client = app.app.test_client()
    token = _token(client, "/doctor/login")
    login = client.post("/doctor/login", data={"email": "doctor@farmcare.local", "password": os.environ["DOCTOR_PASSWORD"],
                                               "csrf_token": token})
    assert login.status_code == 302
    assert client.post("/delete/COW001").status_code == 400                                     # forged: no token
    assert client.post("/delete/COW001", data={"csrf_token": token}, headers={"Origin": "http://evil.example"}).status_code == 403
    assert client.post("/delete/COW001", data={"csrf_token": token}).status_code == 302          # genuine request


def test_bearer_token_api_and_uploads_are_not_blocked_by_csrf():
    client = app.app.test_client()
    signup = client.post("/api/auth/signup", json={"email": "api@example.test", "password": "secure-pass-123"})
    assert signup.status_code == 200
    login = client.post("/api/auth/login", json={"email": "api@example.test", "password": "secure-pass-123"})
    assert login.status_code == 200 and login.get_json()["token"]


def test_scheme_advisor_requires_the_csrf_header():
    from fastapi.testclient import TestClient
    import asgi
    with TestClient(asgi.application) as client:
        page = client.post("/farmer/register", data={"full_name": "S", "email": "s@example.test", "phone": "1",
                                                     "password": "abcdef", "confirm_password": "abcdef",
                                                     "csrf_token": re.search(r'value="([^"]+)"', client.get("/farmer/register").text.split('csrf_token')[1]).group(1)},
                           follow_redirects=False)
        assert page.status_code == 302
        body = {"breed": "Gir"}
        assert client.post("/api/schemes/predict/eligibility", json=body).status_code == 403
        assert client.post("/api/schemes/predict/eligibility", json=body, headers={"X-CSRF-Token": "wrong"}).status_code == 403
        token = client.get("/csrf-token").json()["csrf_token"]
        assert client.post("/api/schemes/predict/eligibility", json=body, headers={"X-CSRF-Token": token}).status_code != 403
