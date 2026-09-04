from datetime import datetime, timedelta, timezone

from app.decisions.models import Decision

EMAIL_OWNER = "owner@example.com"
EMAIL_MEMBER = "member@example.com"
EMAIL_MEMBER_TWO = "member2@example.com"
EMAIL_VIEWER = "viewer@example.com"
EMAIL_STRANGER = "stranger@example.com"
PASSWORD = "strongpass123"
NOW = datetime(2026, 9, 4, 12, 0, tzinfo=timezone.utc)


def _register_and_login(client, email, full_name="Test User"):
    client.post(
        "/auth/register",
        json={"email": email, "password": PASSWORD, "full_name": full_name},
    )
    token = client.post("/auth/login", json={"email": email, "password": PASSWORD}).json()[
        "access_token"
    ]
    return {"Authorization": f"Bearer {token}"}


def _workspace(client):
    owner = _register_and_login(client, EMAIL_OWNER, "Owner")
    member = _register_and_login(client, EMAIL_MEMBER, "Member One")
    member_two = _register_and_login(client, EMAIL_MEMBER_TWO, "Member Two")
    viewer = _register_and_login(client, EMAIL_VIEWER, "Viewer")
    workspace_id = client.post("/workspaces", json={"name": "Team"}, headers=owner).json()["id"]
    client.post(
        f"/workspaces/{workspace_id}/members",
        json={"email": EMAIL_MEMBER, "role": "member"},
        headers=owner,
    )
    client.post(
        f"/workspaces/{workspace_id}/members",
        json={"email": EMAIL_MEMBER_TWO, "role": "member"},
        headers=owner,
    )
    client.post(
        f"/workspaces/{workspace_id}/members",
        json={"email": EMAIL_VIEWER, "role": "viewer"},
        headers=owner,
    )
    return workspace_id, owner, member, member_two, viewer


def _create_active_decision(client, workspace_id, headers, title="Decision", tags=None):
    payload = {"title": title}
    if tags is not None:
        payload["tags"] = tags
    decision_id = client.post(
        f"/workspaces/{workspace_id}/decisions", json=payload, headers=headers
    ).json()["id"]
    client.patch(
        f"/workspaces/{workspace_id}/decisions/{decision_id}",
        json={"status": "active"},
        headers=headers,
    )
    return decision_id


def _set_updated_at(db_session, decision_id, value):
    decision = db_session.query(Decision).filter(Decision.id == decision_id).one()
    decision.updated_at = value
    db_session.commit()


def test_viewer_can_read_empty_dashboard(client):
    workspace_id, _, _, _, viewer = _workspace(client)

    response = client.get(f"/workspaces/{workspace_id}/dashboard", headers=viewer)

    assert response.status_code == 200
    body = response.json()
    assert body["totals"]["decisions"] == 0
    assert body["pagination"] == {"limit": 50, "offset": 0, "total": 0}
    assert set(body["totals"]["by_status"]) == {
        "draft",
        "active",
        "needs_revision",
        "completed",
        "cancelled",
    }


def test_stranger_cannot_read_dashboard(client):
    workspace_id, _, _, _, _ = _workspace(client)
    stranger = _register_and_login(client, EMAIL_STRANGER)

    response = client.get(f"/workspaces/{workspace_id}/dashboard", headers=stranger)

    assert response.status_code == 403


def test_missing_workspace_and_decision_are_404(client):
    _, owner, _, _, _ = _workspace(client)
    missing_ws = "11111111-1111-1111-1111-111111111111"
    missing_decision = "22222222-2222-2222-2222-222222222222"

    dashboard = client.get(f"/workspaces/{missing_ws}/dashboard", headers=owner)
    summary = client.get(
        f"/workspaces/{missing_ws}/decisions/{missing_decision}/summary",
        headers=owner,
    )

    assert dashboard.status_code == 404
    assert summary.status_code == 404


