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


def _workspace(client):
    owner_headers = _register_and_login(client, EMAIL_OWNER)
    member_headers = _register_and_login(client, EMAIL_MEMBER)
    viewer_headers = _register_and_login(client, EMAIL_VIEWER)
    workspace_id = client.post(
        "/workspaces", json={"name": "Product Team"}, headers=owner_headers
    ).json()["id"]
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


def _activity(client, workspace_id, headers):
    return client.get(f"/workspaces/{workspace_id}/activity", headers=headers)


def _exp_url(workspace_id, decision_id, experiment_id=None):
    base = f"/workspaces/{workspace_id}/decisions/{decision_id}/experiments"
    return base if experiment_id is None else f"{base}/{experiment_id}"


def _create_experiment(client, workspace_id, decision_id, headers, **overrides):
    payload = {
        "metric_name": "conversion",
        "metric_direction": "higher_is_better",
        "target_value": 100,
        "partial_tolerance_percent": 5,
    }
    payload.update(overrides)
    return client.post(
        _exp_url(workspace_id, decision_id), json=payload, headers=headers
    ).json()["id"]


# --- decisions ------------------------------------------------------------


def test_decision_created_logs_activity(client):
    workspace_id, _, member_headers, _ = _workspace(client)

    client.post(
        f"/workspaces/{workspace_id}/decisions",
        json={"title": "Onboarding revamp"},
        headers=member_headers,
    )

    entries = _activity(client, workspace_id, member_headers).json()
    assert len(entries) == 1
    assert entries[0]["action"] == "decision.created"
    assert entries[0]["entity_type"] == "decision"
    assert "Onboarding revamp" in entries[0]["summary"]


def test_decision_status_change_logs_old_and_new(client):
    workspace_id, _, member_headers, _ = _workspace(client)
    decision_id = client.post(
        f"/workspaces/{workspace_id}/decisions",
        json={"title": "Pricing test"},
        headers=member_headers,
    ).json()["id"]

    client.patch(
        f"/workspaces/{workspace_id}/decisions/{decision_id}",
        json={"status": "active"},
        headers=member_headers,
    )

    entries = _activity(client, workspace_id, member_headers).json()
    status_entries = [e for e in entries if e["action"] == "decision.status_changed"]
    assert len(status_entries) == 1
    assert "draft" in status_entries[0]["summary"]
    assert "active" in status_entries[0]["summary"]


def test_decision_noop_status_update_does_not_log(client):
    workspace_id, _, member_headers, _ = _workspace(client)
    decision_id = client.post(
        f"/workspaces/{workspace_id}/decisions",
        json={"title": "Steady state"},
        headers=member_headers,
    ).json()["id"]

    # тот же самый статус, что уже стоит — не событие
    client.patch(
        f"/workspaces/{workspace_id}/decisions/{decision_id}",
        json={"status": "draft"},
        headers=member_headers,
    )

    entries = _activity(client, workspace_id, member_headers).json()
    status_entries = [e for e in entries if e["action"] == "decision.status_changed"]
    assert status_entries == []


def test_decision_title_edit_alone_does_not_log(client):
    # скоуп первого среза: только created/status_changed, без diff по полям
    workspace_id, _, member_headers, _ = _workspace(client)
    decision_id = client.post(
        f"/workspaces/{workspace_id}/decisions",
        json={"title": "Original title"},
        headers=member_headers,
    ).json()["id"]

    client.patch(
        f"/workspaces/{workspace_id}/decisions/{decision_id}",
        json={"title": "Renamed"},
        headers=member_headers,
    )

    entries = _activity(client, workspace_id, member_headers).json()
    assert len(entries) == 1  # только decision.created, ничего про rename


# --- experiments ------------------------------------------------------------


def test_experiment_created_logs_activity(client):
    workspace_id, _, member_headers, _ = _workspace(client)
    decision_id = client.post(
        f"/workspaces/{workspace_id}/decisions",
        json={"title": "Pricing test"},
        headers=member_headers,
    ).json()["id"]
    client.patch(
        f"/workspaces/{workspace_id}/decisions/{decision_id}",
        json={"status": "active"},
        headers=member_headers,
    )

    _create_experiment(client, workspace_id, decision_id, member_headers)

    entries = _activity(client, workspace_id, member_headers).json()
    created = [e for e in entries if e["action"] == "experiment.created"]
    assert len(created) == 1
    assert created[0]["entity_type"] == "experiment"


