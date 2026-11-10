from urllib.parse import quote

from src import app as app_module

CHESS = "Chess Club"
CHESS_URL = f"/activities/{quote(CHESS)}/signup"


def test_get_activities_returns_all_activities_with_expected_fields(client):
    response = client.get("/activities")

    assert response.status_code == 200
    data = response.json()
    assert set(data) == set(app_module.activities)
    for details in data.values():
        assert {"description", "schedule", "max_participants", "participants"} <= set(details)
    assert data[CHESS]["participants"] == ["michael@mergington.edu", "daniel@mergington.edu"]


def test_root_redirects_to_static_index(client):
    response = client.get("/", follow_redirects=False)

    assert response.status_code in (302, 307)
    assert response.headers["location"] == "/static/index.html"


def test_signup_adds_student_to_activity(client):
    response = client.post(CHESS_URL, params={"email": "new@mergington.edu"})

    assert response.status_code == 200
    assert response.json() == {"message": f"Signed up new@mergington.edu for {CHESS}"}
    assert "new@mergington.edu" in app_module.activities[CHESS]["participants"]


def test_signup_unknown_activity_returns_404(client):
    response = client.post("/activities/Nope/signup", params={"email": "a@mergington.edu"})

    assert response.status_code == 404
    assert response.json() == {"detail": "Activity not found"}


def test_signup_duplicate_returns_400_and_does_not_change_list(client):
    before = list(app_module.activities[CHESS]["participants"])

    response = client.post(CHESS_URL, params={"email": "michael@mergington.edu"})

    assert response.status_code == 400
    assert response.json() == {"detail": "Student already signed up for this activity"}
    assert app_module.activities[CHESS]["participants"] == before


def test_signup_full_activity_returns_400(client):
    activity = app_module.activities[CHESS]
    activity["max_participants"] = len(activity["participants"])

    response = client.post(CHESS_URL, params={"email": "late@mergington.edu"})

    assert response.status_code == 400
    assert response.json() == {"detail": "Activity is full"}
    assert "late@mergington.edu" not in activity["participants"]


def test_unregister_removes_student(client):
    response = client.delete(CHESS_URL, params={"email": "michael@mergington.edu"})

    assert response.status_code == 200
    assert response.json() == {"message": f"Unregistered michael@mergington.edu from {CHESS}"}
    assert "michael@mergington.edu" not in app_module.activities[CHESS]["participants"]


def test_unregister_student_not_signed_up_returns_404(client):
    response = client.delete(CHESS_URL, params={"email": "stranger@mergington.edu"})

    assert response.status_code == 404
    assert response.json() == {"detail": "Student is not signed up for this activity"}


def test_unregister_unknown_activity_returns_404(client):
    response = client.delete("/activities/Nope/signup", params={"email": "a@mergington.edu"})

    assert response.status_code == 404
    assert response.json() == {"detail": "Activity not found"}


def test_signup_then_unregister_then_signup_again(client):
    email = "cycle@mergington.edu"

    assert client.post(CHESS_URL, params={"email": email}).status_code == 200
    assert email in client.get("/activities").json()[CHESS]["participants"]

    assert client.delete(CHESS_URL, params={"email": email}).status_code == 200
    assert email not in client.get("/activities").json()[CHESS]["participants"]

    assert client.post(CHESS_URL, params={"email": email}).status_code == 200
    assert email in client.get("/activities").json()[CHESS]["participants"]
