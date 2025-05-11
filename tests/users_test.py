"""
Tests for User-related API endpoints.

This module contains test cases for the user management features
including user creation, retrieval, update, and deletion.
"""

import json
from expenses.models import User
from tests.conftest import app, create_user, get_auth_headers


class TestUserEndpoints:
    """Test cases for User-related endpoints"""

    def test_get_users(self, client):
        """Test GET /api/users/ - Should return list of users"""
        create_user(client)

        response = client.get("/api/users/")
        assert response.status_code == 200
        data = json.loads(response.data)
        assert "users" in data
        assert len(data["users"]) == 1
        assert data["users"][0]["email"] == "test@example.com"

        # Hypermedia check
        assert "@controls" in data
        assert "create" in data["@controls"]

    def test_create_user_valid(self, client):
        """Test POST /api/users/ with valid data - Should create a new user"""
        user_data = {
            "name": "Alice",
            "email": "alice@example.com",
            "password_hash": "alicepass",
        }
        response = client.post("/api/users/", data=json.dumps(user_data), content_type="application/json")
        assert response.status_code == 201
        data = json.loads(response.data)
        assert "email" in data and data["email"] == "alice@example.com"
        assert "api_key" in data
        assert "@controls" in data
        assert "self" in data["@controls"]
        assert "update" in data["@controls"]

        with app.app_context():
            user = User.query.filter_by(email="alice@example.com").first()
            assert user is not None
            assert user.name == "Alice"

    def test_create_user_duplicate_email(self, client):
        """Test POST /api/users/ with duplicate email - Should return 409 Conflict"""
        user_data = {
            "name": "Bob",
            "email": "bob@example.com",
            "password_hash": "bobpass",
        }
        client.post("/api/users/", data=json.dumps(user_data), content_type="application/json")
        response = client.post("/api/users/", data=json.dumps(user_data), content_type="application/json")
        assert response.status_code == 409
        assert "already exists" in json.loads(response.data)["message"]

    def test_create_user_invalid_data(self, client):
        """Test POST /api/users/ with missing required field - Should return 400 Bad Request"""
        user_data = {"email": "invalid@example.com", "password_hash": "pass"}
        response = client.post("/api/users/", data=json.dumps(user_data), content_type="application/json")
        assert response.status_code == 400

    def test_get_specific_user(self, client):
        """Test GET /api/users/<user_id> - Should return user details"""
        create_user(client)
        user = User.query.first()
        user_uuid = user.uuid

        response = client.get(f"/api/users/{user_uuid}")
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data["name"] == "Test User"
        assert data["email"] == "test@example.com"
        assert "@controls" in data
        assert "update" in data["@controls"]

    def test_get_nonexistent_user(self, client):
        """Test GET /api/users/<user_id> with invalid ID - Should return 404 Not Found"""
        response = client.get("/api/users/nonexistent-id")
        assert response.status_code == 404

    def test_update_user_authenticated(self, client):
        """Test PUT /api/users/<user_id> as authenticated user - Should update user info"""
        api_key = create_user(client)
        user = User.query.first()
        user_uuid = user.uuid

        update_data = {"name": "Updated Name"}
        response = client.put(f"/api/users/{user_uuid}", data=json.dumps(update_data), headers=get_auth_headers(api_key))
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data["name"] == "Updated Name"
        assert "@controls" in data

        updated_user = User.query.first()
        assert updated_user.name == "Updated Name"

    def test_update_other_user(self, client):
        """Test PUT /api/users/<user_id> on another user's account - Should return 403 Forbidden"""
        api_key_1 = create_user(client, email="user1@example.com")
        user_data = {
            "name": "User 2",
            "email": "user2@example.com",
            "password_hash": "pass2",
        }
        client.post("/api/users/", data=json.dumps(user_data), content_type="application/json")
        user2 = User.query.filter_by(email="user2@example.com").first()

        update_data = {"name": "Hacked Name"}
        response = client.put(f"/api/users/{user2.uuid}", data=json.dumps(update_data), headers=get_auth_headers(api_key_1))
        assert response.status_code == 403

    def test_delete_user_authenticated(self, client):
        """Test DELETE /api/users/<user_id> as authenticated user - Should delete user"""
        api_key = create_user(client)
        user = User.query.first()
        response = client.delete(f"/api/users/{user.uuid}", headers=get_auth_headers(api_key))
        assert response.status_code == 204
        deleted_user = User.query.first()
        assert deleted_user is None

    def test_delete_without_auth(self, client):
        """Test DELETE /api/users/<user_id> without auth - Should return 403 Forbidden"""
        create_user(client)
        user = User.query.first()
        response = client.delete(f"/api/users/{user.uuid}")
        assert response.status_code == 403

    def test_post_without_json(self, client):
        """Test POST /api/users/ without JSON - Should return 415 Unsupported Media Type"""
        response = client.post("/api/users/", data="not json")
        assert response.status_code == 415

    def test_post_missing_email(self, client):
        """Test POST /api/users/ with missing email - Should return 400 Bad Request"""
        user_data = {"name": "Invalid User", "password_hash": "password123"}
        response = client.post("/api/users/", data=json.dumps(user_data), content_type="application/json")
        assert response.status_code == 400

    def test_update_user_email_conflict(self, client):
        """Test PUT /api/users/<user_id> with conflicting email - Should return 409 Conflict"""
        api_key_1 = create_user(client, email="user1@example.com")
        user_data = {
            "name": "User 2",
            "email": "user2@example.com",
            "password_hash": "pass2",
        }
        client.post("/api/users/", data=json.dumps(user_data), content_type="application/json")

        user1 = User.query.filter_by(email="user1@example.com").first()
        update_data = {"email": "user2@example.com"}
        response = client.put(f"/api/users/{user1.uuid}", data=json.dumps(update_data), headers=get_auth_headers(api_key_1))
        assert response.status_code == 409

    def test_delete_other_user(self, client):
        """Test DELETE /api/users/<user_id> on another user's account - Should return 403 Forbidden"""
        api_key_1 = create_user(client, email="user1@example.com")
        user_data = {
            "name": "User 2",
            "email": "user2@example.com",
            "password_hash": "pass2",
        }
        client.post("/api/users/", data=json.dumps(user_data), content_type="application/json")
        user2 = User.query.filter_by(email="user2@example.com").first()
        response = client.delete(f"/api/users/{user2.uuid}", headers=get_auth_headers(api_key_1))
        assert response.status_code == 403
