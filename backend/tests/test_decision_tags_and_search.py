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


def test_create_decision_with_tags(client):
    workspace_id, member_headers = _create_workspace_with_member(client)

    response = client.post(
        f"/workspaces/{workspace_id}/decisions",
        json={"title": "New onboarding flow", "tags": ["onboarding", "growth"]},
        headers=member_headers,
    )

    assert response.status_code == 201
    assert sorted(response.json()["tags"]) == ["growth", "onboarding"]


def test_tags_are_deduplicated_and_trimmed(client):
    workspace_id, member_headers = _create_workspace_with_member(client)

    response = client.post(
        f"/workspaces/{workspace_id}/decisions",
        json={"title": "Pricing test", "tags": [" pricing ", "pricing", "", "  "]},
        headers=member_headers,
    )

    assert response.json()["tags"] == ["pricing"]


def test_search_by_q_matches_title_or_description(client):
    workspace_id, member_headers = _create_workspace_with_member(client)
    client.post(
        f"/workspaces/{workspace_id}/decisions",
        json={"title": "Recommendation algorithm v2"},
        headers=member_headers,
    )
    client.post(
        f"/workspaces/{workspace_id}/decisions",
        json={"title": "Something else", "description": "affects the recommendation engine"},
        headers=member_headers,
    )
    client.post(
        f"/workspaces/{workspace_id}/decisions",
        json={"title": "Unrelated decision"},
        headers=member_headers,
    )

    response = client.get(
        f"/workspaces/{workspace_id}/decisions", params={"q": "recommendation"}, headers=member_headers
    )

    assert response.status_code == 200
    assert len(response.json()) == 2


def test_search_by_q_is_case_insensitive(client):
    workspace_id, member_headers = _create_workspace_with_member(client)
    client.post(
        f"/workspaces/{workspace_id}/decisions",
        json={"title": "Onboarding Revamp"},
        headers=member_headers,
    )

    response = client.get(
        f"/workspaces/{workspace_id}/decisions", params={"q": "ONBOARDING"}, headers=member_headers
    )

    assert len(response.json()) == 1


def test_filter_by_tag_returns_only_matching_decisions(client):
    workspace_id, member_headers = _create_workspace_with_member(client)
    client.post(
        f"/workspaces/{workspace_id}/decisions",
        json={"title": "Decision A", "tags": ["growth"]},
        headers=member_headers,
    )
    client.post(
        f"/workspaces/{workspace_id}/decisions",
        json={"title": "Decision B", "tags": ["retention"]},
        headers=member_headers,
    )

    response = client.get(
        f"/workspaces/{workspace_id}/decisions", params={"tag": "growth"}, headers=member_headers
    )

    assert len(response.json()) == 1
    assert response.json()[0]["title"] == "Decision A"


def test_update_replaces_tags_entirely(client):
    workspace_id, member_headers = _create_workspace_with_member(client)
    decision_id = client.post(
        f"/workspaces/{workspace_id}/decisions",
        json={"title": "Decision", "tags": ["old-tag"]},
        headers=member_headers,
    ).json()["id"]

    response = client.patch(
        f"/workspaces/{workspace_id}/decisions/{decision_id}",
        json={"tags": ["new-tag"]},
        headers=member_headers,
    )

    assert response.json()["tags"] == ["new-tag"]


def test_update_without_tags_field_leaves_tags_untouched(client):
    workspace_id, member_headers = _create_workspace_with_member(client)
    decision_id = client.post(
        f"/workspaces/{workspace_id}/decisions",
        json={"title": "Decision", "tags": ["keep-me"]},
        headers=member_headers,
    ).json()["id"]

    response = client.patch(
        f"/workspaces/{workspace_id}/decisions/{decision_id}",
        json={"title": "Renamed"},
        headers=member_headers,
    )

    assert response.json()["tags"] == ["keep-me"]


def test_update_with_empty_tags_list_clears_all_tags(client):
    workspace_id, member_headers = _create_workspace_with_member(client)
    decision_id = client.post(
        f"/workspaces/{workspace_id}/decisions",
        json={"title": "Decision", "tags": ["a", "b"]},
        headers=member_headers,
    ).json()["id"]

    response = client.patch(
        f"/workspaces/{workspace_id}/decisions/{decision_id}",
        json={"tags": []},
        headers=member_headers,
    )

    assert response.json()["tags"] == []
