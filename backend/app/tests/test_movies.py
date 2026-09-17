def test_search_movies(client):
    resp = client.get("/api/movies/search", params={"q": "avatar", "city": "Visakhapatnam"})
    assert resp.status_code == 200
    body = resp.json()
    assert len(body) == 1
    assert body[0]["title"].lower() == "avatar"


def test_search_movies_empty_query_returns_422(client):
    resp = client.get("/api/movies/search", params={"q": "", "city": "X"})
    assert resp.status_code == 422
