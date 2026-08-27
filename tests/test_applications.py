def sample_application(**overrides):
    payload = {
        "company": "Northstar Labs",
        "role": "Backend Engineer",
        "status": "applied",
        "location": "Toronto, ON",
        "next_action": "Follow up next week",
    }
    payload.update(overrides)
    return payload


def test_health(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}


def test_create_and_get_application(client):
    created = client.post("/api/applications", json=sample_application())
    assert created.status_code == 201
    application = created.json()
    assert application["company"] == "Northstar Labs"
    assert application["id"]

    fetched = client.get(f"/api/applications/{application['id']}")
    assert fetched.status_code == 200
    assert fetched.json()["role"] == "Backend Engineer"


def test_filter_and_search(client):
    client.post("/api/applications", json=sample_application())
    client.post(
        "/api/applications",
        json=sample_application(company="Maple Systems", role="QA Engineer", status="interview"),
    )

    filtered = client.get("/api/applications", params={"status": "interview"})
    assert [item["company"] for item in filtered.json()] == ["Maple Systems"]

    searched = client.get("/api/applications", params={"search": "north"})
    assert [item["role"] for item in searched.json()] == ["Backend Engineer"]


def test_update_and_delete_application(client):
    application_id = client.post("/api/applications", json=sample_application()).json()["id"]

    updated = client.patch(
        f"/api/applications/{application_id}",
        json={"status": "interview", "next_action": "Prepare system-design examples"},
    )
    assert updated.status_code == 200
    assert updated.json()["status"] == "interview"

    deleted = client.delete(f"/api/applications/{application_id}")
    assert deleted.status_code == 204
    assert client.get(f"/api/applications/{application_id}").status_code == 404


def test_analytics(client):
    client.post("/api/applications", json=sample_application(status="applied"))
    client.post("/api/applications", json=sample_application(company="Orbit", status="interview"))
    client.post("/api/applications", json=sample_application(company="Harbour", status="offer"))
    client.post("/api/applications", json=sample_application(company="Cedar", status="rejected"))

    data = client.get("/api/analytics").json()
    assert data["total"] == 4
    assert data["active"] == 3
    assert data["response_rate"] == 50.0
    assert data["by_status"]["offer"] == 1


def test_rejects_invalid_salary_range(client):
    response = client.post(
        "/api/applications", json=sample_application(salary_min=120_000, salary_max=80_000)
    )
    assert response.status_code == 422
