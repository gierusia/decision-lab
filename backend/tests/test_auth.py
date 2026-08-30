EMAIL = "ada@example.com"
PASSWORD = "strongpass123"


def register(client, email=EMAIL, password=PASSWORD, full_name="Ada Lovelace"):
    return client.post(
        "/auth/register",
        json={"email": email, "password": password, "full_name": full_name},
    )


def login(client, email=EMAIL, password=PASSWORD):
    return client.post("/auth/login", json={"email": email, "password": password})


def auth_headers(client) -> dict[str, str]:
    register(client)
    token = login(client).json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def test_register_creates_user(client):
    response = register(client)

    assert response.status_code == 201
    body = response.json()
    assert body["email"] == EMAIL
    assert body["full_name"] == "Ada Lovelace"
    assert "password" not in body and "password_hash" not in body


def test_register_rejects_duplicate_email(client):
    register(client)
    response = register(client)

    assert response.status_code == 400


def test_register_rejects_short_password(client):
    response = register(client, password="short")

    # Валидация уровня Pydantic — до того, как запрос вообще дошёл до service
    assert response.status_code == 422


def test_login_returns_bearer_token(client):
    register(client)
    response = login(client)

    assert response.status_code == 200
    assert response.json()["token_type"] == "bearer"


def test_login_with_wrong_password_is_unauthorized(client):
    register(client)
    response = login(client, password="totally-wrong-password")

    assert response.status_code == 401


def test_me_rejects_missing_or_invalid_token(client):
    assert client.get("/auth/me").status_code == 401

    garbage_token = {"Authorization": "Bearer this-is-not-a-jwt"}
    assert client.get("/auth/me", headers=garbage_token).status_code == 401


def test_me_returns_current_user_for_valid_token(client):
    headers = auth_headers(client)
    response = client.get("/auth/me", headers=headers)

    assert response.status_code == 200
    assert response.json()["email"] == EMAIL


def test_profile_update_changes_name_and_password(client):
    headers = auth_headers(client)

    response = client.patch(
        "/auth/me",
        json={
            "full_name": "Ada King",
            "current_password": PASSWORD,
            "new_password": "an-even-stronger-pass",
        },
        headers=headers,
    )
    assert response.status_code == 200
    assert response.json()["full_name"] == "Ada King"

    # старый пароль больше не подходит, новый — подходит
    assert login(client, password=PASSWORD).status_code == 401
    assert login(client, password="an-even-stronger-pass").status_code == 200


def test_profile_update_rejects_wrong_current_password(client):
    headers = auth_headers(client)

    response = client.patch(
        "/auth/me",
        json={"current_password": "wrong-password", "new_password": "an-even-stronger-pass"},
        headers=headers,
    )

    assert response.status_code == 400
