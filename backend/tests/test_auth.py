def test_user_registration(client):
    payload = {
        "email": "newuser@enterprise.com",
        "password": "Password123!",
        "full_name": "John Doe",
        "organization_name": "New Horizons Ltd"
    }
    response = client.post("/api/v1/auth/register", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["user"]["email"] == "newuser@enterprise.com"
    assert data["user"]["organization"]["name"] == "New Horizons Ltd"


def test_user_login(client):
    login_payload = {
        "email": "newuser@enterprise.com",
        "password": "Password123!"
    }
    response = client.post("/api/v1/auth/login", json=login_payload)
    assert response.status_code == 200
    data = response.json()
    assert data["token_type"] == "bearer"
    assert "access_token" in data


def test_invalid_login(client):
    login_payload = {
        "email": "newuser@enterprise.com",
        "password": "WrongPassword!"
    }
    response = client.post("/api/v1/auth/login", json=login_payload)
    assert response.status_code == 401
