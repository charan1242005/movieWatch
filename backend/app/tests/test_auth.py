def test_register_and_login(client):
    resp = client.post("/api/auth/register", json={
        "name": "Alice", "email": "alice@example.com", "password": "secret123"
    })
    assert resp.status_code == 201
    assert resp.json()["email"] == "alice@example.com"

    resp = client.post("/api/auth/login", data={"username": "alice@example.com", "password": "secret123"})
    assert resp.status_code == 200
    assert "access_token" in resp.json()


def test_login_wrong_password(client):
    client.post("/api/auth/register", json={"name": "Bob", "email": "bob@example.com", "password": "secret123"})
    resp = client.post("/api/auth/login", data={"username": "bob@example.com", "password": "wrong"})
    assert resp.status_code == 401


def test_protected_route_requires_auth(client):
    resp = client.get("/api/auth/me")
    assert resp.status_code == 401