def test_experiment_status_change_logs_verdict_on_completion(client):
    workspace_id, _, member_headers, _ = _workspace(client)
    decision_id = client.post(
        f"/workspaces/{workspace_id}/decisions",
        json={"title": "Pricing test"},
        headers=member_headers,
    ).json()["id"]
    client.patch(
        f"/workspaces/{workspace_id}/decisions/{decision_id}",
        json={"status": "active"},
        headers=member_headers,
    )
    experiment_id = _create_experiment(client, workspace_id, decision_id, member_headers)

    client.patch(
        _exp_url(workspace_id, decision_id, experiment_id),
        json={"status": "running"},
        headers=member_headers,
    )
    client.patch(
        _exp_url(workspace_id, decision_id, experiment_id),
        json={"status": "completed", "actual_value": 100},
        headers=member_headers,
    )

    entries = _activity(client, workspace_id, member_headers).json()
    status_entries = [e for e in entries if e["action"] == "experiment.status_changed"]
    assert len(status_entries) == 2  # planned->running, running->completed
    completed_entry = status_entries[0]  # самый свежий первым
    assert "completed" in completed_entry["summary"]
    assert "вердикт" in completed_entry["summary"]


# --- members ------------------------------------------------------------


def test_member_added_logs_activity(client):
    owner_headers = _register_and_login(client, EMAIL_OWNER)
    _register_and_login(client, EMAIL_MEMBER)
    workspace_id = client.post(
        "/workspaces", json={"name": "Team"}, headers=owner_headers
    ).json()["id"]

    client.post(
        f"/workspaces/{workspace_id}/members",
        json={"email": EMAIL_MEMBER, "role": "member"},
        headers=owner_headers,
    )

    entries = _activity(client, workspace_id, owner_headers).json()
    added = [e for e in entries if e["action"] == "member.added"]
    assert len(added) == 1
    assert added[0]["entity_type"] == "member"
    assert EMAIL_MEMBER in added[0]["summary"]


def test_member_removed_logs_activity(client):
    workspace_id, owner_headers, member_headers, _ = _workspace(client)
    members = client.get(
        f"/workspaces/{workspace_id}/members", headers=owner_headers
    ).json()
    target = next(m for m in members if m["email"] == EMAIL_MEMBER)

    client.delete(
        f"/workspaces/{workspace_id}/members/{target['id']}", headers=owner_headers
    )

    entries = _activity(client, workspace_id, owner_headers).json()
    removed = [e for e in entries if e["action"] == "member.removed"]
    assert len(removed) == 1
    assert EMAIL_MEMBER in removed[0]["summary"]


# --- access control & ordering ------------------------------------------


def test_viewer_can_list_activity(client):
    workspace_id, _, member_headers, viewer_headers = _workspace(client)
    client.post(
        f"/workspaces/{workspace_id}/decisions",
        json={"title": "Something"},
        headers=member_headers,
    )

    response = _activity(client, workspace_id, viewer_headers)

    assert response.status_code == 200
    assert len(response.json()) == 1


def test_stranger_cannot_list_activity(client):
    workspace_id, _, _, _ = _workspace(client)
    stranger_headers = _register_and_login(client, EMAIL_STRANGER)

    response = _activity(client, workspace_id, stranger_headers)

    assert response.status_code == 403


def test_activity_is_ordered_most_recent_first(client):
    workspace_id, _, member_headers, _ = _workspace(client)
    client.post(
        f"/workspaces/{workspace_id}/decisions",
        json={"title": "First"},
        headers=member_headers,
    )
    client.post(
        f"/workspaces/{workspace_id}/decisions",
        json={"title": "Second"},
        headers=member_headers,
    )

    entries = _activity(client, workspace_id, member_headers).json()

    assert "Second" in entries[0]["summary"]
    assert "First" in entries[1]["summary"]


def test_actor_email_is_included(client):
    workspace_id, _, member_headers, _ = _workspace(client)
    client.post(
        f"/workspaces/{workspace_id}/decisions",
        json={"title": "Something"},
        headers=member_headers,
    )

    entries = _activity(client, workspace_id, member_headers).json()

    assert entries[0]["actor_email"] == EMAIL_MEMBER
