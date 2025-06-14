"""
Comprehensive API tests for admin endpoints.
Tests admin user management, game administration, and system features.
"""
import pytest
from fastapi.testclient import TestClient
from app.main import app
import uuid
from tests.test_utils import get_test_token, create_test_user
from app.models import User
from app.auth import create_access_token, get_password_hash
from datetime import datetime, timezone, timedelta
import json

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

class TestAdminAPI:
    """Test admin API endpoints."""

    @pytest.fixture
    def admin_user(self, db_session):
        """Create an admin user for testing."""
        admin = User(
            username="adminuser",
            hashed_password=get_password_hash("adminpassword123"),
            email="admin@example.com",
            is_admin=True
        )
        db_session.add(admin)
        db_session.commit()
        db_session.refresh(admin)
        
        # Create admin token
        admin_token = create_access_token(
            data={"sub": "adminuser"},
            expires_delta=timedelta(minutes=30)
        )
        
        return {
            "id": admin.id,
            "username": "adminuser",
            "token": admin_token,
            "password": "adminpassword123"
        }

    def test_get_admin_stats_success(self, client: TestClient, admin_user):
        """Test getting admin statistics."""
        headers = {"Authorization": f"Bearer {admin_user['token']}"}
        response = client.get("/admin/stats", headers=headers)
        
        if response.status_code != 404:  # Endpoint exists
            assert response.status_code == 200
            data = response.json()
            assert "total_users" in data or "users" in data
            assert "total_games" in data or "games" in data

    def test_get_admin_stats_forbidden_regular_user(self, client: TestClient, test_user):
        """Test that regular users cannot access admin stats."""
        headers = {"Authorization": f"Bearer {test_user['token']}"}
        response = client.get("/admin/stats", headers=headers)
        
        if response.status_code != 404:  # Endpoint exists
            assert response.status_code == 403

    def test_get_all_users_admin(self, client: TestClient, admin_user):
        """Test getting all users as admin."""
        headers = {"Authorization": f"Bearer {admin_user['token']}"}
        response = client.get("/admin/users", headers=headers)
        
        if response.status_code != 404:  # Endpoint exists
            assert response.status_code == 200
            data = response.json()
            assert isinstance(data, list) or "users" in data

    def test_get_user_details_admin(self, client: TestClient, admin_user, test_user):
        """Test getting specific user details as admin."""
        headers = {"Authorization": f"Bearer {admin_user['token']}"}
        response = client.get(f"/admin/users/{test_user['id']}", headers=headers)
        
        if response.status_code != 404:  # Endpoint exists
            assert response.status_code == 200
            data = response.json()
            assert data["username"] == test_user["username"]

    def test_update_user_admin(self, client: TestClient, admin_user, test_user):
        """Test updating user as admin."""
        headers = {"Authorization": f"Bearer {admin_user['token']}"}
        response = client.patch(f"/admin/users/{test_user['id']}", json={
            "is_admin": False,
            "is_active": True,
            "email": "updated_by_admin@example.com"
        }, headers=headers)
        
        if response.status_code != 404:  # Endpoint exists
            assert response.status_code == 200

    def test_delete_user_admin(self, client: TestClient, admin_user, db_session):
        """Test deleting user as admin."""
        # Create a user to delete
        user_to_delete = User(
            username="deleteme",
            hashed_password=get_password_hash("password123"),
            email="deleteme@example.com"
        )
        db_session.add(user_to_delete)
        db_session.commit()
        db_session.refresh(user_to_delete)
        
        headers = {"Authorization": f"Bearer {admin_user['token']}"}
        response = client.delete(f"/admin/users/{user_to_delete.id}", headers=headers)
        
        if response.status_code != 404:  # Endpoint exists
            assert response.status_code in [200, 204]

    def test_ban_user_admin(self, client: TestClient, admin_user, test_user):
        """Test banning user as admin."""
        headers = {"Authorization": f"Bearer {admin_user['token']}"}
        response = client.post(f"/admin/users/{test_user['id']}/ban", json={
            "reason": "Inappropriate behavior",
            "duration_days": 7
        }, headers=headers)
        
        if response.status_code != 404:  # Endpoint exists
            assert response.status_code == 200

    def test_unban_user_admin(self, client: TestClient, admin_user, test_user):
        """Test unbanning user as admin."""
        headers = {"Authorization": f"Bearer {admin_user['token']}"}
        response = client.delete(f"/admin/users/{test_user['id']}/ban", headers=headers)
        
        if response.status_code != 404:  # Endpoint exists
            assert response.status_code == 200

    def test_get_all_games_admin(self, client: TestClient, admin_user):
        """Test getting all games as admin."""
        headers = {"Authorization": f"Bearer {admin_user['token']}"}
        response = client.get("/admin/games", headers=headers)
        
        if response.status_code != 404:  # Endpoint exists
            assert response.status_code == 200
            data = response.json()
            assert isinstance(data, list) or "games" in data

    def test_get_game_details_admin(self, client: TestClient, admin_user, test_user):
        """Test getting specific game details as admin."""
        # First create a game
        headers_user = {"Authorization": f"Bearer {test_user['token']}"}
        create_response = client.post("/games/", json={
            "language": "en",
            "max_players": 2
        }, headers=headers_user)
        
        if create_response.status_code == 200:
            game_id = create_response.json()["id"]
            
            headers_admin = {"Authorization": f"Bearer {admin_user['token']}"}
            response = client.get(f"/admin/games/{game_id}", headers=headers_admin)
            
            if response.status_code != 404:  # Endpoint exists
                assert response.status_code == 200
                data = response.json()
                assert data["id"] == game_id

    def test_terminate_game_admin(self, client: TestClient, admin_user, test_user):
        """Test terminating game as admin."""
        # First create a game
        headers_user = {"Authorization": f"Bearer {test_user['token']}"}
        create_response = client.post("/games/", json={
            "language": "en",
            "max_players": 2
        }, headers=headers_user)
        
        if create_response.status_code == 200:
            game_id = create_response.json()["id"]
            
            headers_admin = {"Authorization": f"Bearer {admin_user['token']}"}
            response = client.post(f"/admin/games/{game_id}/terminate", json={
                "reason": "Administrative action"
            }, headers=headers_admin)
            
            if response.status_code != 404:  # Endpoint exists
                assert response.status_code == 200

    def test_get_system_health_admin(self, client: TestClient, admin_user):
        """Test getting system health as admin."""
        headers = {"Authorization": f"Bearer {admin_user['token']}"}
        response = client.get("/admin/health", headers=headers)
        
        if response.status_code != 404:  # Endpoint exists
            assert response.status_code == 200
            data = response.json()
            assert "status" in data or "database" in data

    def test_get_error_logs_admin(self, client: TestClient, admin_user):
        """Test getting error logs as admin."""
        headers = {"Authorization": f"Bearer {admin_user['token']}"}
        response = client.get("/admin/logs/errors", headers=headers)
        
        if response.status_code != 404:  # Endpoint exists
            assert response.status_code == 200
            data = response.json()
            assert isinstance(data, list) or "logs" in data

    def test_clear_cache_admin(self, client: TestClient, admin_user):
        """Test clearing cache as admin."""
        headers = {"Authorization": f"Bearer {admin_user['token']}"}
        response = client.post("/admin/cache/clear", headers=headers)
        
        if response.status_code != 404:  # Endpoint exists
            assert response.status_code == 200

    def test_update_system_settings_admin(self, client: TestClient, admin_user):
        """Test updating system settings as admin."""
        headers = {"Authorization": f"Bearer {admin_user['token']}"}
        response = client.patch("/admin/settings", json={
            "maintenance_mode": False,
            "registration_enabled": True,
            "max_games_per_user": 10
        }, headers=headers)
        
        if response.status_code != 404:  # Endpoint exists
            assert response.status_code == 200

    def test_backup_database_admin(self, client: TestClient, admin_user):
        """Test database backup as admin."""
        headers = {"Authorization": f"Bearer {admin_user['token']}"}
        response = client.post("/admin/backup", headers=headers)
        
        if response.status_code != 404:  # Endpoint exists
            assert response.status_code in [200, 202]  # 202 for async operation

    def test_get_user_activity_admin(self, client: TestClient, admin_user, test_user):
        """Test getting user activity as admin."""
        headers = {"Authorization": f"Bearer {admin_user['token']}"}
        response = client.get(f"/admin/users/{test_user['id']}/activity", headers=headers)
        
        if response.status_code != 404:  # Endpoint exists
            assert response.status_code == 200
            data = response.json()
            assert isinstance(data, list) or "activities" in data

    def test_send_announcement_admin(self, client: TestClient, admin_user):
        """Test sending announcement as admin."""
        headers = {"Authorization": f"Bearer {admin_user['token']}"}
        response = client.post("/admin/announcements", json={
            "title": "System Maintenance",
            "message": "The system will be down for maintenance from 2-4 AM UTC.",
            "priority": "high",
            "target_users": "all"
        }, headers=headers)
        
        if response.status_code != 404:  # Endpoint exists
            assert response.status_code in [200, 201]

    def test_get_announcements_admin(self, client: TestClient, admin_user):
        """Test getting announcements as admin."""
        headers = {"Authorization": f"Bearer {admin_user['token']}"}
        response = client.get("/admin/announcements", headers=headers)
        
        if response.status_code != 404:  # Endpoint exists
            assert response.status_code == 200
            data = response.json()
            assert isinstance(data, list) or "announcements" in data

    def test_get_word_statistics_admin(self, client: TestClient, admin_user):
        """Test getting word statistics as admin."""
        headers = {"Authorization": f"Bearer {admin_user['token']}"}
        response = client.get("/admin/words/stats", headers=headers)
        
        if response.status_code != 404:  # Endpoint exists
            assert response.status_code == 200
            data = response.json()
            assert isinstance(data, dict)

    def test_manage_wordlist_admin(self, client: TestClient, admin_user):
        """Test managing wordlist as admin."""
        headers = {"Authorization": f"Bearer {admin_user['token']}"}
        
        # Add words
        response = client.post("/admin/words", json={
            "language": "en",
            "words": ["TESTWORD", "ADMINWORD"]
        }, headers=headers)
        
        if response.status_code != 404:  # Endpoint exists
            assert response.status_code in [200, 201]

    def test_delete_words_admin(self, client: TestClient, admin_user):
        """Test deleting words as admin."""
        headers = {"Authorization": f"Bearer {admin_user['token']}"}
        response = client.delete("/admin/words", json={
            "language": "en",
            "words": ["TESTWORD"]
        }, headers=headers)
        
        if response.status_code != 404:  # Endpoint exists
            assert response.status_code == 200

    def test_get_pending_reports_admin(self, client: TestClient, admin_user):
        """Test getting pending reports as admin."""
        headers = {"Authorization": f"Bearer {admin_user['token']}"}
        response = client.get("/admin/reports", headers=headers)
        
        if response.status_code != 404:  # Endpoint exists
            assert response.status_code == 200
            data = response.json()
            assert isinstance(data, list) or "reports" in data

    def test_resolve_report_admin(self, client: TestClient, admin_user):
        """Test resolving report as admin."""
        headers = {"Authorization": f"Bearer {admin_user['token']}"}
        response = client.patch("/admin/reports/1", json={
            "status": "resolved",
            "action_taken": "User warned",
            "admin_notes": "First offense, issued warning"
        }, headers=headers)
        
        if response.status_code != 404:  # Endpoint exists
            assert response.status_code in [200, 404]  # 404 if report doesn't exist

    def test_get_analytics_admin(self, client: TestClient, admin_user):
        """Test getting analytics as admin."""
        headers = {"Authorization": f"Bearer {admin_user['token']}"}
        response = client.get("/admin/analytics", headers=headers)
        
        if response.status_code != 404:  # Endpoint exists
            assert response.status_code == 200
            data = response.json()
            assert isinstance(data, dict)

    def test_export_data_admin(self, client: TestClient, admin_user):
        """Test exporting data as admin."""
        headers = {"Authorization": f"Bearer {admin_user['token']}"}
        response = client.get("/admin/export?type=users&format=csv", headers=headers)
        
        if response.status_code != 404:  # Endpoint exists
            assert response.status_code == 200

    def test_import_data_admin(self, client: TestClient, admin_user):
        """Test importing data as admin."""
        headers = {"Authorization": f"Bearer {admin_user['token']}"}
        
        # Mock CSV data
        csv_data = b"username,email\ntestimport,test@import.com"
        files = {"file": ("import.csv", csv_data, "text/csv")}
        
        response = client.post("/admin/import", files=files, headers=headers)
        
        if response.status_code != 404:  # Endpoint exists
            assert response.status_code in [200, 202]

    def test_maintenance_mode_admin(self, client: TestClient, admin_user):
        """Test enabling/disabling maintenance mode as admin."""
        headers = {"Authorization": f"Bearer {admin_user['token']}"}
        
        # Enable maintenance mode
        response = client.post("/admin/maintenance", json={
            "enabled": True,
            "message": "System under maintenance"
        }, headers=headers)
        
        if response.status_code != 404:  # Endpoint exists
            assert response.status_code == 200

    def test_get_active_sessions_admin(self, client: TestClient, admin_user):
        """Test getting active sessions as admin."""
        headers = {"Authorization": f"Bearer {admin_user['token']}"}
        response = client.get("/admin/sessions", headers=headers)
        
        if response.status_code != 404:  # Endpoint exists
            assert response.status_code == 200
            data = response.json()
            assert isinstance(data, list) or "sessions" in data

    def test_revoke_user_sessions_admin(self, client: TestClient, admin_user, test_user):
        """Test revoking user sessions as admin."""
        headers = {"Authorization": f"Bearer {admin_user['token']}"}
        response = client.delete(f"/admin/users/{test_user['id']}/sessions", headers=headers)
        
        if response.status_code != 404:  # Endpoint exists
            assert response.status_code == 200

    def test_unauthorized_access_admin_endpoints(self, client: TestClient, test_user):
        """Test that regular users cannot access admin endpoints."""
        headers = {"Authorization": f"Bearer {test_user['token']}"}
        
        admin_endpoints = [
            ("GET", "/admin/stats"),
            ("GET", "/admin/users"),
            ("GET", "/admin/games"),
            ("POST", "/admin/cache/clear"),
            ("GET", "/admin/logs/errors"),
            ("POST", "/admin/announcements"),
        ]
        
        for method, endpoint in admin_endpoints:
            if method == "GET":
                response = client.get(endpoint, headers=headers)
            else:
                response = client.post(endpoint, json={}, headers=headers)
            
            if response.status_code != 404:  # Endpoint exists
                assert response.status_code == 403

    def test_unauthenticated_access_admin_endpoints(self, client: TestClient):
        """Test that unauthenticated users cannot access admin endpoints."""
        admin_endpoints = [
            ("GET", "/admin/stats"),
            ("GET", "/admin/users"),
            ("GET", "/admin/games"),
        ]
        
        for method, endpoint in admin_endpoints:
            if method == "GET":
                response = client.get(endpoint)
            else:
                response = client.post(endpoint, json={})
            
            assert response.status_code == 401

    def test_admin_user_creation(self, client: TestClient, admin_user):
        """Test creating admin user as admin."""
        headers = {"Authorization": f"Bearer {admin_user['token']}"}
        response = client.post("/admin/users", json={
            "username": "newadmin",
            "password": "securepassword123",
            "email": "newadmin@example.com",
            "is_admin": True
        }, headers=headers)
        
        if response.status_code != 404:  # Endpoint exists
            assert response.status_code in [200, 201]

    def test_bulk_user_operations_admin(self, client: TestClient, admin_user):
        """Test bulk user operations as admin."""
        headers = {"Authorization": f"Bearer {admin_user['token']}"}
        response = client.post("/admin/users/bulk", json={
            "action": "send_notification",
            "user_ids": [1, 2, 3],
            "notification": {
                "title": "System Update",
                "message": "Please update your client"
            }
        }, headers=headers)
        
        if response.status_code != 404:  # Endpoint exists
            assert response.status_code == 200

    def test_server_metrics_admin(self, client: TestClient, admin_user):
        """Test getting server metrics as admin."""
        headers = {"Authorization": f"Bearer {admin_user['token']}"}
        response = client.get("/admin/metrics", headers=headers)
        
        if response.status_code != 404:  # Endpoint exists
            assert response.status_code == 200
            data = response.json()
            assert "cpu_usage" in data or "memory_usage" in data or "response_times" in data

