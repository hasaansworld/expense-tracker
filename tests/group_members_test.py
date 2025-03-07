"""
Tests for GroupMember-related API endpoints.

This module contains test cases for the group membership features
including adding, retrieving, and removing group members.
"""

import json

from expenses.models import User, Group, GroupMember
from tests.conftest import create_user, get_auth_headers


class TestGroupMemberEndpoints:
    """Test cases for GroupMember-related endpoints"""

    def test_get_group_members(self, client):
        """Test GET /api/groups/<group_id>/members/ - Should return list of members"""
        # Create a user and group first
        api_key = create_user(client)

        # Create a group via API
        group_data = {
            "name": "Member Test Group",
            "description": "Group for testing members",
        }
        response = client.post(
            "/api/groups/",
            data=json.dumps(group_data),
            headers=get_auth_headers(api_key),
        )
        group_uuid = json.loads(response.data)["group"]["id"]

        # Get group members
        response = client.get(f"/api/groups/{group_uuid}/members/")
        assert response.status_code == 200
        data = json.loads(response.data)
        assert "members" in data
        assert len(data["members"]) == 1  # Creator is automatically a member
        assert data["members"][0]["role"] == "admin"

    def test_add_member_as_admin(self, client):
        """Test POST /api/groups/<group_id>/members/ as admin - Should add new member"""
        # Create admin user
        admin_key = create_user(client, name="Admin", email="admin@example.com")

        # Create a new user to be added as member
        create_user(client, name="New Member", email="member@example.com")

        # Create a group via API
        group_data = {
            "name": "Admin Group",
            "description": "Group for testing member addition",
        }
        response = client.post(
            "/api/groups/",
            data=json.dumps(group_data),
            headers=get_auth_headers(admin_key),
        )
        group_uuid = json.loads(response.data)["group"]["id"]

        # Get the member user's UUID
        member = User.query.filter_by(email="member@example.com").first()
        member_uuid = member.uuid

        # Add new member
        member_data = {"user_id": member_uuid, "role": "member"}
        response = client.post(
            f"/api/groups/{group_uuid}/members/",
            data=json.dumps(member_data),
            headers=get_auth_headers(admin_key),
        )
        assert response.status_code == 201

        # Verify member was added
        group = Group.query.first()
        group_members = GroupMember.query.filter_by(group_id=group.id).all()
        assert len(group_members) == 2  # Admin + new member

    def test_add_member_as_non_admin(self, client):
        """Test POST /api/groups/<group_id>/members/ as non-admin - Should return 403 Forbidden"""
        # Create admin user
        admin_key = create_user(client, name="Admin", email="admin@example.com")

        # Create a regular member user
        member_key = create_user(
            client, name="Regular Member", email="member@example.com"
        )

        # Create a user to be added
        create_user(client, name="New Person", email="new@example.com")

        # Create a group via API as admin
        group_data = {
            "name": "Admin Group",
            "description": "Group for testing member addition permissions",
        }
        response = client.post(
            "/api/groups/",
            data=json.dumps(group_data),
            headers=get_auth_headers(admin_key),
        )
        group_uuid = json.loads(response.data)["group"]["id"]

        # Get the member and new person UUIDs
        member = User.query.filter_by(email="member@example.com").first()
        new_person = User.query.filter_by(email="new@example.com").first()
        member_uuid = member.uuid
        new_person_uuid = new_person.uuid

        # Add regular member to group
        member_data = {"user_id": member_uuid, "role": "member"}
        client.post(
            f"/api/groups/{group_uuid}/members/",
            data=json.dumps(member_data),
            headers=get_auth_headers(admin_key),
        )

        # Try to add new member as regular member
        add_data = {"user_id": new_person_uuid}
        response = client.post(
            f"/api/groups/{group_uuid}/members/",
            data=json.dumps(add_data),
            headers=get_auth_headers(member_key),
        )
        assert response.status_code == 403
        assert "admin" in json.loads(response.data)["message"]

    def test_add_duplicate_member(self, client):
        """Test POST /api/groups/<group_id>/members/ with duplicate - Should return 409 Conflict"""
        # Create admin user
        admin_key = create_user(client, name="Admin", email="admin@example.com")

        # Create a user to be added
        create_user(client, name="Member", email="member@example.com")

        # Create a group via API
        group_data = {
            "name": "Test Group",
            "description": "Group for testing duplicate member addition",
        }
        response = client.post(
            "/api/groups/",
            data=json.dumps(group_data),
            headers=get_auth_headers(admin_key),
        )
        group_uuid = json.loads(response.data)["group"]["id"]

        # Get the member's UUID
        member = User.query.filter_by(email="member@example.com").first()
        member_uuid = member.uuid

        # Add member to group
        member_data = {"user_id": member_uuid, "role": "member"}
        client.post(
            f"/api/groups/{group_uuid}/members/",
            data=json.dumps(member_data),
            headers=get_auth_headers(admin_key),
        )

        # Try to add same member again
        response = client.post(
            f"/api/groups/{group_uuid}/members/",
            data=json.dumps(member_data),
            headers=get_auth_headers(admin_key),
        )
        assert response.status_code == 409
        assert "already a member" in json.loads(response.data)["message"]

    def test_remove_member_as_admin(self, client):
        """Test DELETE /api/groups/<group_id>/members/<user_id> as admin - Should remove member"""
        # Create admin user
        admin_key = create_user(client, name="Admin", email="admin@example.com")

        # Create a user to be added and then removed
        create_user(client, name="Member", email="member@example.com")

        # Create a group via API
        group_data = {
            "name": "Test Group",
            "description": "Group for testing member removal",
        }
        response = client.post(
            "/api/groups/",
            data=json.dumps(group_data),
            headers=get_auth_headers(admin_key),
        )
        group_uuid = json.loads(response.data)["group"]["id"]

        # Get the member's UUID
        member = User.query.filter_by(email="member@example.com").first()
        member_uuid = member.uuid

        # Add member to group
        member_data = {"user_id": member_uuid, "role": "member"}
        client.post(
            f"/api/groups/{group_uuid}/members/",
            data=json.dumps(member_data),
            headers=get_auth_headers(admin_key),
        )

        # Remove member
        response = client.delete(
            f"/api/groups/{group_uuid}/members/{member_uuid}",
            headers=get_auth_headers(admin_key),
        )
        assert response.status_code == 204

        # Verify member was removed
        group = Group.query.first()
        members = GroupMember.query.filter_by(group_id=group.id).all()
        assert len(members) == 1  # Only admin left
        assert members[0].user.email == "admin@example.com"

    def test_remove_last_admin(self, client):
        """Test DELETE /api/groups/<group_id>/members/<user_id> on last admin - Should return 400 Bad Request"""
        # Create user
        admin_key = create_user(client, name="Solo Admin", email="admin@example.com")

        # Create a group via API
        group_data = {
            "name": "Solo Admin Group",
            "description": "Group with only one admin",
        }
        response = client.post(
            "/api/groups/",
            data=json.dumps(group_data),
            headers=get_auth_headers(admin_key),
        )
        group_uuid = json.loads(response.data)["group"]["id"]

        # Get the admin's UUID
        admin = User.query.filter_by(email="admin@example.com").first()
        admin_uuid = admin.uuid

        # Try to remove the only admin
        response = client.delete(
            f"/api/groups/{group_uuid}/members/{admin_uuid}",
            headers=get_auth_headers(admin_key),
        )
        assert response.status_code == 400
        assert "last admin" in json.loads(response.data)["message"]