def test_dashboard_counts_and_author(client):
    workspace_id, _, member, member_two, viewer = _workspace(client)
    first = _create_active_decision(client, workspace_id, member, "Alpha", tags=["a"])
    _create_active_decision(client, workspace_id, member_two, "Beta")
    client.post(
        f"/workspaces/{workspace_id}/decisions/{first}/experiments",
        json={
            "metric_name": "conversion",
            "metric_direction": "higher_is_better",
            "target_value": 100,
            "partial_tolerance_percent": 5,
        },
        headers=member,
    )

    response = client.get(f"/workspaces/{workspace_id}/dashboard", headers=viewer)
    body = response.json()

    assert body["totals"]["decisions"] == 2
    assert body["totals"]["by_status"]["active"] == 2
    assert body["totals"]["experiments_open"] == 1
    assert body["totals"]["experiments_completed"] == 0
    alpha = next(item for item in body["decisions"] if item["title"] == "Alpha")
    assert alpha["author"]["full_name"] == "Member One"
    assert alpha["readiness"] == "blocked_by_open_experiments"
    assert alpha["experiment_counts"]["planned"] == 1
    assert alpha["tags"] == ["a"]


def test_filters_status_author_and_stale_only(client, db_session):
    workspace_id, owner, member, member_two, viewer = _workspace(client)
    stale_id = _create_active_decision(client, workspace_id, member, "Old active")
    completed_id = _create_active_decision(client, workspace_id, member_two, "Old completed")
    client.patch(
        f"/workspaces/{workspace_id}/decisions/{completed_id}",
        json={"status": "completed"},
        headers=owner,
    )
    _set_updated_at(db_session, stale_id, NOW - timedelta(days=30, seconds=1))
    _set_updated_at(db_session, completed_id, NOW - timedelta(days=365))

    by_author = client.get(
        f"/workspaces/{workspace_id}/dashboard",
        params={"author_id": client.get("/auth/me", headers=member).json()["id"]},
        headers=viewer,
    ).json()
    by_status = client.get(
        f"/workspaces/{workspace_id}/dashboard",
        params={"status": "completed"},
        headers=viewer,
    ).json()
    stale_only = client.get(
        f"/workspaces/{workspace_id}/dashboard",
        params={"stale_only": True},
        headers=viewer,
    ).json()
    stale_and_completed = client.get(
        f"/workspaces/{workspace_id}/dashboard",
        params={"stale_only": True, "status": "completed"},
        headers=viewer,
    ).json()

    assert by_author["totals"]["decisions"] == 1
    assert by_author["decisions"][0]["title"] == "Old active"
    assert by_status["totals"]["decisions"] == 1
    assert stale_only["totals"]["decisions"] == 1
    assert stale_only["decisions"][0]["is_stale"] is True
    assert stale_and_completed["totals"]["decisions"] == 0


def test_stale_boundary_via_summary(client, db_session):
    workspace_id, _, member, _, viewer = _workspace(client)
    decision_id = _create_active_decision(client, workspace_id, member, "Boundary")

    _set_updated_at(
        db_session,
        decision_id,
        datetime.now(timezone.utc) - timedelta(days=30) + timedelta(seconds=30),
    )
    on_threshold = client.get(
        f"/workspaces/{workspace_id}/decisions/{decision_id}/summary", headers=viewer
    ).json()
    _set_updated_at(
        db_session, decision_id, datetime.now(timezone.utc) - timedelta(days=30, seconds=2)
    )
    past_threshold = client.get(
        f"/workspaces/{workspace_id}/decisions/{decision_id}/summary", headers=viewer
    ).json()

    assert on_threshold["is_stale"] is False
    assert past_threshold["is_stale"] is True
    assert past_threshold["readiness"] == "ready_to_close"


def test_patch_title_clears_stale(client, db_session):
    workspace_id, _, member, _, viewer = _workspace(client)
    decision_id = _create_active_decision(client, workspace_id, member, "Stale one")
    _set_updated_at(
        db_session, decision_id, datetime.now(timezone.utc) - timedelta(days=40)
    )

    before = client.get(
        f"/workspaces/{workspace_id}/decisions/{decision_id}/summary", headers=viewer
    ).json()
    client.patch(
        f"/workspaces/{workspace_id}/decisions/{decision_id}",
        json={"title": "Touched"},
        headers=member,
    )
    after = client.get(
        f"/workspaces/{workspace_id}/decisions/{decision_id}/summary", headers=viewer
    ).json()

    assert before["is_stale"] is True
    assert after["is_stale"] is False
    assert after["title"] == "Touched"


