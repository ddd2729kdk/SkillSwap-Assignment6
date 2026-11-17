from datetime import datetime, timedelta, timezone


def future(days=5, hours=0):
    return (datetime.now(timezone.utc) + timedelta(days=days, hours=hours)).isoformat()


def make_user(client, n=1, **overrides):
    payload = {
        "full_name": f"Student Number{n}",
        "email": f"student{n}@uni.kz",
        "university": "Test University",
        "major": "Computer Science",
        "year_of_study": 2,
    }
    payload.update(overrides)
    response = client.post("/users", json=payload)
    assert response.status_code == 201, response.text
    return response.json()


def make_skill(client, name="Python", category="programming"):
    response = client.post("/skills", json={"name": name, "category": category})
    assert response.status_code == 201, response.text
    return response.json()


def add_skill(client, user_id, skill_id, kind, level="intermediate"):
    response = client.post(
        f"/users/{user_id}/skills",
        json={"skill_id": skill_id, "kind": kind, "level": level},
    )
    assert response.status_code == 201, response.text
    return response.json()


def setup_pair(client):
    a = make_user(client, 1)
    b = make_user(client, 2)
    python = make_skill(client, "Python")
    english = make_skill(client, "English", "languages")
    add_skill(client, a["id"], python["id"], "offer")
    add_skill(client, a["id"], english["id"], "want")
    add_skill(client, b["id"], english["id"], "offer")
    add_skill(client, b["id"], python["id"], "want")
    return a, b, python, english


def make_swap(client, a, b, python, english, **overrides):
    payload = {
        "requester_id": a["id"],
        "partner_id": b["id"],
        "skill_id": english["id"],
        "offered_skill_id": python["id"],
        "scheduled_at": future(),
        "duration_minutes": 60,
    }
    payload.update(overrides)
    return client.post("/swaps", json=payload)


def test_health(client):
    assert client.get("/").json()["status"] == "ok"


def test_user_crud_and_validation(client):
    user = make_user(client)
    assert client.get(f"/users/{user['id']}").status_code == 200
    assert client.get("/users/999").status_code == 404
    assert client.post("/users", json={"full_name": "A"}).status_code == 422
    bad_email = {**user, "email": "not-an-email"}
    assert client.post("/users", json=bad_email).status_code == 422
    assert client.post("/users", json={**user, "year_of_study": 9}).status_code == 422
    assert client.post("/users", json={**user, "id": None}).status_code == 409
    patched = client.patch(f"/users/{user['id']}", json={"major": "Math"})
    assert patched.status_code == 200 and patched.json()["major"] == "Math"
    assert client.patch(f"/users/{user['id']}", json={}).status_code == 400
    other = make_user(client, 2)
    conflict = client.patch(f"/users/{other['id']}", json={"email": user["email"]})
    assert conflict.status_code == 409
    assert client.delete(f"/users/{user['id']}").status_code == 204
    assert client.get(f"/users/{user['id']}").status_code == 404


def test_user_filters(client):
    make_user(client, 1, university="Alpha Uni")
    make_user(client, 2, university="Beta Uni")
    assert len(client.get("/users", params={"university": "alpha"}).json()) == 1
    assert len(client.get("/users", params={"limit": 1}).json()) == 1
    assert client.get("/users", params={"limit": 0}).status_code == 422


def test_skill_crud(client):
    skill = make_skill(client)
    assert client.post("/skills", json={"name": "python", "category": "programming"}).status_code == 409
    assert client.post("/skills", json={"name": "X", "category": "bad"}).status_code == 422
    assert client.get("/skills", params={"category": "programming"}).json()[0]["id"] == skill["id"]
    assert client.patch(f"/skills/{skill['id']}", json={"name": "Python 3"}).json()["name"] == "Python 3"
    assert client.get("/skills/99").status_code == 404
    assert client.delete(f"/skills/{skill['id']}").status_code == 204


def test_user_skills_rules(client):
    user = make_user(client)
    skill = make_skill(client)
    record = add_skill(client, user["id"], skill["id"], "offer")
    dup = client.post(f"/users/{user['id']}/skills", json={"skill_id": skill["id"], "kind": "want", "level": "beginner"})
    assert dup.status_code == 409
    missing = client.post(f"/users/{user['id']}/skills", json={"skill_id": 99, "kind": "want", "level": "beginner"})
    assert missing.status_code == 404
    assert client.post(f"/users/99/skills", json={"skill_id": 1, "kind": "want", "level": "beginner"}).status_code == 404
    upd = client.patch(f"/users/{user['id']}/skills/{record['id']}", json={"level": "advanced"})
    assert upd.json()["level"] == "advanced"
    assert client.delete(f"/skills/{skill['id']}").status_code == 409
    assert client.delete(f"/users/{user['id']}/skills/{record['id']}").status_code == 204
    assert client.get(f"/users/{user['id']}/skills").json() == []


