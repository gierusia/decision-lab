EMAIL_OWNER = "owner@example.com"
EMAIL_MEMBER = "member@example.com"
EMAIL_MEMBER_TWO = "member2@example.com"
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
    member_two_headers = _register_and_login(client, EMAIL_MEMBER_TWO)
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
        json={"email": EMAIL_MEMBER_TWO, "role": "member"},
        headers=owner_headers,
    )
    client.post(
        f"/workspaces/{workspace_id}/members",
        json={"email": EMAIL_VIEWER, "role": "viewer"},
        headers=owner_headers,
    )
    return workspace_id, owner_headers, member_headers, member_two_headers, viewer_headers


def _active_decision(client, workspace_id, headers):
    decision_id = client.post(
        f"/workspaces/{workspace_id}/decisions",
        json={"title": "Pricing test"},
        headers=headers,
    ).json()["id"]
    client.patch(
        f"/workspaces/{workspace_id}/decisions/{decision_id}",
        json={"status": "active"},
        headers=headers,
    )
    return decision_id


def _exp_url(workspace_id, decision_id, experiment_id=None):
    base = f"/workspaces/{workspace_id}/decisions/{decision_id}/experiments"
    if experiment_id is None:
        return base
    return f"{base}/{experiment_id}"


def _create_payload(**overrides):
    payload = {
        "metric_name": "conversion",
        "metric_direction": "higher_is_better",
        "target_value": 100,
        "partial_tolerance_percent": 5,
    }
    payload.update(overrides)
    return payload


def test_cannot_create_experiment_on_draft(client):
    workspace_id, _, member_headers, _, _ = _workspace(client)
    decision_id = client.post(
        f"/workspaces/{workspace_id}/decisions",
        json={"title": "Still draft"},
        headers=member_headers,
    ).json()["id"]

    response = client.post(
        _exp_url(workspace_id, decision_id),
        json=_create_payload(),
        headers=member_headers,
    )

    assert response.status_code == 400


def test_member_creates_experiment_on_active(client):
    workspace_id, _, member_headers, _, _ = _workspace(client)
    decision_id = _active_decision(client, workspace_id, member_headers)

    response = client.post(
        _exp_url(workspace_id, decision_id),
        json=_create_payload(notes="first run", feature_flag_key="pricing_v2"),
        headers=member_headers,
    )

    assert response.status_code == 201
    body = response.json()
    assert body["status"] == "planned"
    assert body["verdict"] is None
    assert body["is_frozen"] is False
    assert body["feature_flag_key"] == "pricing_v2"
    assert float(body["partial_tolerance_percent"]) == 5


def test_tolerance_is_required(client):
    workspace_id, _, member_headers, _, _ = _workspace(client)
    decision_id = _active_decision(client, workspace_id, member_headers)
    payload = _create_payload()
    del payload["partial_tolerance_percent"]

    response = client.post(
        _exp_url(workspace_id, decision_id), json=payload, headers=member_headers
    )

    assert response.status_code == 422


def test_viewer_cannot_create_but_can_read(client):
    workspace_id, _, member_headers, _, viewer_headers = _workspace(client)
    decision_id = _active_decision(client, workspace_id, member_headers)
    created = client.post(
        _exp_url(workspace_id, decision_id),
        json=_create_payload(),
        headers=member_headers,
    ).json()

    forbidden = client.post(
        _exp_url(workspace_id, decision_id),
        json=_create_payload(),
        headers=viewer_headers,
    )
    listing = client.get(_exp_url(workspace_id, decision_id), headers=viewer_headers)
    one = client.get(
        _exp_url(workspace_id, decision_id, created["id"]), headers=viewer_headers
    )

    assert forbidden.status_code == 403
    assert listing.status_code == 200
    assert len(listing.json()) == 1
    assert one.status_code == 200


def test_stranger_cannot_see_experiments(client):
    workspace_id, _, member_headers, _, _ = _workspace(client)
    decision_id = _active_decision(client, workspace_id, member_headers)
    stranger = _register_and_login(client, EMAIL_STRANGER)

    response = client.get(_exp_url(workspace_id, decision_id), headers=stranger)

    assert response.status_code == 403


def test_planned_cannot_jump_to_completed(client):
    workspace_id, _, member_headers, _, _ = _workspace(client)
    decision_id = _active_decision(client, workspace_id, member_headers)
    experiment_id = client.post(
        _exp_url(workspace_id, decision_id),
        json=_create_payload(actual_value=100),
        headers=member_headers,
    ).json()["id"]

    response = client.patch(
        _exp_url(workspace_id, decision_id, experiment_id),
        json={"status": "completed"},
        headers=member_headers,
    )

    assert response.status_code == 400