def test_summary_readiness_and_verdicts(client):
    workspace_id, _, member, _, viewer = _workspace(client)
    decision_id = _create_active_decision(client, workspace_id, member, "Lab")
    url = f"/workspaces/{workspace_id}/decisions/{decision_id}/experiments"

    planned = client.post(
        url,
        json={
            "metric_name": "open",
            "metric_direction": "higher_is_better",
            "target_value": 10,
            "partial_tolerance_percent": 5,
        },
        headers=member,
    ).json()["id"]

    def _complete(name, actual, direction="higher_is_better", target=100, tolerance=5):
        exp_id = client.post(
            url,
            json={
                "metric_name": name,
                "metric_direction": direction,
                "target_value": target,
                "partial_tolerance_percent": tolerance,
            },
            headers=member,
        ).json()["id"]
        client.patch(f"{url}/{exp_id}", json={"status": "running", "actual_value": actual}, headers=member)
        client.patch(f"{url}/{exp_id}", json={"status": "completed"}, headers=member)

    _complete("win", 100)
    _complete("almost", 96)
    _complete("lose", 10)

    blocked = client.get(
        f"/workspaces/{workspace_id}/decisions/{decision_id}/summary", headers=viewer
    ).json()
    client.delete(f"{url}/{planned}", headers=member)
    ready = client.get(
        f"/workspaces/{workspace_id}/decisions/{decision_id}/summary", headers=viewer
    ).json()

    assert blocked["readiness"] == "blocked_by_open_experiments"
    assert len(blocked["experiments"]["open"]) == 1
    assert blocked["experiments"]["verdicts"] == {
        "success": 1,
        "partial": 1,
        "failed": 1,
    }
    assert ready["readiness"] == "ready_to_close"
    assert ready["experiments"]["open"] == []
    assert ready["experiments"]["total"] == 3


def test_summary_draft_and_closed(client):
    workspace_id, owner, member, _, viewer = _workspace(client)
    draft_id = client.post(
        f"/workspaces/{workspace_id}/decisions",
        json={"title": "Draft"},
        headers=member,
    ).json()["id"]
    closed_id = _create_active_decision(client, workspace_id, member, "Done")
    client.patch(
        f"/workspaces/{workspace_id}/decisions/{closed_id}",
        json={"status": "completed"},
        headers=owner,
    )

    draft = client.get(
        f"/workspaces/{workspace_id}/decisions/{draft_id}/summary", headers=viewer
    ).json()
    closed = client.get(
        f"/workspaces/{workspace_id}/decisions/{closed_id}/summary", headers=viewer
    ).json()

    assert draft["readiness"] == "draft"
    assert draft["experiments"]["total"] == 0
    assert closed["readiness"] == "closed"
    assert closed["is_stale"] is False
    assert closed["stale_after_at"] is None


def test_dashboard_pagination(client):
    workspace_id, _, member, _, viewer = _workspace(client)
    titles = ["One", "Two", "Three"]
    for title in titles:
        _create_active_decision(client, workspace_id, member, title)

    first = client.get(
        f"/workspaces/{workspace_id}/dashboard",
        params={"limit": 2, "offset": 0},
        headers=viewer,
    ).json()
    second = client.get(
        f"/workspaces/{workspace_id}/dashboard",
        params={"limit": 2, "offset": 2},
        headers=viewer,
    ).json()
    too_big = client.get(
        f"/workspaces/{workspace_id}/dashboard",
        params={"limit": 101},
        headers=viewer,
    )

    assert first["pagination"]["total"] == 3
    assert len(first["decisions"]) == 2
    assert len(second["decisions"]) == 1
    assert {item["title"] for item in first["decisions"]}.isdisjoint(
        {item["title"] for item in second["decisions"]}
    )
    assert first["totals"]["decisions"] == 3
    assert too_big.status_code == 422


def test_period_filter_uses_updated_at(client, db_session):
    workspace_id, _, member, _, viewer = _workspace(client)
    old_id = _create_active_decision(client, workspace_id, member, "Old")
    new_id = _create_active_decision(client, workspace_id, member, "New")
    _set_updated_at(db_session, old_id, datetime(2026, 1, 1, tzinfo=timezone.utc))
    _set_updated_at(db_session, new_id, datetime(2026, 8, 1, tzinfo=timezone.utc))

    body = client.get(
        f"/workspaces/{workspace_id}/dashboard",
        params={
            "date_from": "2026-07-01T00:00:00Z",
            "date_to": "2026-09-01T00:00:00Z",
        },
        headers=viewer,
    ).json()

    assert body["totals"]["decisions"] == 1
    assert body["decisions"][0]["title"] == "New"
    assert body["filters"]["date_from"] is not None
