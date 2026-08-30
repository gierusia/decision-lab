EMAIL_OWNER = "owner@example.com"
EMAIL_OTHER = "other@example.com"
PASSWORD = "strongpass123"


def _register_and_login(client, email) -> dict[str, str]:
    client.post(
        "/auth/register",
        json={"email": email, "password": PASSWORD, "full_name": "Test User"},
    )
    token = client.post("/auth/login", json={"email": email, "password": PASSWORD}).json()[
        "access_token"
    ]
    return {"Authorization": f"Bearer {token}"}


def test_create_workspace_makes_creator_the_owner(client):
    headers = _register_and_login(client, EMAIL_OWNER)

    response = client.post("/workspaces", json={"name": "Product Team"}, headers=headers)

    assert response.status_code == 201
    body = response.json()
    assert body["name"] == "Product Team"
    assert body["stale_threshold_days"] == 30  # дефолт, если не передали явно


def test_create_workspace_accepts_custom_stale_threshold(client):
    headers = _register_and_login(client, EMAIL_OWNER)

    response = client.post(
        "/workspaces",
        json={"name": "Product Team", "stale_threshold_days": 14},
        headers=headers,
    )

    assert response.json()["stale_threshold_days"] == 14


def test_list_workspaces_returns_only_mine(client):
    owner_headers = _register_and_login(client, EMAIL_OWNER)
    other_headers = _register_and_login(client, EMAIL_OTHER)

    client.post("/workspaces", json={"name": "Owner's workspace"}, headers=owner_headers)
    client.post("/workspaces", json={"name": "Other's workspace"}, headers=other_headers)

    response = client.get("/workspaces", headers=owner_headers)

    names = [workspace["name"] for workspace in response.json()]
    assert names == ["Owner's workspace"]


def test_owner_can_update_settings(client):
    headers = _register_and_login(client, EMAIL_OWNER)
    workspace_id = client.post("/workspaces", json={"name": "Product Team"}, headers=headers).json()[
        "id"
    ]

    response = client.patch(
        f"/workspaces/{workspace_id}",
        json={"name": "Renamed Team", "stale_threshold_days": 7},
        headers=headers,
    )

    assert response.status_code == 200
    assert response.json()["name"] == "Renamed Team"
    assert response.json()["stale_threshold_days"] == 7


def test_non_owner_cannot_update_settings(client):
    owner_headers = _register_and_login(client, EMAIL_OWNER)
    other_headers = _register_and_login(client, EMAIL_OTHER)
    workspace_id = client.post(
        "/workspaces", json={"name": "Product Team"}, headers=owner_headers
    ).json()["id"]

    response = client.patch(
        f"/workspaces/{workspace_id}",
        json={"name": "Hijacked"},
        headers=other_headers,
    )

    assert response.status_code == 403


def test_non_member_cannot_view_workspace(client):
    owner_headers = _register_and_login(client, EMAIL_OWNER)
    other_headers = _register_and_login(client, EMAIL_OTHER)
    workspace_id = client.post(
        "/workspaces", json={"name": "Product Team"}, headers=owner_headers
    ).json()["id"]

    response = client.get(f"/workspaces/{workspace_id}", headers=other_headers)

    assert response.status_code == 403


def test_getting_nonexistent_workspace_returns_404(client):
    headers = _register_and_login(client, EMAIL_OWNER)

    response = client.get(
        "/workspaces/00000000-0000-0000-0000-000000000000", headers=headers
    )

    assert response.status_code == 404
