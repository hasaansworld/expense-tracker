"""
Tests for Group-related API endpoints.

This module contains test cases for the group management features
including group creation, retrieval, update, and deletion.
"""

import json

from expenses.models import Group, GroupMember
from tests.conftest import create_user, get_auth_headers


class TestGroupEndpoints:
    """Test cases for Group-related endpoints"""

    def test_get_groups(self, client):
        """Test GET /api/groups/ - Should return list of groups"""
        # Create a user and group first
        api_key = create_user(client)

        # Create a group via API
        group_data = {"name": "Test Group", "description": "API-created group"}
        client.post(
            "/api/groups/",
            data=json.dumps(group_data),
            headers=get_auth_headers(api_key),
        )

        # Get all groups
        response = client.get("/api/groups/")
        assert response.status_code == 200
        data = json.loads(response.data)
        assert "groups" in data
        assert len(data["groups"]) == 1
        assert data["groups"][0]["name"] == "Test Group"

        # ✅ Hypermedia check
        assert "@controls" in data
        assert "create" in data["@controls"]
        assert "self" in data["@controls"]
        assert "@controls" in data["groups"][0]
        assert "self" in data["groups"][0]["@controls"]
        assert "members" in data["groups"][0]["@controls"]
        assert "expenses" in data["groups"][0]["@controls"]

    def test_create_group_authenticated(self, client):
        """Test POST /api/groups/ with valid auth - Should create a new group"""
        # Create a user first
        api_key = create_user(client)

        # Create a group
        group_data = {"name": "New Group", "description": "Test description"}
        response = client.post(
            "/api/groups/",
            data=json.dumps(group_data),
            headers=get_auth_headers(api_key),
        )
        assert response.status_code == 201
        data = json.loads(response.data)
        assert data["name"] == "New Group"
        assert data["description"] == "Test description"

        # Hypermedia check
        assert "@controls" in data
        assert "self" in data["@controls"]
        assert "members" in data["@controls"]
        assert "expenses" in data["@controls"]

        # Verify the creator was automatically added as admin
        group = Group.query.first()
        member = GroupMember.query.filter_by(group_id=group.id).first()
        assert member is not None
        assert member.role == "admin"

    def test_create_group_unauthenticated(self, client):
        """Test POST /api/groups/ without auth - Should return 403 Forbidden"""
        group_data = {"name": "Unauthorized Group"}
        response = client.post(
            "/api/groups/", data=json.dumps(group_data), content_type="application/json"
        )
        assert response.status_code == 403

    def test_create_group_invalid_data(self, client):
        """Test POST /api/groups/ with invalid data - Should return 400 Bad Request"""
        # Create a user first
        api_key = create_user(client)

        # Try to create a group with missing name (required field)
        group_data = {"description": "Missing name field"}
        response = client.post(
            "/api/groups/",
            data=json.dumps(group_data),
            headers=get_auth_headers(api_key),
        )
        assert response.status_code == 400

    def test_get_specific_group(self, client):
        """Test GET /api/groups/<group_id> - Should return group details"""
        # Create a user and group first
        api_key = create_user(client)

        # Create a group via API
        group_data = {"name": "Test Group", "description": "Group description"}
        response = client.post(
            "/api/groups/",
            data=json.dumps(group_data),
            headers=get_auth_headers(api_key),
        )
        group_uuid = json.loads(response.data)["id"]

        # Get group details
        response = client.get(f"/api/groups/{group_uuid}")
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data["name"] == "Test Group"

        # Hypermedia check
        assert "@controls" in data
        assert "self" in data["@controls"]
        assert "update" in data["@controls"]
        assert "delete" in data["@controls"]
        assert "members" in data["@controls"]
        assert "expenses" in data["@controls"]

    def test_update_group_as_admin(self, client):
        """Test PUT /api/groups/<group_id> as admin - Should update group info"""
        # Create a user first
        api_key = create_user(client)

        # Create a group via API
        group_data = {"name": "Original Name", "description": "Original description"}
        response = client.post(
            "/api/groups/",
            data=json.dumps(group_data),
            headers=get_auth_headers(api_key),
        )
        group_uuid = json.loads(response.data)["id"]

        # Update group
        update_data = {"name": "Updated Group", "description": "New description"}
        response = client.put(
            f"/api/groups/{group_uuid}",
            data=json.dumps(update_data),
            headers=get_auth_headers(api_key),
        )
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data["name"] == "Updated Group"
        assert data["description"] == "New description"

        #  Hypermedia check
        assert "@controls" in data
        assert "self" in data["@controls"]

    def test_delete_group_as_admin(self, client):
        """Test DELETE /api/groups/<group_id> as admin - Should delete group"""
        # Create a user first
        api_key = create_user(client)

        # Create a group via API
        group_data = {
            "name": "Group to Delete",
            "description": "This group will be deleted",
        }
        response = client.post(
            "/api/groups/",
            data=json.dumps(group_data),
            headers=get_auth_headers(api_key),
        )
        group_uuid = json.loads(response.data)["id"]

        # Delete group
        response = client.delete(
            f"/api/groups/{group_uuid}", headers=get_auth_headers(api_key)
        )
        assert response.status_code == 204

        # Verify group is deleted
        deleted_group = Group.query.first()
        assert deleted_group is None
