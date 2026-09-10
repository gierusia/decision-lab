EMAIL_OWNER = "owner@example.com"
EMAIL_MEMBER = "member@example.com"
EMAIL_VIEWER = "viewer@example.com"
EMAIL_STRANGER = "stranger@example.com"
PASSWORD = "strongpass123"


def _register_and_login(client, email):
    client.post("/auth/register", json={"email": email, "password": PASSWORD, "full_name": "Test User"})
    token = client.post("/auth/login", json={"email": email, "password": PASSWORD}).json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def _workspace(client):
    owner = _register_and_login(client, EMAIL_OWNER)
    member = _register_and_login(client, EMAIL_MEMBER)
    viewer = _register_and_login(client, EMAIL_VIEWER)
    workspace_id = client.post("/workspaces", json={"name": "Team"}, headers=owner).json()["id"]
    client.post(
        f"/workspaces/{workspace_id}/members",
        json={"email": EMAIL_MEMBER, "role": "member"},
        headers=owner,
    )
    client.post(
        f"/workspaces/{workspace_id}/members",
        json={"email": EMAIL_VIEWER, "role": "viewer"},
        headers=owner,
    )
    return workspace_id, owner, member, viewer


def _row(rows, email):
    return next(item for item in rows if item["email"] == email)


def test_viewer_can_read_contribution(client):
    workspace_id, _, _, viewer = _workspace(client)
    response = client.get(f"/workspaces/{workspace_id}/contribution", headers=viewer)
    assert response.status_code == 200
    emails = {item["email"] for item in response.json()}
    assert emails == {EMAIL_OWNER, EMAIL_MEMBER, EMAIL_VIEWER}


def test_stranger_cannot_read_contribution(client):
    workspace_id, _, _, _ = _workspace(client)
    stranger = _register_and_login(client, EMAIL_STRANGER)
    response = client.get(f"/workspaces/{workspace_id}/contribution", headers=stranger)
    assert response.status_code == 403


def test_created_objects_and_verdicts_count_for_author(client):
    workspace_id, _, member, viewer = _workspace(client)
    decision_id = client.post(
        f"/workspaces/{workspace_id}/decisions",
        json={"title": "Lab"},
        headers=member,
    ).json()["id"]
    client.patch(
        f"/workspaces/{workspace_id}/decisions/{decision_id}",
        json={"status": "active"},
        headers=member,
    )
    exp_url = f"/workspaces/{workspace_id}/decisions/{decision_id}/experiments"
    exp_id = client.post(
        exp_url,
        json={
            "metric_name": "win",
            "metric_direction": "higher_is_better",
            "target_value": 100,
            "partial_tolerance_percent": 5,
        },
        headers=member,
    ).json()["id"]
    client.patch(f"{exp_url}/{exp_id}", json={"status": "running", "actual_value": 100}, headers=member)
    client.patch(f"{exp_url}/{exp_id}", json={"status": "completed"}, headers=member)

    rows = client.get(f"/workspaces/{workspace_id}/contribution", headers=viewer).json()
    author = _row(rows, EMAIL_MEMBER)
    idle = _row(rows, EMAIL_VIEWER)

    assert author["decisions_created"] == 1
    assert author["experiments_created"] == 1
    assert author["verdicts"] == {"success": 1, "partial": 0, "failed": 0}
    assert author["status_changes"] >= 2
    assert author["experiments_completed"] == 1
    assert idle["decisions_created"] == 0
    assert idle["experiments_created"] == 0
    assert idle["status_changes"] == 0


def test_status_change_counts_actor_not_author(client):
    workspace_id, owner, member, viewer = _workspace(client)
    decision_id = client.post(
        f"/workspaces/{workspace_id}/decisions",
        json={"title": "Shared"},
        headers=member,
    ).json()["id"]
    client.patch(
        f"/workspaces/{workspace_id}/decisions/{decision_id}",
        json={"status": "active"},
        headers=owner,
    )

    rows = client.get(f"/workspaces/{workspace_id}/contribution", headers=viewer).json()
    author = _row(rows, EMAIL_MEMBER)
    actor = _row(rows, EMAIL_OWNER)

    assert author["decisions_created"] == 1
    assert actor["decisions_created"] == 0
    assert actor["status_changes"] >= 1
    assert author["status_changes"] == 0
