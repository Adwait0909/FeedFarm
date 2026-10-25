import sqlite3

import app


def reset_farmer_test_data():
    conn = sqlite3.connect(app.DB_PATH)
    try:
        conn.execute("DELETE FROM farmers_assistance_requests")
        conn.execute("DELETE FROM farms")
        conn.execute("DELETE FROM cow_medical_history")
        conn.execute("DELETE FROM cows")
        conn.execute("DELETE FROM farmers")
        conn.commit()
    finally:
        conn.close()


def test_farmer_can_register_and_login():
    reset_farmer_test_data()
    client = app.app.test_client()

    register_response = client.post(
        "/farmer/register",
        data={
            "full_name": "Asha Patil",
            "email": "farmer.test@example.com",
            "phone": "9876543211",
            "password": "Farmer@123",
            "confirm_password": "Farmer@123",
        },
        follow_redirects=True,
    )
    assert register_response.status_code == 200

    login_response = client.post(
        "/farmer/login",
        data={
            "email": "farmer.test@example.com",
            "password": "Farmer@123",
        },
        follow_redirects=True,
    )
    assert login_response.status_code == 200
    body = login_response.get_data(as_text=True)
    assert "Dashboard" in body or "farmer" in body.lower()


def test_farmer_can_create_farm_and_register_cow_with_uid_and_qr():
    reset_farmer_test_data()
    client = app.app.test_client()

    client.post(
        "/farmer/register",
        data={
            "full_name": "Farmer User",
            "email": "farmer.cow@example.com",
            "phone": "9876543212",
            "password": "Farmer@123",
            "confirm_password": "Farmer@123",
        },
        follow_redirects=True,
    )

    client.post(
        "/farmer/login",
        data={
            "email": "farmer.cow@example.com",
            "password": "Farmer@123",
        },
        follow_redirects=True,
    )

    farm_response = client.post(
        "/farmer/farm",
        data={
            "farm_name": "Shivaji Dairy",
            "village": "Khed",
            "taluka": "Pune City",
            "district": "Pune",
            "state": "Maharashtra",
            "service_area": "Pune",
        },
        follow_redirects=True,
    )
    assert farm_response.status_code == 200

    cow_response = client.post(
        "/farmer/cows/new",
        data={
            "cow_name": "Gauri",
            "local_cow_number": "KH-120",
            "breed": "Gir",
            "cow_type": "Dairy",
            "gender": "Female",
            "date_of_birth": "2021-03-15",
            "age": "5",
            "color": "Brown",
            "notes": "Good milk yield",
        },
        follow_redirects=True,
    )
    assert cow_response.status_code == 200
    body = cow_response.get_data(as_text=True)
    assert "COW" in body or "QR" in body
    assert "Gauri" in body


def test_local_cow_number_is_unique_per_farm_not_globally():
    reset_farmer_test_data()
    client = app.app.test_client()

    first_farmer = client.post(
        "/farmer/register",
        data={
            "full_name": "Farmer One",
            "email": "farmer.one@example.com",
            "phone": "9000000001",
            "password": "Farmer@123",
            "confirm_password": "Farmer@123",
        },
        follow_redirects=True,
    )
    assert first_farmer.status_code == 200

    second_farmer = client.post(
        "/farmer/register",
        data={
            "full_name": "Farmer Two",
            "email": "farmer.two@example.com",
            "phone": "9000000002",
            "password": "Farmer@123",
            "confirm_password": "Farmer@123",
        },
        follow_redirects=True,
    )
    assert second_farmer.status_code == 200

    client.post(
        "/farmer/login",
        data={
            "email": "farmer.one@example.com",
            "password": "Farmer@123",
        },
        follow_redirects=True,
    )
    client.post(
        "/farmer/farm",
        data={
            "farm_name": "Farm A",
            "village": "Khed",
            "taluka": "Pune City",
            "district": "Pune",
            "state": "Maharashtra",
            "service_area": "Pune",
        },
        follow_redirects=True,
    )

    client.post(
        "/farmer/cows/new",
        data={
            "cow_name": "Desi Cow A",
            "local_cow_number": "001",
            "breed": "Gir",
            "cow_type": "Dairy",
            "gender": "Female",
        },
        follow_redirects=True,
    )

    client.get("/farmer/logout")

    client.post(
        "/farmer/login",
        data={
            "email": "farmer.two@example.com",
            "password": "Farmer@123",
        },
        follow_redirects=True,
    )
    client.post(
        "/farmer/farm",
        data={
            "farm_name": "Farm B",
            "village": "Pimpri",
            "taluka": "Pune City",
            "district": "Pune",
            "state": "Maharashtra",
            "service_area": "Pune",
        },
        follow_redirects=True,
    )

    second_cow = client.post(
        "/farmer/cows/new",
        data={
            "cow_name": "Desi Cow B",
            "local_cow_number": "001",
            "breed": "Sahiwal",
            "cow_type": "Dairy",
            "gender": "Female",
        },
        follow_redirects=True,
    )

    assert second_cow.status_code == 200
    body = second_cow.get_data(as_text=True)
    assert "Desi Cow B" in body


