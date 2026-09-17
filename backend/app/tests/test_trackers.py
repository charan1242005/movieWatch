def _create_tracker(client, headers, **overrides):
    payload = {
        "movie_title": "Avatar",
        "city": "Visakhapatnam",
        "date": "2026-09-25",
        "platform": "mock",
        "cinema": "Any Cinema",
        "language": "English",
        "format": "IMAX",
        "start_time": "18:00",
        "end_time": "22:00",
        "seats_required": 2,
        "adjacent_seats": False,
        "check_interval": 1,
    }
    payload.update(overrides)
    return client.post("/api/trackers", json=payload, headers=headers)


def test_create_list_tracker(client, auth_headers):
    resp = _create_tracker(client, auth_headers)
    assert resp.status_code == 201
    tracker = resp.json()
    assert tracker["status"] == "stopped"
    assert tracker["movie_title"] == "Avatar"

    resp = client.get("/api/trackers", headers=auth_headers)
    assert resp.status_code == 200
    assert len(resp.json()) == 1


def test_start_and_stop_tracker(client, auth_headers):
    tracker = _create_tracker(client, auth_headers).json()
    tid = tracker["id"]

    resp = client.post(f"/api/trackers/{tid}/start", headers=auth_headers)
    assert resp.status_code == 200
    assert resp.json()["status"] == "active"

    resp = client.post(f"/api/trackers/{tid}/stop", headers=auth_headers)
    assert resp.status_code == 200
    assert resp.json()["status"] == "stopped"


def test_delete_tracker(client, auth_headers):
    tracker = _create_tracker(client, auth_headers).json()
    tid = tracker["id"]
    resp = client.delete(f"/api/trackers/{tid}", headers=auth_headers)
    assert resp.status_code == 204
    resp = client.get(f"/api/trackers/{tid}", headers=auth_headers)
    assert resp.status_code == 404


def test_cannot_access_other_users_tracker(client, auth_headers):
    tracker = _create_tracker(client, auth_headers).json()
    tid = tracker["id"]

    client.post("/api/auth/register", json={"name": "Other", "email": "other@example.com", "password": "pass1234"})
    login = client.post("/api/auth/login", data={"username": "other@example.com", "password": "pass1234"})
    other_headers = {"Authorization": f"Bearer {login.json()['access_token']}"}

    resp = client.get(f"/api/trackers/{tid}", headers=other_headers)
    assert resp.status_code == 404
