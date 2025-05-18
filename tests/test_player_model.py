from fastapi.testclient import TestClient
from app.main import app
from app.database import SessionLocal
from app.models import Player

client = TestClient(app)

def test_create_player_and_assign_rack():
    db = SessionLocal()

    # Spiel anlegen
    res = client.post("/games/")
    game_id = res.json()["id"]

    # Benutzer registrieren
    user_res = client.post("/users/register", json={"username": "tester", "password": "testpass"})
    assert user_res.status_code in (200, 400)

    # Simuliere Benutzer-ID (wird sonst durch Login ermittelt)
    user_id = 1

    # Spieler manuell anlegen
    player = Player(user_id=user_id, game_id=game_id, rack="HALLOTE", score=0)
    db.add(player)
    db.commit()
    db.refresh(player)

    # Prüfen
    assert player.rack == "HALLOTE"
    assert player.score == 0
    assert player.user_id == user_id
    assert player.game_id == game_id

    db.close()
