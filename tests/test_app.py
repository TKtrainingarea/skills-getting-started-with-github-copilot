import pytest
from fastapi.testclient import TestClient

from src import app as app_module


@pytest.fixture
def activities(monkeypatch):
    test_activities = {
        "Chess Club": {
            "description": "Play chess",
            "schedule": "Fridays",
            "max_participants": 2,
            "participants": ["existing@example.com"],
        },
        "Full Club": {
            "description": "A full activity",
            "schedule": "Mondays",
            "max_participants": 1,
            "participants": ["existing@example.com"],
        },
    }
    monkeypatch.setattr(app_module, "activities", test_activities)
    return test_activities


@pytest.fixture
def client(activities):
    return TestClient(app_module.app, follow_redirects=False)


def test_root_redirects_to_static_index(client):
    response = client.get("/")

    assert response.status_code == 307
    assert response.headers["location"] == "/static/index.html"


def test_get_activities_returns_activity_data(client, activities):
    response = client.get("/activities")

    assert response.status_code == 200
    assert response.json() == activities


def test_signup_adds_participant(client, activities):
    response = client.post(
        "/activities/Chess Club/signup",
        params={"email": "new@example.com"},
    )

    assert response.status_code == 200
    assert response.json() == {
        "message": "Signed up new@example.com for Chess Club"
    }
    assert "new@example.com" in activities["Chess Club"]["participants"]


@pytest.mark.parametrize(
    ("activity_name", "email", "expected_status", "expected_detail"),
    [
        ("Unknown Club", "new@example.com", 404, "Activity not found"),
        ("Chess Club", "invalid-email", 400, "Valid email is required"),
        (
            "Chess Club",
            "existing@example.com",
            400,
            "Student already signed up for this activity",
        ),
        ("Full Club", "new@example.com", 400, "Activity is already full"),
    ],
)
def test_signup_rejects_invalid_requests(
    client, activity_name, email, expected_status, expected_detail
):
    response = client.post(
        f"/activities/{activity_name}/signup",
        params={"email": email},
    )

    assert response.status_code == expected_status
    assert response.json() == {"detail": expected_detail}


def test_unregister_removes_participant(client, activities):
    response = client.delete(
        "/activities/Chess Club/signup",
        params={"email": "existing@example.com"},
    )

    assert response.status_code == 200
    assert response.json() == {
        "message": "Removed existing@example.com from Chess Club"
    }
    assert "existing@example.com" not in activities["Chess Club"]["participants"]


@pytest.mark.parametrize(
    ("activity_name", "email", "expected_detail"),
    [
        ("Unknown Club", "student@example.com", "Activity not found"),
        (
            "Chess Club",
            "not-signed-up@example.com",
            "Student is not signed up for this activity",
        ),
    ],
)
def test_unregister_rejects_unknown_activity_or_participant(
    client, activity_name, email, expected_detail
):
    response = client.delete(
        f"/activities/{activity_name}/signup",
        params={"email": email},
    )

    assert response.status_code == 404
    assert response.json() == {"detail": expected_detail}
