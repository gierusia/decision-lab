EMAIL_OWNER = "owner@example.com"
EMAIL_MEMBER = "member@example.com"
EMAIL_VIEWER = "viewer@example.com"
EMAIL_STRANGER = "stranger@example.com"
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


def _create_workspace(client, headers) -> str:
    return client.post("/workspaces", json={"name": "Product Team"}, headers=headers).json()["id"]


def test_owner_can_add_member(client):
    owner_headers = _register_and_login(client, EMAIL_OWNER)
    _register_and_login(client, EMAIL_MEMBER)  # получатель приглашения должен уже существовать
    workspace_id = _create_workspace(client, owner_headers)

    response = client.post(
        f"/workspaces/{workspace_id}/members",
        json={"email": EMAIL_MEMBER, "role": "member"},
        headers=owner_headers,
    )

    assert response.status_code == 201
    assert response.json()["role"] == "member"
    assert response.json()["email"] == EMAIL_MEMBER


def test_cannot_invite_someone_as_owner(client):
    owner_headers = _register_and_login(client, EMAIL_OWNER)
    _register_and_login(client, EMAIL_MEMBER)
    workspace_id = _create_workspace(client, owner_headers)

    response = client.post(
        f"/workspaces/{workspace_id}/members",
        json={"email": EMAIL_MEMBER, "role": "owner"},
        headers=owner_headers,
    )

    assert response.status_code == 422  # схема режет это ещё до бизнес-логики


def test_cannot_invite_unregistered_email(client):
    owner_headers = _register_and_login(client, EMAIL_OWNER)
    workspace_id = _create_workspace(client, owner_headers)

    response = client.post(
        f"/workspaces/{workspace_id}/members",
        json={"email": "nobody@example.com", "role": "member"},
        headers=owner_headers,
    )

    assert response.status_code == 400


def test_cannot_invite_same_person_twice(client):
    owner_headers = _register_and_login(client, EMAIL_OWNER)
    _register_and_login(client, EMAIL_MEMBER)
    workspace_id = _create_workspace(client, owner_headers)

    client.post(
        f"/workspaces/{workspace_id}/members",
        json={"email": EMAIL_MEMBER, "role": "member"},
        headers=owner_headers,
    )
    response = client.post(
        f"/workspaces/{workspace_id}/members",
        json={"email": EMAIL_MEMBER, "role": "viewer"},
        headers=owner_headers,
    )

    assert response.status_code == 400


def test_non_owner_cannot_add_member(client):
    owner_headers = _register_and_login(client, EMAIL_OWNER)
    member_headers = _register_and_login(client, EMAIL_MEMBER)
    _register_and_login(client, EMAIL_VIEWER)
    workspace_id = _create_workspace(client, owner_headers)
    client.post(
        f"/workspaces/{workspace_id}/members",
        json={"email": EMAIL_MEMBER, "role": "member"},
        headers=owner_headers,
    )

    # у member роль есть, но она недостаточно высокая, чтобы приглашать
    response = client.post(
        f"/workspaces/{workspace_id}/members",
        json={"email": EMAIL_VIEWER, "role": "viewer"},
        headers=member_headers,
    )

    assert response.status_code == 403


def test_viewer_can_list_members_but_not_change_settings(client):
    owner_headers = _register_and_login(client, EMAIL_OWNER)
    viewer_headers = _register_and_login(client, EMAIL_VIEWER)
    workspace_id = _create_workspace(client, owner_headers)
    client.post(
        f"/workspaces/{workspace_id}/members",
        json={"email": EMAIL_VIEWER, "role": "viewer"},
        headers=owner_headers,
    )

    list_response = client.get(f"/workspaces/{workspace_id}/members", headers=viewer_headers)
    assert list_response.status_code == 200
    assert len(list_response.json()) == 2  # owner + viewer

    settings_response = client.patch(
        f"/workspaces/{workspace_id}", json={"name": "Hijacked"}, headers=viewer_headers
    )
    assert settings_response.status_code == 403


def test_stranger_cannot_list_members(client):
    owner_headers = _register_and_login(client, EMAIL_OWNER)
    stranger_headers = _register_and_login(client, EMAIL_STRANGER)
    workspace_id = _create_workspace(client, owner_headers)

    response = client.get(f"/workspaces/{workspace_id}/members", headers=stranger_headers)

    assert response.status_code == 403


def test_owner_can_change_member_role(client):
    owner_headers = _register_and_login(client, EMAIL_OWNER)
    _register_and_login(client, EMAIL_MEMBER)
    workspace_id = _create_workspace(client, owner_headers)
    member_id = client.post(
        f"/workspaces/{workspace_id}/members",
        json={"email": EMAIL_MEMBER, "role": "viewer"},
        headers=owner_headers,
    ).json()["id"]

    response = client.patch(
        f"/workspaces/{workspace_id}/members/{member_id}",
        json={"role": "member"},
        headers=owner_headers,
    )

    assert response.status_code == 200
    assert response.json()["role"] == "member"


def test_owner_role_cannot_be_changed_through_member_endpoint(client):
    owner_headers = _register_and_login(client, EMAIL_OWNER)
    workspace_id = _create_workspace(client, owner_headers)
    owner_member_id = client.get(
        f"/workspaces/{workspace_id}/members", headers=owner_headers
    ).json()[0]["id"]

    response = client.patch(
        f"/workspaces/{workspace_id}/members/{owner_member_id}",
        json={"role": "member"},
        headers=owner_headers,
    )

    assert response.status_code == 400


def test_owner_can_remove_member(client):
    owner_headers = _register_and_login(client, EMAIL_OWNER)
    _register_and_login(client, EMAIL_MEMBER)
    workspace_id = _create_workspace(client, owner_headers)
    member_id = client.post(
        f"/workspaces/{workspace_id}/members",
        json={"email": EMAIL_MEMBER, "role": "member"},
        headers=owner_headers,
    ).json()["id"]

    response = client.delete(
        f"/workspaces/{workspace_id}/members/{member_id}", headers=owner_headers
    )
    assert response.status_code == 204

    remaining = client.get(f"/workspaces/{workspace_id}/members", headers=owner_headers).json()
    assert len(remaining) == 1  # остался только owner
