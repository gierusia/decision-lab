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


def _create_workspace_with_member_and_viewer(client):
    owner_headers = _register_and_login(client, EMAIL_OWNER)
    member_headers = _register_and_login(client, EMAIL_MEMBER)
    viewer_headers = _register_and_login(client, EMAIL_VIEWER)
    workspace_id = client.post("/workspaces", json={"name": "Product Team"}, headers=owner_headers).json()[
        "id"
    ]
    client.post(
        f"/workspaces/{workspace_id}/members",
        json={"email": EMAIL_MEMBER, "role": "member"},
        headers=owner_headers,
    )
    client.post(
        f"/workspaces/{workspace_id}/members",
        json={"email": EMAIL_VIEWER, "role": "viewer"},
        headers=owner_headers,
    )
    return workspace_id, owner_headers, member_headers, viewer_headers


def test_member_can_create_decision(client):
    workspace_id, _, member_headers, _ = _create_workspace_with_member_and_viewer(client)

    response = client.post(
        f"/workspaces/{workspace_id}/decisions",
        json={"title": "Ship the new pricing page"},
        headers=member_headers,
    )

    assert response.status_code == 201
    body = response.json()
    assert body["title"] == "Ship the new pricing page"
    assert body["status"] == "draft"  # дефолт при создании


def test_viewer_cannot_create_decision(client):
    workspace_id, _, _, viewer_headers = _create_workspace_with_member_and_viewer(client)

    response = client.post(
        f"/workspaces/{workspace_id}/decisions",
        json={"title": "Should not be allowed"},
        headers=viewer_headers,
    )

    assert response.status_code == 403


def test_viewer_can_list_and_view_decisions(client):
    workspace_id, _, member_headers, viewer_headers = _create_workspace_with_member_and_viewer(
        client
    )
    client.post(
        f"/workspaces/{workspace_id}/decisions",
        json={"title": "Onboarding revamp"},
        headers=member_headers,
    )

    list_response = client.get(f"/workspaces/{workspace_id}/decisions", headers=viewer_headers)
    assert list_response.status_code == 200
    assert len(list_response.json()) == 1

    decision_id = list_response.json()[0]["id"]
    get_response = client.get(
        f"/workspaces/{workspace_id}/decisions/{decision_id}", headers=viewer_headers
    )
    assert get_response.status_code == 200


def test_stranger_cannot_access_decisions(client):
    workspace_id, _, member_headers, _ = _create_workspace_with_member_and_viewer(client)
    stranger_headers = _register_and_login(client, EMAIL_STRANGER)
    client.post(
        f"/workspaces/{workspace_id}/decisions",
        json={"title": "Private decision"},
        headers=member_headers,
    )

    response = client.get(f"/workspaces/{workspace_id}/decisions", headers=stranger_headers)

    assert response.status_code == 403


def test_created_by_records_the_actual_creator(client):
    workspace_id, owner_headers, member_headers, _ = _create_workspace_with_member_and_viewer(
        client
    )
    me = client.get("/auth/me", headers=member_headers).json()

    decision = client.post(
        f"/workspaces/{workspace_id}/decisions",
        json={"title": "New recommendation algorithm"},
        headers=member_headers,
    ).json()

    assert decision["created_by"] == me["id"]


def test_member_can_update_title_and_status(client):
    workspace_id, _, member_headers, _ = _create_workspace_with_member_and_viewer(client)
    decision_id = client.post(
        f"/workspaces/{workspace_id}/decisions",
        json={"title": "Draft decision"},
        headers=member_headers,
    ).json()["id"]

    response = client.patch(
        f"/workspaces/{workspace_id}/decisions/{decision_id}",
        json={"title": "Renamed decision", "status": "active"},
        headers=member_headers,
    )

    assert response.status_code == 200
    assert response.json()["title"] == "Renamed decision"
    assert response.json()["status"] == "active"


def test_viewer_cannot_update_decision(client):
    workspace_id, _, member_headers, viewer_headers = _create_workspace_with_member_and_viewer(
        client
    )
    decision_id = client.post(
        f"/workspaces/{workspace_id}/decisions",
        json={"title": "Draft decision"},
        headers=member_headers,
    ).json()["id"]

    response = client.patch(
        f"/workspaces/{workspace_id}/decisions/{decision_id}",
        json={"title": "Hijacked"},
        headers=viewer_headers,
    )

    assert response.status_code == 403


def test_owner_can_delete_decision(client):
    workspace_id, owner_headers, member_headers, _ = _create_workspace_with_member_and_viewer(
        client
    )
    decision_id = client.post(
        f"/workspaces/{workspace_id}/decisions",
        json={"title": "To be removed"},
        headers=member_headers,
    ).json()["id"]

    delete_response = client.delete(
        f"/workspaces/{workspace_id}/decisions/{decision_id}", headers=owner_headers
    )
    assert delete_response.status_code == 204

    get_response = client.get(
        f"/workspaces/{workspace_id}/decisions/{decision_id}", headers=owner_headers
    )
    assert get_response.status_code == 404


def test_member_cannot_delete_decision(client):
    # Создавать и менять статус (в т.ч. на cancelled) Member может через
    # PATCH — но стереть решение из workspace целиком нельзя, только Owner.
    workspace_id, _, member_headers, _ = _create_workspace_with_member_and_viewer(client)
    decision_id = client.post(
        f"/workspaces/{workspace_id}/decisions",
        json={"title": "Should survive"},
        headers=member_headers,
    ).json()["id"]

    response = client.delete(
        f"/workspaces/{workspace_id}/decisions/{decision_id}", headers=member_headers
    )
    assert response.status_code == 403

    # решение осталось на месте
    get_response = client.get(
        f"/workspaces/{workspace_id}/decisions/{decision_id}", headers=member_headers
    )
    assert get_response.status_code == 200


def test_getting_nonexistent_decision_returns_404(client):
    workspace_id, _, member_headers, _ = _create_workspace_with_member_and_viewer(client)

    response = client.get(
        f"/workspaces/{workspace_id}/decisions/00000000-0000-0000-0000-000000000000",
        headers=member_headers,
    )

    assert response.status_code == 404


def test_decision_is_not_visible_from_a_different_workspace(client):
    workspace_id, owner_headers, member_headers, _ = _create_workspace_with_member_and_viewer(
        client
    )
    decision_id = client.post(
        f"/workspaces/{workspace_id}/decisions",
        json={"title": "Belongs to first workspace"},
        headers=member_headers,
    ).json()["id"]

    other_workspace_id = client.post(
        "/workspaces", json={"name": "Second Workspace"}, headers=owner_headers
    ).json()["id"]

    # тот же decision_id, но в пути указан ДРУГОЙ workspace_id
    response = client.get(
        f"/workspaces/{other_workspace_id}/decisions/{decision_id}", headers=owner_headers
    )

    assert response.status_code == 404
