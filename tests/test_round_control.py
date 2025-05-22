# tests/test_round_control.py

from fastapi.testclient import TestClient
from app.main import app
import uuid
from datetime import datetime, timezone

client = TestClient(app)

def test_turn_rotation_after_move():
    pw = "pw"
    # Spieler 1
    u1 = f"user1_{uuid.uuid4().hex[:6]}"
    client.post("/users/register", json={"username": u1, "password": pw})
    t1 = client.post("/auth/token", data={"username": u1, "password": pw}).json()["access_token"]
    h1 = {"Authorization": f"Bearer {t1}"}

    # Spieler 2
    u2 = f"user2_{uuid.uuid4().hex[:6]}"
    client.post("/users/register", json={"username": u2, "password": pw})
    t2 = client.post("/auth/token", data={"username": u2, "password": pw}).json()["access_token"]
    h2 = {"Authorization": f"Bearer {t2}"}

    # Spiel anlegen, beitreten, starten
    gid = client.post("/games/").json()["id"]
    client.post(f"/games/{gid}/join", headers=h1)
    client.post(f"/games/{gid}/join", headers=h2)
    client.post(f"/games/{gid}/start", headers=h1)

    # user1 macht Zug
    move = [{"row":7,"col":7,"letter":"H"}]
    resp1 = client.post(f"/games/{gid}/move", json={"move_data": move}, headers=h1)
    assert resp1.status_code == 200

    # user1 darf nicht erneut
    resp1b = client.post(f"/games/{gid}/move", json={"move_data": move}, headers=h1)
    assert resp1b.status_code == 403

    # user2 darf jetzt
    resp2 = client.post(f"/games/{gid}/move", json={"move_data": move}, headers=h2)
    assert resp2.status_code == 200


def test_pass_turn():
    pw = "pw"
    # Spieler 1
    u1 = f"user1_{uuid.uuid4().hex[:6]}"
    client.post("/users/register", json={"username": u1, "password": pw})
    t1 = client.post("/auth/token", data={"username": u1, "password": pw}).json()["access_token"]
    h1 = {"Authorization": f"Bearer {t1}"}

    # Spieler 2
    u2 = f"user2_{uuid.uuid4().hex[:6]}"
    client.post("/users/register", json={"username": u2, "password": pw})
    t2 = client.post("/auth/token", data={"username": u2, "password": pw}).json()["access_token"]
    h2 = {"Authorization": f"Bearer {t2}"}

    # Spiel anlegen, beitreten, starten
    gid = client.post("/games/").json()["id"]
    client.post(f"/games/{gid}/join", headers=h1)
    client.post(f"/games/{gid}/join", headers=h2)
    client.post(f"/games/{gid}/start", headers=h1)

    # user1 passt
    pass_res = client.post(f"/games/{gid}/pass", headers=h1)
    assert pass_res.status_code == 200
    np = pass_res.json()["next_player_id"]
    assert np is not None