def test_same_farm_duplicate_local_cow_number_is_rejected():
    reset_farmer_test_data()
    client = app.app.test_client()

    client.post(
        "/farmer/register",
        data={
            "full_name": "Farmer Duplicate",
            "email": "farmer.duplicate@example.com",
            "phone": "9000000011",
            "password": "Farmer@123",
            "confirm_password": "Farmer@123",
        },
        follow_redirects=True,
    )
    client.post(
        "/farmer/login",
        data={
            "email": "farmer.duplicate@example.com",
            "password": "Farmer@123",
        },
        follow_redirects=True,
    )
    client.post(
        "/farmer/farm",
        data={
            "farm_name": "Duplicate Farm",
            "village": "Saswad",
            "taluka": "Purandar",
            "district": "Pune",
            "state": "Maharashtra",
            "service_area": "Pune",
        },
        follow_redirects=True,
    )

    first = client.post(
        "/farmer/cows/new",
        data={
            "cow_name": "Same Farm Cow One",
            "local_cow_number": "001",
            "breed": "Gir",
            "cow_type": "Dairy",
            "gender": "Female",
        },
        follow_redirects=True,
    )
    assert first.status_code == 200

    second = client.post(
        "/farmer/cows/new",
        data={
            "cow_name": "Same Farm Cow Two",
            "local_cow_number": "001",
            "breed": "Holstein",
            "cow_type": "Dairy",
            "gender": "Female",
        },
        follow_redirects=True,
    )
    body = second.get_data(as_text=True)
    assert "already used on this farm" in body.lower()


def test_same_farmer_different_farms_accepts_same_local_number():
    reset_farmer_test_data()
    client = app.app.test_client()

    client.post(
        "/farmer/register",
        data={
            "full_name": "Farmer Two Farms",
            "email": "farmer.twofarms@example.com",
            "phone": "9000000022",
            "password": "Farmer@123",
            "confirm_password": "Farmer@123",
        },
        follow_redirects=True,
    )
    client.post(
        "/farmer/login",
        data={
            "email": "farmer.twofarms@example.com",
            "password": "Farmer@123",
        },
        follow_redirects=True,
    )
    client.post(
        "/farmer/farm",
        data={
            "farm_name": "Farm C",
            "village": "Nashik",
            "taluka": "Nashik",
            "district": "Nashik",
            "state": "Maharashtra",
            "service_area": "Nashik",
        },
        follow_redirects=True,
    )
    first = client.post(
        "/farmer/cows/new",
        data={
            "cow_name": "Cross Farm One",
            "local_cow_number": "001",
            "breed": "Gir",
            "cow_type": "Dairy",
            "gender": "Female",
        },
        follow_redirects=True,
    )
    assert first.status_code == 200

    other_farm = client.post(
        "/farmer/farm",
        data={
            "farm_name": "Farm D",
            "village": "Pune",
            "taluka": "Pune City",
            "district": "Pune",
            "state": "Maharashtra",
            "service_area": "Pune",
        },
        follow_redirects=True,
    )
    assert other_farm.status_code == 200

    second = client.post(
        "/farmer/cows/new",
        data={
            "cow_name": "Cross Farm Two",
            "local_cow_number": "001",
            "breed": "Sahiwal",
            "cow_type": "Dairy",
            "gender": "Female",
        },
        follow_redirects=True,
    )
    assert second.status_code == 200
    assert "Cross Farm Two" in second.get_data(as_text=True)