def test_matching(client):
    a, b, python, english = setup_pair(client)
    c = make_user(client, 3)
    add_skill(client, c["id"], english["id"], "offer")
    matches = client.get(f"/users/{a['id']}/matches").json()
    assert [m["user"]["id"] for m in matches] == [b["id"], c["id"]]
    assert matches[0]["mutual"] is True
    assert matches[0]["can_teach_you"] == ["English"]
    assert matches[0]["wants_to_learn_from_you"] == ["Python"]
    assert matches[1]["mutual"] is False
    assert client.get(f"/users/{a['id']}/matches", params={"min_score": 1000}).json() == []
    assert client.get("/users/999/matches").status_code == 404
    teachers = client.get(f"/skills/{english['id']}/teachers").json()
    assert {t["id"] for t in teachers} == {b["id"], c["id"]}


def test_swap_creation_rules(client):
    a, b, python, english = setup_pair(client)
    assert make_swap(client, a, a, python, english).status_code == 400
    assert make_swap(client, a, b, python, english, skill_id=python["id"]).status_code == 400
    assert make_swap(client, a, b, python, english, offered_skill_id=english["id"]).status_code == 400
    assert make_swap(client, a, b, python, english, scheduled_at=future(-1)).status_code == 400
    assert make_swap(client, a, b, python, english, partner_id=999).status_code == 404
    assert make_swap(client, a, b, python, english, duration_minutes=5).status_code == 422
    assert make_swap(client, a, b, python, english, scheduled_at="garbage").status_code == 422
    ok = make_swap(client, a, b, python, english)
    assert ok.status_code == 201 and ok.json()["status"] == "pending"
    assert ok.json()["skill_name"] == "English"
    assert make_swap(client, a, b, python, english, scheduled_at=future(7)).status_code == 409


def test_swap_lifecycle_and_reviews(client):
    a, b, python, english = setup_pair(client)
    swap = make_swap(client, a, b, python, english).json()
    sid = swap["id"]
    review = {"swap_id": sid, "author_id": a["id"], "rating": 5}
    assert client.post("/reviews", json=review).status_code == 409
    forbidden = client.patch(f"/swaps/{sid}/status", json={"actor_id": a["id"], "status": "accepted"})
    assert forbidden.status_code == 403
    outsider = make_user(client, 3)
    assert client.patch(f"/swaps/{sid}/status", json={"actor_id": outsider["id"], "status": "cancelled"}).status_code == 403
    assert client.patch(f"/swaps/{sid}/status", json={"actor_id": b["id"], "status": "completed"}).status_code == 409
    assert client.patch(f"/swaps/{sid}/status", json={"actor_id": b["id"], "status": "pending"}).status_code == 422
    accepted = client.patch(f"/swaps/{sid}/status", json={"actor_id": b["id"], "status": "accepted"})
    assert accepted.status_code == 200 and accepted.json()["status"] == "accepted"
    assert client.patch(f"/swaps/{sid}", json={"actor_id": a["id"], "message": "hi"}).status_code == 409
    assert client.delete(f"/swaps/{sid}", params={"actor_id": a["id"]}).status_code == 409
    assert client.delete(f"/users/{a['id']}").status_code == 409
    done = client.patch(f"/swaps/{sid}/status", json={"actor_id": a["id"], "status": "completed"})
    assert done.json()["status"] == "completed"
    assert client.post("/reviews", json={**review, "author_id": outsider["id"]}).status_code == 403
    created = client.post("/reviews", json={**review, "comment": "  Great   session "})
    assert created.status_code == 201
    assert created.json()["reviewee_id"] == b["id"]
    assert created.json()["comment"] == "Great session"
    assert client.post("/reviews", json=review).status_code == 409
    assert client.post("/reviews", json={**review, "rating": 6}).status_code == 422
    reply = client.post("/reviews", json={**review, "author_id": b["id"], "rating": 3})
    assert reply.status_code == 201
    assert client.get(f"/users/{b['id']}").json()["average_rating"] == 5.0
    assert client.get(f"/users/{a['id']}").json()["reviews_count"] == 1
    assert client.get("/reviews", params={"user_id": b["id"]}).json()[0]["rating"] == 5
    rid = created.json()["id"]
    assert client.patch(f"/reviews/{rid}", json={"author_id": b["id"], "rating": 1}).status_code == 403
    assert client.patch(f"/reviews/{rid}", json={"author_id": a["id"], "rating": 4}).json()["rating"] == 4
    assert client.get(f"/users/{b['id']}").json()["average_rating"] == 4.0
    assert client.delete(f"/reviews/{rid}", params={"author_id": b["id"]}).status_code == 403
    assert client.delete(f"/reviews/{rid}", params={"author_id": a["id"]}).status_code == 204
    assert client.get(f"/reviews/{rid}").status_code == 404
    assert client.delete(f"/swaps/{sid}", params={"actor_id": a["id"]}).status_code == 204
    assert client.get(f"/swaps/{sid}").status_code == 404
    assert client.get("/reviews").json() == []


