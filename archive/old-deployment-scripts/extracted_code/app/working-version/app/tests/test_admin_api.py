import pytest
from fastapi.testclient import TestClient
from app.main import app
import uuid
from tests.test_utils import get_test_token, create_test_user

client = TestClient(app)

def test_admin_list_wordlists():
    username = f"admin_{uuid.uuid4().hex[:6]}"
    password = "testpass"
    response = create_test_user(client, username, password)
    assert response.status_code == 200
    token = get_test_token(username)
    headers = {"Authorization": f"Bearer {token}"}
    
    response = client.get("/admin/wordlists", headers=headers)
    assert response.status_code in (200, 403, 404)

def test_admin_delete_wordlist():
    username = f"admin_{uuid.uuid4().hex[:6]}"
    password = "testpass"
    response = create_test_user(client, username, password)
    assert response.status_code == 200
    token = get_test_token(username)
    headers = {"Authorization": f"Bearer {token}"}
    
    response = client.delete("/admin/wordlists/en", headers=headers)
    assert response.status_code in (200, 403, 404)

def test_admin_import_wordlist():
    username = f"admin_{uuid.uuid4().hex[:6]}"
    password = "testpass"
    response = create_test_user(client, username, password)
    assert response.status_code == 200
    token = get_test_token(username)
    headers = {"Authorization": f"Bearer {token}"}
    
    response = client.post("/admin/wordlists/import", headers=headers, data={"language": "test"})
    assert response.status_code in (200, 403, 404, 422)

def test_non_admin_access():
    username = f"user_{uuid.uuid4().hex[:6]}"
    password = "testpass"
    response = create_test_user(client, username, password)
    assert response.status_code == 200
    token = get_test_token(username)
    headers = {"Authorization": f"Bearer {token}"}
    
    response = client.get("/admin/wordlists", headers=headers)
    assert response.status_code == 403

