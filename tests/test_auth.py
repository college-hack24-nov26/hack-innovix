def test_login_page(client):
    res = client.get("/login")
    assert res.status_code == 200
    assert b"Log in" in res.data or b"login" in res.data.lower()


def test_register_and_patient_role_blocked_from_doctor(client):
    res = client.post(
        "/register",
        data={
            "first_name": "Test",
            "last_name": "User",
            "email": "t@example.com",
            "password": "password1",
            "confirm": "password1",
            "age": "30",
            "gender": "other",
            "language": "en",
            "id_type": "new",
            "id_value": "",
        },
        follow_redirects=False,
    )
    assert res.status_code in (302, 200)
    blocked = client.get("/doctor/dashboard")
    assert blocked.status_code in (302, 403)