def test_cancel_and_decline(client):
    a, b, python, english = setup_pair(client)
    sid = make_swap(client, a, b, python, english).json()["id"]
    declined = client.patch(f"/swaps/{sid}/status", json={"actor_id": b["id"], "status": "declined"})
    assert declined.json()["status"] == "declined"
    assert client.patch(f"/swaps/{sid}/status", json={"actor_id": b["id"], "status": "accepted"}).status_code == 409
    sid2 = make_swap(client, a, b, python, english).json()["id"]
    cancelled = client.patch(f"/swaps/{sid2}/status", json={"actor_id": a["id"], "status": "cancelled"})
    assert cancelled.json()["status"] == "cancelled"


def test_schedule_overlap_conflict(client):
    a, b, python, english = setup_pair(client)
    c = make_user(client, 3)
    add_skill(client, c["id"], english["id"], "offer")
    slot = future(6)
    first = make_swap(client, a, b, python, english, scheduled_at=slot).json()["id"]
    client.patch(f"/swaps/{first}/status", json={"actor_id": b["id"], "status": "accepted"})
    clash = make_swap(client, a, c, python, english, offered_skill_id=None, scheduled_at=slot)
    assert clash.status_code == 409
    free = make_swap(client, a, c, python, english, offered_skill_id=None, scheduled_at=future(8))
    assert free.status_code == 201


def test_swap_update_and_filters(client):
    a, b, python, english = setup_pair(client)
    sid = make_swap(client, a, b, python, english).json()["id"]
    assert client.patch(f"/swaps/{sid}", json={"actor_id": b["id"], "message": "x"}).status_code == 403
    assert client.patch(f"/swaps/{sid}", json={"actor_id": a["id"]}).status_code == 400
    assert client.patch(f"/swaps/{sid}", json={"actor_id": a["id"], "scheduled_at": future(-2)}).status_code == 400
    ok = client.patch(f"/swaps/{sid}", json={"actor_id": a["id"], "duration_minutes": 90})
    assert ok.json()["duration_minutes"] == 90
    assert len(client.get("/swaps", params={"user_id": b["id"], "role": "partner"}).json()) == 1
    assert client.get("/swaps", params={"user_id": b["id"], "role": "requester"}).json() == []
    assert client.get("/swaps", params={"role": "partner"}).status_code == 400
    assert client.get("/swaps", params={"status": "bogus"}).status_code == 422
    assert client.get("/swaps", params={"user_id": 999}).status_code == 404
    assert client.get("/swaps/999").status_code == 404


def test_offer_removal_blocked_by_active_swap(client):
    a, b, python, english = setup_pair(client)
    make_swap(client, a, b, python, english)
    records = client.get(f"/users/{b['id']}/skills", params={"kind": "offer"}).json()
    assert client.delete(f"/users/{b['id']}/skills/{records[0]['id']}").status_code == 409
    assert client.delete(f"/users/{a['id']}/skills/{records[0]['id']}").status_code == 404


def test_delete_user_cascade(client):
    a, b, python, english = setup_pair(client)
    sid = make_swap(client, a, b, python, english).json()["id"]
    client.patch(f"/swaps/{sid}/status", json={"actor_id": b["id"], "status": "cancelled"})
    assert client.delete(f"/users/{b['id']}").status_code == 204
    assert client.get(f"/swaps/{sid}").status_code == 404
    assert client.get(f"/users/{a['id']}/matches").json() == []
