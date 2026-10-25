import sqlite3
import app


def reset_data():
    conn = sqlite3.connect(app.DB_PATH)
    try:
        conn.execute("DELETE FROM farmers_assistance_requests")
        conn.execute("DELETE FROM cow_medical_history")
        conn.execute("DELETE FROM cows")
        conn.execute("DELETE FROM farms")
        conn.execute("DELETE FROM farmers")
        conn.commit()
    finally:
        conn.close()


def test_farmer_isolation_and_qr_persistence():
    reset_data()
    client = app.app.test_client()

    # Register Farmer A and create farm + cow
    client.post('/farmer/register', data={
        'full_name': 'Farmer A', 'email': 'a@example.com', 'phone': '9001', 'password': 'p', 'confirm_password': 'p'
    }, follow_redirects=True)
    client.post('/farmer/login', data={'email': 'a@example.com', 'password': 'p'}, follow_redirects=True)
    client.post('/farmer/farm', data={'farm_name': 'A', 'village': 'V', 'taluka': 'T', 'district': 'D', 'state': 'S'}, follow_redirects=True)
    resp = client.post('/farmer/cows/new', data={'cow_name': 'A1', 'local_cow_number': '001', 'breed': 'Gir', 'cow_type': 'Dairy', 'gender':'Female'}, follow_redirects=True)
    assert resp.status_code == 200
    body = resp.get_data(as_text=True)
    assert 'COW' in body or 'QR' in body

    # Extract cow id from redirect to qr or success page
    # Register Farmer B and check they cannot see A's cows
    client.get('/farmer/logout')
    client.post('/farmer/register', data={'full_name': 'Farmer B', 'email': 'b@example.com', 'phone': '9002', 'password': 'p', 'confirm_password': 'p'}, follow_redirects=True)
    client.post('/farmer/login', data={'email': 'b@example.com', 'password': 'p'}, follow_redirects=True)
    dash = client.get('/farmer', follow_redirects=True)
    assert 'A1' not in dash.get_data(as_text=True)

    # Public homepage should not show cow lists
    public = client.get('/', follow_redirects=True)
    assert 'A1' not in public.get_data(as_text=True)
