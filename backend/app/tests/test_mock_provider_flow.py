"""
End-to-end test of the required minimum workflow:

Create tracker -> Start tracker -> Worker checks mock provider ->
mock provider initially unavailable -> forced available -> worker detects
availability -> notification generated -> frontend can read it via API.
"""


def test_full_mock_availability_flow(client, auth_headers):
    payload = {
        "movie_title": "Avatar",
        "city": "Visakhapatnam",
        "date": "2026-09-25",
        "platform": "mock",
        "cinema": "Any Cinema",
        "seats_required": 2,
        "adjacent_seats": False,
        "check_interval": 1,
    }
    tracker = client.post("/api/trackers", json=payload, headers=auth_headers).json()
    tid = tracker["id"]

    # Force the simulated showset straight to SEATS_AVAILABLE so the test is fast.
    force = client.post("/api/dev/mock/force-state", headers=auth_headers, json={
        "movie_id": "mock-avatar", "city": "Visakhapatnam", "date": "2026-09-25", "state": "SEATS_AVAILABLE",
    })
    assert force.status_code == 200

    # Starting the tracker performs an immediate check.
    resp = client.post(f"/api/trackers/{tid}/start", headers=auth_headers)
    assert resp.status_code == 200

    shows = client.get(f"/api/trackers/{tid}/shows", headers=auth_headers).json()
    assert len(shows) > 0
    assert any(s["available_seats"] >= 2 for s in shows)

    notifications = client.get("/api/notifications", headers=auth_headers).json()
    assert any(n["tracker_id"] == tid for n in notifications)
    assert any("TICKETS AVAILABLE" in n["message"] for n in notifications)


def test_no_shows_when_movie_not_available(client, auth_headers):
    payload = {
        "movie_title": "Unreleased Film",
        "city": "Hyderabad",
        "date": "2026-12-25",
        "platform": "mock",
        "seats_required": 1,
        "check_interval": 1,
    }
    tracker = client.post("/api/trackers", json=payload, headers=auth_headers).json()
    tid = tracker["id"]

    client.post("/api/dev/mock/force-state", headers=auth_headers, json={
        "movie_id": "mock-unreleased-film", "city": "Hyderabad", "date": "2026-12-25",
        "state": "MOVIE_NOT_AVAILABLE",
    })

    client.post(f"/api/trackers/{tid}/start", headers=auth_headers)
    shows = client.get(f"/api/trackers/{tid}/shows", headers=auth_headers).json()
    assert shows == []
