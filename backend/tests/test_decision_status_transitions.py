EMAIL_OWNER = "owner@example.com"
EMAIL_MEMBER = "member@example.com"
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


def _create_decision(client) -> tuple[str, str, dict[str, str]]:
    owner_headers = _register_and_login(client, EMAIL_OWNER)
    member_headers = _register_and_login(client, EMAIL_MEMBER)
    workspace_id = client.post("/workspaces", json={"name": "Product Team"}, headers=owner_headers).json()[
        "id"
    ]
    client.post(
        f"/workspaces/{workspace_id}/members",
        json={"email": EMAIL_MEMBER, "role": "member"},
        headers=owner_headers,
    )
    decision_id = client.post(
        f"/workspaces/{workspace_id}/decisions",
        json={"title": "Test decision"},
        headers=member_headers,
    ).json()["id"]
    return workspace_id, decision_id, member_headers


def _set_status(client, workspace_id, decision_id, headers, status):
    return client.patch(
        f"/workspaces/{workspace_id}/decisions/{decision_id}",
        json={"status": status},
        headers=headers,
    )


def test_draft_can_move_to_active(client):
    workspace_id, decision_id, headers = _create_decision(client)

    response = _set_status(client, workspace_id, decision_id, headers, "active")

    assert response.status_code == 200
    assert response.json()["status"] == "active"


def test_draft_can_move_to_cancelled(client):
    workspace_id, decision_id, headers = _create_decision(client)

    response = _set_status(client, workspace_id, decision_id, headers, "cancelled")

    assert response.status_code == 200


def test_draft_cannot_jump_to_completed(client):
    workspace_id, decision_id, headers = _create_decision(client)

    response = _set_status(client, workspace_id, decision_id, headers, "completed")

    assert response.status_code == 400


def test_draft_cannot_jump_to_needs_revision(client):
    workspace_id, decision_id, headers = _create_decision(client)

    response = _set_status(client, workspace_id, decision_id, headers, "needs_revision")

    assert response.status_code == 400


def test_active_can_move_to_needs_revision(client):
    workspace_id, decision_id, headers = _create_decision(client)
    _set_status(client, workspace_id, decision_id, headers, "active")

    response = _set_status(client, workspace_id, decision_id, headers, "needs_revision")

    assert response.status_code == 200


def test_needs_revision_can_return_to_active(client):
    workspace_id, decision_id, headers = _create_decision(client)
    _set_status(client, workspace_id, decision_id, headers, "active")
    _set_status(client, workspace_id, decision_id, headers, "needs_revision")

    response = _set_status(client, workspace_id, decision_id, headers, "active")

    assert response.status_code == 200
    assert response.json()["status"] == "active"


def test_active_can_move_to_completed(client):
    workspace_id, decision_id, headers = _create_decision(client)
    _set_status(client, workspace_id, decision_id, headers, "active")

    response = _set_status(client, workspace_id, decision_id, headers, "completed")

    assert response.status_code == 200


def test_completed_is_terminal(client):
    workspace_id, decision_id, headers = _create_decision(client)
    _set_status(client, workspace_id, decision_id, headers, "active")
    _set_status(client, workspace_id, decision_id, headers, "completed")

    response = _set_status(client, workspace_id, decision_id, headers, "active")

    assert response.status_code == 400


def test_cancelled_is_terminal(client):
    workspace_id, decision_id, headers = _create_decision(client)
    _set_status(client, workspace_id, decision_id, headers, "cancelled")

    response = _set_status(client, workspace_id, decision_id, headers, "active")

    assert response.status_code == 400


def test_setting_the_same_status_again_is_a_noop(client):
    workspace_id, decision_id, headers = _create_decision(client)

    response = _set_status(client, workspace_id, decision_id, headers, "draft")

    assert response.status_code == 200
    assert response.json()["status"] == "draft"


def test_status_update_does_not_touch_title_or_tags(client):
    owner_headers = _register_and_login(client, EMAIL_OWNER)
    member_headers = _register_and_login(client, EMAIL_MEMBER)
    workspace_id = client.post("/workspaces", json={"name": "Team"}, headers=owner_headers).json()[
        "id"
    ]
    client.post(
        f"/workspaces/{workspace_id}/members",
        json={"email": EMAIL_MEMBER, "role": "member"},
        headers=owner_headers,
    )
    decision_id = client.post(
        f"/workspaces/{workspace_id}/decisions",
        json={"title": "Keep my title", "tags": ["keep-me"]},
        headers=member_headers,
    ).json()["id"]

    response = _set_status(client, workspace_id, decision_id, member_headers, "active")

    assert response.json()["title"] == "Keep my title"
    assert response.json()["tags"] == ["keep-me"]