def test_complete_without_actual_is_rejected(client):
    workspace_id, _, member_headers, _, _ = _workspace(client)
    decision_id = _active_decision(client, workspace_id, member_headers)
    experiment_id = client.post(
        _exp_url(workspace_id, decision_id),
        json=_create_payload(),
        headers=member_headers,
    ).json()["id"]
    client.patch(
        _exp_url(workspace_id, decision_id, experiment_id),
        json={"status": "running"},
        headers=member_headers,
    )

    response = client.patch(
        _exp_url(workspace_id, decision_id, experiment_id),
        json={"status": "completed"},
        headers=member_headers,
    )

    assert response.status_code == 400


def test_running_to_completed_computes_verdict_and_freezes(client):
    workspace_id, _, member_headers, _, _ = _workspace(client)
    decision_id = _active_decision(client, workspace_id, member_headers)
    experiment_id = client.post(
        _exp_url(workspace_id, decision_id),
        json=_create_payload(),
        headers=member_headers,
    ).json()["id"]
    client.patch(
        _exp_url(workspace_id, decision_id, experiment_id),
        json={"status": "running", "actual_value": 96},
        headers=member_headers,
    )

    response = client.patch(
        _exp_url(workspace_id, decision_id, experiment_id),
        json={"status": "completed"},
        headers=member_headers,
    )

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "completed"
    assert body["verdict"] == "partial"
    assert body["is_frozen"] is True


def test_frozen_blocks_metric_patch(client):
    workspace_id, _, member_headers, _, _ = _workspace(client)
    decision_id = _active_decision(client, workspace_id, member_headers)
    experiment_id = client.post(
        _exp_url(workspace_id, decision_id),
        json=_create_payload(),
        headers=member_headers,
    ).json()["id"]
    client.patch(
        _exp_url(workspace_id, decision_id, experiment_id),
        json={"status": "running", "actual_value": 100},
        headers=member_headers,
    )
    client.patch(
        _exp_url(workspace_id, decision_id, experiment_id),
        json={"status": "completed"},
        headers=member_headers,
    )

    response = client.patch(
        _exp_url(workspace_id, decision_id, experiment_id),
        json={"actual_value": 80},
        headers=member_headers,
    )

    assert response.status_code == 400


def test_member_cannot_unfreeze(client):
    workspace_id, _, member_headers, _, _ = _workspace(client)
    decision_id = _active_decision(client, workspace_id, member_headers)
    experiment_id = client.post(
        _exp_url(workspace_id, decision_id),
        json=_create_payload(),
        headers=member_headers,
    ).json()["id"]
    client.patch(
        _exp_url(workspace_id, decision_id, experiment_id),
        json={"status": "running", "actual_value": 100},
        headers=member_headers,
    )
    client.patch(
        _exp_url(workspace_id, decision_id, experiment_id),
        json={"status": "completed"},
        headers=member_headers,
    )

    response = client.patch(
        _exp_url(workspace_id, decision_id, experiment_id),
        json={"is_frozen": False},
        headers=member_headers,
    )

    assert response.status_code == 400


def test_owner_unfreeze_recalculates_on_patch(client):
    workspace_id, owner_headers, member_headers, _, _ = _workspace(client)
    decision_id = _active_decision(client, workspace_id, member_headers)
    experiment_id = client.post(
        _exp_url(workspace_id, decision_id),
        json=_create_payload(),
        headers=member_headers,
    ).json()["id"]
    client.patch(
        _exp_url(workspace_id, decision_id, experiment_id),
        json={"status": "running", "actual_value": 100},
        headers=member_headers,
    )
    client.patch(
        _exp_url(workspace_id, decision_id, experiment_id),
        json={"status": "completed"},
        headers=member_headers,
    )

    unfreeze = client.patch(
        _exp_url(workspace_id, decision_id, experiment_id),
        json={"is_frozen": False},
        headers=owner_headers,
    )
    recalc = client.patch(
        _exp_url(workspace_id, decision_id, experiment_id),
        json={"actual_value": 90},
        headers=member_headers,
    )

    assert unfreeze.status_code == 200
    assert unfreeze.json()["is_frozen"] is False
    assert recalc.status_code == 200
    assert recalc.json()["verdict"] == "failed"
    assert recalc.json()["status"] == "completed"


