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


def _create_workspace_with_member(client):
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
    return workspace_id, member_headers


def _create_decision_with_status(client, workspace_id, headers, title, status):
    decision_id = client.post(
        f"/workspaces/{workspace_id}/decisions", json={"title": title}, headers=headers
    ).json()["id"]
    if status == "active":
        client.patch(
            f"/workspaces/{workspace_id}/decisions/{decision_id}",
            json={"status": "active"},
            headers=headers,
        )
    elif status == "cancelled":
        client.patch(
            f"/workspaces/{workspace_id}/decisions/{decision_id}",
            json={"status": "cancelled"},
            headers=headers,
        )
    elif status in ("needs_revision", "completed"):
        # идём по графу переходов честно: draft -> active -> нужный статус
        client.patch(
            f"/workspaces/{workspace_id}/decisions/{decision_id}",
            json={"status": "active"},
            headers=headers,
        )
        client.patch(
            f"/workspaces/{workspace_id}/decisions/{decision_id}",
            json={"status": status},
            headers=headers,
        )
    return decision_id


def test_filter_by_status_returns_only_matching_decisions(client):
    workspace_id, headers = _create_workspace_with_member(client)
    _create_decision_with_status(client, workspace_id, headers, "Draft one", "draft")
    _create_decision_with_status(client, workspace_id, headers, "Active one", "active")
    _create_decision_with_status(client, workspace_id, headers, "Cancelled one", "cancelled")

    response = client.get(
        f"/workspaces/{workspace_id}/decisions", params={"status": "active"}, headers=headers
    )

    assert response.status_code == 200
    titles = [d["title"] for d in response.json()]
    assert titles == ["Active one"]


def test_filter_by_invalid_status_returns_422(client):
    workspace_id, headers = _create_workspace_with_member(client)

    response = client.get(
        f"/workspaces/{workspace_id}/decisions", params={"status": "bogus"}, headers=headers
    )

    assert response.status_code == 422


def test_status_filter_combines_with_q(client):
    workspace_id, headers = _create_workspace_with_member(client)
    _create_decision_with_status(client, workspace_id, headers, "Pricing draft", "draft")
    _create_decision_with_status(client, workspace_id, headers, "Pricing active", "active")
    _create_decision_with_status(client, workspace_id, headers, "Onboarding active", "active")

    response = client.get(
        f"/workspaces/{workspace_id}/decisions",
        params={"status": "active", "q": "pricing"},
        headers=headers,
    )

    titles = [d["title"] for d in response.json()]
    assert titles == ["Pricing active"]


def test_no_status_filter_returns_everything(client):
    workspace_id, headers = _create_workspace_with_member(client)
    _create_decision_with_status(client, workspace_id, headers, "One", "draft")
    _create_decision_with_status(client, workspace_id, headers, "Two", "active")

    response = client.get(f"/workspaces/{workspace_id}/decisions", headers=headers)

    assert len(response.json()) == 2