def test_member_can_patch_another_members_experiment_in_same_workspace(client):
    workspace_id, _, member_headers, member_two_headers, _ = _workspace(client)
    decision_id = _active_decision(client, workspace_id, member_headers)
    experiment_id = client.post(
        _exp_url(workspace_id, decision_id),
        json=_create_payload(),
        headers=member_headers,
    ).json()["id"]

    response = client.patch(
        _exp_url(workspace_id, decision_id, experiment_id),
        json={"notes": "touched by teammate"},
        headers=member_two_headers,
    )

    assert response.status_code == 200
    assert response.json()["notes"] == "touched by teammate"


def test_member_can_delete_own_but_not_foreign(client):
    workspace_id, _, member_headers, member_two_headers, _ = _workspace(client)
    decision_id = _active_decision(client, workspace_id, member_headers)
    own_id = client.post(
        _exp_url(workspace_id, decision_id),
        json=_create_payload(metric_name="own"),
        headers=member_headers,
    ).json()["id"]
    foreign_id = client.post(
        _exp_url(workspace_id, decision_id),
        json=_create_payload(metric_name="foreign"),
        headers=member_two_headers,
    ).json()["id"]

    forbidden = client.delete(
        _exp_url(workspace_id, decision_id, foreign_id), headers=member_headers
    )
    allowed = client.delete(
        _exp_url(workspace_id, decision_id, own_id), headers=member_headers
    )

    assert forbidden.status_code == 403
    assert allowed.status_code == 204


def test_owner_can_delete_any_experiment(client):
    workspace_id, owner_headers, member_headers, _, _ = _workspace(client)
    decision_id = _active_decision(client, workspace_id, member_headers)
    experiment_id = client.post(
        _exp_url(workspace_id, decision_id),
        json=_create_payload(),
        headers=member_headers,
    ).json()["id"]

    response = client.delete(
        _exp_url(workspace_id, decision_id, experiment_id), headers=owner_headers
    )

    assert response.status_code == 204


def test_member_cannot_complete_decision_with_open_experiments(client):
    workspace_id, _, member_headers, _, _ = _workspace(client)
    decision_id = _active_decision(client, workspace_id, member_headers)
    client.post(
        _exp_url(workspace_id, decision_id),
        json=_create_payload(),
        headers=member_headers,
    )

    response = client.patch(
        f"/workspaces/{workspace_id}/decisions/{decision_id}",
        json={"status": "completed"},
        headers=member_headers,
    )

    assert response.status_code == 400


def test_owner_can_complete_decision_with_open_experiments(client):
    workspace_id, owner_headers, member_headers, _, _ = _workspace(client)
    decision_id = _active_decision(client, workspace_id, member_headers)
    client.post(
        _exp_url(workspace_id, decision_id),
        json=_create_payload(),
        headers=member_headers,
    )

    response = client.patch(
        f"/workspaces/{workspace_id}/decisions/{decision_id}",
        json={"status": "completed"},
        headers=owner_headers,
    )

    assert response.status_code == 200
    assert response.json()["status"] == "completed"


def test_cannot_create_experiment_after_decision_completed(client):
    workspace_id, owner_headers, member_headers, _, _ = _workspace(client)
    decision_id = _active_decision(client, workspace_id, member_headers)
    client.patch(
        f"/workspaces/{workspace_id}/decisions/{decision_id}",
        json={"status": "completed"},
        headers=owner_headers,
    )

    response = client.post(
        _exp_url(workspace_id, decision_id),
        json=_create_payload(),
        headers=member_headers,
    )

    assert response.status_code == 400


def test_cannot_unfreeze_on_cancelled_decision(client):
    workspace_id, owner_headers, member_headers, _, _ = _workspace(client)
    decision_id = _active_decision(client, workspace_id, member_headers)
    experiment_id = client.post(
        _exp_url(workspace_id, decision_id),
        json=_create_payload(),
        headers=member_headers,
    ).json()["id"]
    client.patch(
        _exp_url(workspace_id, decision_id, experiment_id),
        json={"status": "running", "actual_value": 100},
        headers=member_headers,
    )
    client.patch(
        _exp_url(workspace_id, decision_id, experiment_id),
        json={"status": "completed"},
        headers=member_headers,
    )
    client.patch(
        f"/workspaces/{workspace_id}/decisions/{decision_id}",
        json={"status": "cancelled"},
        headers=owner_headers,
    )

    response = client.patch(
        _exp_url(workspace_id, decision_id, experiment_id),
        json={"is_frozen": False},
        headers=owner_headers,
    )

    assert response.status_code == 400
