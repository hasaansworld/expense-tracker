import pytest
import json
from flask import Flask
from expenses.app import app  # Import the app instance
from expenses.models import db, User, Group, GroupMember, Expense, ExpenseParticipant, ApiKey

@pytest.fixture
def client():
    """
    Configure a test client with an in-memory database for testing.
    This overrides the default database configuration in app.py.
    """
    # Save original config to restore it later
    original_db_uri = app.config["SQLALCHEMY_DATABASE_URI"]
    original_testing = app.config.get("TESTING", False)
    
    # Configure for testing with in-memory SQLite database
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///:memory:"
    app.config["TESTING"] = True
    app.config["CACHE_TYPE"] = "NullCache"  # Disable caching for tests
    
    with app.test_client() as client:
        with app.app_context():
            db.create_all()
            yield client
            db.session.remove()
            db.drop_all()
    
    # Restore original configuration
    app.config["SQLALCHEMY_DATABASE_URI"] = original_db_uri
    app.config["TESTING"] = original_testing

def create_user(client, name="Test User", email="test@example.com"):
    """Helper function to create a user and return the API key"""
    user_data = {
        "name": name,
        "email": email,
        "password_hash": "securepassword"
    }
    response = client.post(
        "/api/users/",
        data=json.dumps(user_data),
        content_type="application/json"
    )
    return json.loads(response.data)["api_key"]

def get_auth_headers(api_key):
    """Helper to generate headers with API key for authenticated requests"""
    return {
        "Content-Type": "application/json",
        "X-API-Key": api_key
    }

class TestUserEndpoints:
    """Test cases for User-related endpoints"""
    
    def test_get_users(self, client):
        """Test GET /api/users/ - Should return list of users"""
        # Create a user first
        create_user(client)
        
        # Get all users
        response = client.get("/api/users/")
        assert response.status_code == 200
        data = json.loads(response.data)
        assert "users" in data
        assert len(data["users"]) == 1
        assert data["users"][0]["email"] == "test@example.com"
    
    def test_create_user_valid(self, client):
        """Test POST /api/users/ with valid data - Should create a new user"""
        user_data = {
            "name": "Alice",
            "email": "alice@example.com",
            "password_hash": "alicepass"
        }
        response = client.post(
            "/api/users/",
            data=json.dumps(user_data),
            content_type="application/json"
        )
        assert response.status_code == 201
        data = json.loads(response.data)
        assert "user" in data
        assert "api_key" in data
        assert data["user"]["email"] == "alice@example.com"
        
        # Verify user exists in database
        with app.app_context():
            user = User.query.filter_by(email="alice@example.com").first()
            assert user is not None
            assert user.name == "Alice"
    
    def test_create_user_duplicate_email(self, client):
        """Test POST /api/users/ with duplicate email - Should return 409 Conflict"""
        # First create a user
        user_data = {
            "name": "Bob",
            "email": "bob@example.com",
            "password_hash": "bobpass"
        }
        client.post(
            "/api/users/",
            data=json.dumps(user_data),
            content_type="application/json"
        )
        
        # Try to create another user with the same email
        response = client.post(
            "/api/users/",
            data=json.dumps(user_data),
            content_type="application/json"
        )
        assert response.status_code == 409
        assert "already exists" in json.loads(response.data)["message"]
    
    def test_create_user_invalid_data(self, client):
        """Test POST /api/users/ with missing required field - Should return 400 Bad Request"""
        # Missing name field (required field)
        user_data = {
            "email": "invalid@example.com",
            "password_hash": "pass"
        }
        response = client.post(
            "/api/users/",
            data=json.dumps(user_data),
            content_type="application/json"
        )
        assert response.status_code == 400
    
    def test_get_specific_user(self, client):
        """Test GET /api/users/<user_id> - Should return user details"""
        # Create a user first
        create_user(client)
        
        # Get the user UUID
        with app.app_context():
            user = User.query.first()
            user_uuid = user.uuid
        
        # Get user details
        response = client.get(f"/api/users/{user_uuid}")
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data["user"]["name"] == "Test User"
        assert data["user"]["email"] == "test@example.com"
    
    def test_get_nonexistent_user(self, client):
        """Test GET /api/users/<user_id> with invalid ID - Should return 404 Not Found"""
        response = client.get("/api/users/nonexistent-id")
        assert response.status_code == 404
    
    def test_update_user_authenticated(self, client):
        """Test PUT /api/users/<user_id> as authenticated user - Should update user info"""
        # Create a user and get API key
        api_key = create_user(client)
        
        # Get the user UUID
        with app.app_context():
            user = User.query.first()
            user_uuid = user.uuid
        
        # Update user details
        update_data = {"name": "Updated Name"}
        response = client.put(
            f"/api/users/{user_uuid}",
            data=json.dumps(update_data),
            headers=get_auth_headers(api_key)
        )
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data["user"]["name"] == "Updated Name"
        
        # Verify changes in database
        with app.app_context():
            updated_user = User.query.first()
            assert updated_user.name == "Updated Name"
    
    def test_update_other_user(self, client):
        """Test PUT /api/users/<user_id> on another user's account - Should return 403 Forbidden"""
        # Create first user
        api_key_1 = create_user(client, email="user1@example.com")
        
        # Create second user
        user_data = {
            "name": "User 2",
            "email": "user2@example.com",
            "password_hash": "pass2"
        }
        client.post(
            "/api/users/",
            data=json.dumps(user_data),
            content_type="application/json"
        )
        
        # Get second user's UUID
        with app.app_context():
            user2 = User.query.filter_by(email="user2@example.com").first()
            user2_uuid = user2.uuid
        
        # Try to update second user using first user's API key
        update_data = {"name": "Hacked Name"}
        response = client.put(
            f"/api/users/{user2_uuid}",
            data=json.dumps(update_data),
            headers=get_auth_headers(api_key_1)
        )
        assert response.status_code == 403
        assert "own account" in json.loads(response.data)["message"]
    
    def test_delete_user_authenticated(self, client):
        """Test DELETE /api/users/<user_id> as authenticated user - Should delete user"""
        # Create a user and get API key
        api_key = create_user(client)
        
        # Get the user UUID
        with app.app_context():
            user = User.query.first()
            user_uuid = user.uuid
        
        # Delete the user
        response = client.delete(
            f"/api/users/{user_uuid}",
            headers=get_auth_headers(api_key)
        )
        assert response.status_code == 204
        
        # Verify user is deleted
        with app.app_context():
            deleted_user = User.query.first()
            assert deleted_user is None
    
    def test_delete_without_auth(self, client):
        """Test DELETE /api/users/<user_id> without auth - Should return 403 Forbidden"""
        # Create a user
        create_user(client)
        
        # Get the user UUID
        with app.app_context():
            user = User.query.first()
            user_uuid = user.uuid
        
        # Try to delete without authentication
        response = client.delete(f"/api/users/{user_uuid}")
        assert response.status_code == 403

class TestGroupEndpoints:
    """Test cases for Group-related endpoints"""
    
    def test_get_groups(self, client):
        """Test GET /api/groups/ - Should return list of groups"""
        # Create a user and group first
        api_key = create_user(client)
        
        # Create a group via API
        group_data = {
            "name": "Test Group",
            "description": "API-created group"
        }
        client.post(
            "/api/groups/",
            data=json.dumps(group_data),
            headers=get_auth_headers(api_key)
        )
        
        # Get all groups
        response = client.get("/api/groups/")
        assert response.status_code == 200
        data = json.loads(response.data)
        assert "groups" in data
        assert len(data["groups"]) == 1
        assert data["groups"][0]["name"] == "Test Group"
    
    def test_create_group_authenticated(self, client):
        """Test POST /api/groups/ with valid auth - Should create a new group"""
        # Create a user first
        api_key = create_user(client)
        
        # Create a group
        group_data = {"name": "New Group", "description": "Test description"}
        response = client.post(
            "/api/groups/",
            data=json.dumps(group_data),
            headers=get_auth_headers(api_key)
        )
        assert response.status_code == 201
        data = json.loads(response.data)
        assert data["group"]["name"] == "New Group"
        assert data["group"]["description"] == "Test description"
        
        # Verify the creator was automatically added as admin
        with app.app_context():
            group = Group.query.first()
            member = GroupMember.query.filter_by(group_id=group.id).first()
            assert member is not None
            assert member.role == "admin"
    
    def test_create_group_unauthenticated(self, client):
        """Test POST /api/groups/ without auth - Should return 403 Forbidden"""
        group_data = {"name": "Unauthorized Group"}
        response = client.post(
            "/api/groups/",
            data=json.dumps(group_data),
            content_type="application/json"
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
            headers=get_auth_headers(api_key)
        )
        assert response.status_code == 400
    
    def test_get_specific_group(self, client):
        """Test GET /api/groups/<group_id> - Should return group details"""
        # Create a user and group first
        api_key = create_user(client)
        
        # Create a group via API
        group_data = {
            "name": "Test Group",
            "description": "Group description"
        }
        response = client.post(
            "/api/groups/",
            data=json.dumps(group_data),
            headers=get_auth_headers(api_key)
        )
        group_uuid = json.loads(response.data)["group"]["id"]
        
        # Get group details
        response = client.get(f"/api/groups/{group_uuid}")
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data["group"]["name"] == "Test Group"
    
    def test_update_group_as_admin(self, client):
        """Test PUT /api/groups/<group_id> as admin - Should update group info"""
        # Create a user first
        api_key = create_user(client)
        
        # Create a group via API
        group_data = {
            "name": "Original Name",
            "description": "Original description"
        }
        response = client.post(
            "/api/groups/",
            data=json.dumps(group_data),
            headers=get_auth_headers(api_key)
        )
        group_uuid = json.loads(response.data)["group"]["id"]
        
        # Update group
        update_data = {"name": "Updated Group", "description": "New description"}
        response = client.put(
            f"/api/groups/{group_uuid}",
            data=json.dumps(update_data),
            headers=get_auth_headers(api_key)
        )
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data["group"]["name"] == "Updated Group"
        assert data["group"]["description"] == "New description"
    
    def test_update_group_as_non_admin(self, client):
        """Test PUT /api/groups/<group_id> as non-admin - Should return 403 Forbidden"""
        # Create admin user and group
        admin_key = create_user(client, name="Admin", email="admin@example.com")
        
        # Create a group via API as admin
        group_data = {
            "name": "Admin Group",
            "description": "Admin-created group"
        }
        response = client.post(
            "/api/groups/",
            data=json.dumps(group_data),
            headers=get_auth_headers(admin_key)
        )
        group_uuid = json.loads(response.data)["group"]["id"]
        
        # Create another user (will be non-admin)
        member_key = create_user(client, name="Member", email="member@example.com")
        
        # Get the member user's UUID
        with app.app_context():
            member = User.query.filter_by(email="member@example.com").first()
            member_uuid = member.uuid
        
        # Add member to group as regular member
        member_data = {"user_id": member_uuid, "role": "member"}
        client.post(
            f"/api/groups/{group_uuid}/members/",
            data=json.dumps(member_data),
            headers=get_auth_headers(admin_key)
        )
        
        # Try to update group as non-admin
        update_data = {"name": "Unauthorized Update"}
        response = client.put(
            f"/api/groups/{group_uuid}",
            data=json.dumps(update_data),
            headers=get_auth_headers(member_key)
        )
        assert response.status_code == 403
        assert "admin" in json.loads(response.data)["message"]
    
    def test_delete_group_as_admin(self, client):
        """Test DELETE /api/groups/<group_id> as admin - Should delete group"""
        # Create a user first
        api_key = create_user(client)
        
        # Create a group via API
        group_data = {
            "name": "Group to Delete",
            "description": "This group will be deleted"
        }
        response = client.post(
            "/api/groups/",
            data=json.dumps(group_data),
            headers=get_auth_headers(api_key)
        )
        group_uuid = json.loads(response.data)["group"]["id"]
        
        # Delete group
        response = client.delete(
            f"/api/groups/{group_uuid}",
            headers=get_auth_headers(api_key)
        )
        assert response.status_code == 204
        
        # Verify group is deleted
        with app.app_context():
            deleted_group = Group.query.first()
            assert deleted_group is None

class TestGroupMemberEndpoints:
    """Test cases for GroupMember-related endpoints"""
    
    def test_get_group_members(self, client):
        """Test GET /api/groups/<group_id>/members/ - Should return list of members"""
        # Create a user and group first
        api_key = create_user(client)
        
        # Create a group via API
        group_data = {
            "name": "Member Test Group",
            "description": "Group for testing members"
        }
        response = client.post(
            "/api/groups/",
            data=json.dumps(group_data),
            headers=get_auth_headers(api_key)
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
            "description": "Group for testing member addition"
        }
        response = client.post(
            "/api/groups/",
            data=json.dumps(group_data),
            headers=get_auth_headers(admin_key)
        )
        group_uuid = json.loads(response.data)["group"]["id"]
        
        # Get the member user's UUID
        with app.app_context():
            member = User.query.filter_by(email="member@example.com").first()
            member_uuid = member.uuid
        
        # Add new member
        member_data = {"user_id": member_uuid, "role": "member"}
        response = client.post(
            f"/api/groups/{group_uuid}/members/",
            data=json.dumps(member_data),
            headers=get_auth_headers(admin_key)
        )
        assert response.status_code == 201
        
        # Verify member was added
        with app.app_context():
            group = Group.query.first()
            group_members = GroupMember.query.filter_by(group_id=group.id).all()
            assert len(group_members) == 2  # Admin + new member
    
    def test_add_member_as_non_admin(self, client):
        """Test POST /api/groups/<group_id>/members/ as non-admin - Should return 403 Forbidden"""
        # Create admin user
        admin_key = create_user(client, name="Admin", email="admin@example.com")
        
        # Create a regular member user
        member_key = create_user(client, name="Regular Member", email="member@example.com")
        
        # Create a user to be added
        create_user(client, name="New Person", email="new@example.com")
        
        # Create a group via API as admin
        group_data = {
            "name": "Admin Group",
            "description": "Group for testing member addition permissions"
        }
        response = client.post(
            "/api/groups/",
            data=json.dumps(group_data),
            headers=get_auth_headers(admin_key)
        )
        group_uuid = json.loads(response.data)["group"]["id"]
        
        # Get the member and new person UUIDs
        with app.app_context():
            member = User.query.filter_by(email="member@example.com").first()
            new_person = User.query.filter_by(email="new@example.com").first()
            member_uuid = member.uuid
            new_person_uuid = new_person.uuid
        
        # Add regular member to group
        member_data = {"user_id": member_uuid, "role": "member"}
        client.post(
            f"/api/groups/{group_uuid}/members/",
            data=json.dumps(member_data),
            headers=get_auth_headers(admin_key)
        )
        
        # Try to add new member as regular member
        add_data = {"user_id": new_person_uuid}
        response = client.post(
            f"/api/groups/{group_uuid}/members/",
            data=json.dumps(add_data),
            headers=get_auth_headers(member_key)
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
            "description": "Group for testing duplicate member addition"
        }
        response = client.post(
            "/api/groups/",
            data=json.dumps(group_data),
            headers=get_auth_headers(admin_key)
        )
        group_uuid = json.loads(response.data)["group"]["id"]
        
        # Get the member's UUID
        with app.app_context():
            member = User.query.filter_by(email="member@example.com").first()
            member_uuid = member.uuid
        
        # Add member to group
        member_data = {"user_id": member_uuid, "role": "member"}
        client.post(
            f"/api/groups/{group_uuid}/members/",
            data=json.dumps(member_data),
            headers=get_auth_headers(admin_key)
        )
        
        # Try to add same member again
        response = client.post(
            f"/api/groups/{group_uuid}/members/",
            data=json.dumps(member_data),
            headers=get_auth_headers(admin_key)
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
            "description": "Group for testing member removal"
        }
        response = client.post(
            "/api/groups/",
            data=json.dumps(group_data),
            headers=get_auth_headers(admin_key)
        )
        group_uuid = json.loads(response.data)["group"]["id"]
        
        # Get the member's UUID
        with app.app_context():
            member = User.query.filter_by(email="member@example.com").first()
            member_uuid = member.uuid
        
        # Add member to group
        member_data = {"user_id": member_uuid, "role": "member"}
        client.post(
            f"/api/groups/{group_uuid}/members/",
            data=json.dumps(member_data),
            headers=get_auth_headers(admin_key)
        )
        
        # Remove member
        response = client.delete(
            f"/api/groups/{group_uuid}/members/{member_uuid}",
            headers=get_auth_headers(admin_key)
        )
        assert response.status_code == 204
        
        # Verify member was removed
        with app.app_context():
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
            "description": "Group with only one admin"
        }
        response = client.post(
            "/api/groups/",
            data=json.dumps(group_data),
            headers=get_auth_headers(admin_key)
        )
        group_uuid = json.loads(response.data)["group"]["id"]
        
        # Get the admin's UUID
        with app.app_context():
            admin = User.query.filter_by(email="admin@example.com").first()
            admin_uuid = admin.uuid
        
        # Try to remove the only admin
        response = client.delete(
            f"/api/groups/{group_uuid}/members/{admin_uuid}",
            headers=get_auth_headers(admin_key)
        )
        assert response.status_code == 400
        assert "last admin" in json.loads(response.data)["message"]


class TestExpenseEndpoints:
    """Test cases for Expense-related endpoints"""
    
    def test_get_group_expenses(self, client):
        """Test GET /api/groups/<group_id>/expenses/ - Should return list of expenses"""
        # Create a user 
        api_key = create_user(client)
        
        # Create a group via API
        group_data = {
            "name": "Expense Group",
            "description": "Group for testing expenses"
        }
        response = client.post(
            "/api/groups/",
            data=json.dumps(group_data),
            headers=get_auth_headers(api_key)
        )
        group_uuid = json.loads(response.data)["group"]["id"]
        
        # Get user UUID
        with app.app_context():
            user = User.query.first()
            user_uuid = user.uuid
            
        # Create an expense
        expense_data = {
            "amount": 50.00,
            "description": "Test Expense",
            "participants": [
                {"user_id": user_uuid, "share": 50.00, "paid": 50.00}
            ]
        }
        client.post(
            f"/api/groups/{group_uuid}/expenses/",
            data=json.dumps(expense_data),
            headers=get_auth_headers(api_key)
        )
        
        # Get expenses
        response = client.get(f"/api/groups/{group_uuid}/expenses/")
        assert response.status_code == 200
        data = json.loads(response.data)
        assert "expenses" in data
        assert len(data["expenses"]) == 1
        assert data["expenses"][0]["description"] == "Test Expense"
        assert float(data["expenses"][0]["amount"]) == 50.00
    
    def test_create_expense_valid(self, client):
        """Test POST /api/groups/<group_id>/expenses/ with valid data - Should create expense"""
        # Create user
        api_key = create_user(client)
        
        # Create a group via API
        group_data = {
            "name": "Expense Group",
            "description": "Group for testing expense creation"
        }
        response = client.post(
            "/api/groups/",
            data=json.dumps(group_data),
            headers=get_auth_headers(api_key)
        )
        group_uuid = json.loads(response.data)["group"]["id"]
        
        # Get user UUID
        with app.app_context():
            user = User.query.first()
            user_uuid = user.uuid
        
        # Create expense with participant
        expense_data = {
            "amount": 100.00,
            "description": "Dinner",
            "category": "Food",
            "participants": [
                {"user_id": user_uuid, "share": 100.00, "paid": 100.00}
            ]
        }
        response = client.post(
            f"/api/groups/{group_uuid}/expenses/",
            data=json.dumps(expense_data),
            headers=get_auth_headers(api_key)
        )
        assert response.status_code == 201
        data = json.loads(response.data)
        assert data["expense"]["description"] == "Dinner"
        assert float(data["expense"]["amount"]) == 100.00
        
        # Verify expense and participant were created
        with app.app_context():
            expense = Expense.query.first()
            assert expense is not None
            assert expense.description == "Dinner"
            
            participant = ExpenseParticipant.query.first()
            assert participant is not None
            assert float(participant.share) == 100.00
            assert float(participant.paid) == 100.00
    
    def test_create_expense_non_member(self, client):
        """Test POST /api/groups/<group_id>/expenses/ as non-member - Should return 403 Forbidden"""
        # Create member user
        member_key = create_user(client, name="Member", email="member@example.com")
        
        # Create a non-member user
        non_member_key = create_user(client, name="Non-Member", email="nonmember@example.com")
        
        # Create a group via API as member
        group_data = {
            "name": "Member Group",
            "description": "Group for testing non-member expense creation"
        }
        response = client.post(
            "/api/groups/",
            data=json.dumps(group_data),
            headers=get_auth_headers(member_key)
        )
        group_uuid = json.loads(response.data)["group"]["id"]
        
        # Get non-member's UUID
        with app.app_context():
            non_member = User.query.filter_by(email="nonmember@example.com").first()
            non_member_uuid = non_member.uuid
        
        # Try to create expense as non-member
        expense_data = {
            "amount": 50.00,
            "description": "Unauthorized Expense",
            "participants": [
                {"user_id": non_member_uuid, "share": 50.00, "paid": 50.00}
            ]
        }
        response = client.post(
            f"/api/groups/{group_uuid}/expenses/",
            data=json.dumps(expense_data),
            headers=get_auth_headers(non_member_key)
        )
        assert response.status_code == 403
        assert "members" in json.loads(response.data)["message"]
    
    def test_create_expense_invalid_shares(self, client):
        """Test POST /api/groups/<group_id>/expenses/ with mismatched shares - Should return 400 Bad Request"""
        # Create user
        api_key = create_user(client)
        
        # Create a group via API
        group_data = {
            "name": "Expense Group",
            "description": "Group for testing invalid expense shares"
        }
        response = client.post(
            "/api/groups/",
            data=json.dumps(group_data),
            headers=get_auth_headers(api_key)
        )
        group_uuid = json.loads(response.data)["group"]["id"]
        
        # Get user UUID
        with app.app_context():
            user = User.query.first()
            user_uuid = user.uuid
        
        # Create expense with incorrect shares
        expense_data = {
            "amount": 100.00,
            "description": "Invalid Shares",
            "participants": [
                {"user_id": user_uuid, "share": 50.00, "paid": 100.00}  # Share doesn't match amount
            ]
        }
        response = client.post(
            f"/api/groups/{group_uuid}/expenses/",
            data=json.dumps(expense_data),
            headers=get_auth_headers(api_key)
        )
        assert response.status_code == 400
        assert "shares" in json.loads(response.data)["message"]
        assert "expense amount" in json.loads(response.data)["message"]
    
    def test_get_expense_details(self, client):
        """Test GET /api/expenses/<expense_id> - Should return expense details"""
        # Create user
        api_key = create_user(client)
        
        # Create a group via API
        group_data = {
            "name": "Expense Group",
            "description": "Group for testing expense details"
        }
        response = client.post(
            "/api/groups/",
            data=json.dumps(group_data),
            headers=get_auth_headers(api_key)
        )
        group_uuid = json.loads(response.data)["group"]["id"]
        
        # Get user UUID
        with app.app_context():
            user = User.query.first()
            user_uuid = user.uuid
        
        # Create expense
        expense_data = {
            "amount": 75.50,
            "description": "Detailed Expense",
            "category": "Entertainment",
            "participants": [
                {"user_id": user_uuid, "share": 75.50, "paid": 75.50}
            ]
        }
        response = client.post(
            f"/api/groups/{group_uuid}/expenses/",
            data=json.dumps(expense_data),
            headers=get_auth_headers(api_key)
        )
        expense_uuid = json.loads(response.data)["expense"]["id"]
        
        # Get expense details
        response = client.get(f"/api/expenses/{expense_uuid}")
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data["expense"]["description"] == "Detailed Expense"
        assert float(data["expense"]["amount"]) == 75.50
        assert data["expense"]["category"] == "Entertainment"
    
    def test_update_expense_creator(self, client):
        """Test PUT /api/expenses/<expense_id> as creator - Should update expense"""
        # Create user
        api_key = create_user(client)
        
        # Create a group via API
        group_data = {
            "name": "Expense Group",
            "description": "Group for testing expense updates"
        }
        response = client.post(
            "/api/groups/",
            data=json.dumps(group_data),
            headers=get_auth_headers(api_key)
        )
        group_uuid = json.loads(response.data)["group"]["id"]
        
        # Get user UUID
        with app.app_context():
            user = User.query.first()
            user_uuid = user.uuid
        
        # Create expense
        expense_data = {
            "amount": 50.00,
            "description": "Original Expense",
            "participants": [
                {"user_id": user_uuid, "share": 50.00, "paid": 50.00}
            ]
        }
        response = client.post(
            f"/api/groups/{group_uuid}/expenses/",
            data=json.dumps(expense_data),
            headers=get_auth_headers(api_key)
        )
        expense_uuid = json.loads(response.data)["expense"]["id"]
        
        # Update expense
        update_data = {
            "amount": 75.00,
            "description": "Updated Expense",
            "category": "Updated Category"
        }
        response = client.put(
            f"/api/expenses/{expense_uuid}",
            data=json.dumps(update_data),
            headers=get_auth_headers(api_key)
        )
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data["expense"]["description"] == "Updated Expense"
        assert float(data["expense"]["amount"]) == 75.00
        
        # Verify expense was updated
        with app.app_context():
            updated_expense = Expense.query.first()
            assert updated_expense.description == "Updated Expense"
            assert float(updated_expense.amount) == 75.00
    
    def test_update_expense_unauthorized(self, client):
        """Test PUT /api/expenses/<expense_id> as non-creator - Should return 403 Forbidden"""
        # Create creator user
        creator_key = create_user(client, name="Creator", email="creator@example.com")
        
        # Create another user
        other_key = create_user(client, name="Other User", email="other@example.com")
        
        # Create a group via API
        group_data = {
            "name": "Shared Group",
            "description": "Group for testing expense update permissions"
        }
        response = client.post(
            "/api/groups/",
            data=json.dumps(group_data),
            headers=get_auth_headers(creator_key)
        )
        group_uuid = json.loads(response.data)["group"]["id"]
        
        # Get user UUIDs
        with app.app_context():
            creator = User.query.filter_by(email="creator@example.com").first()
            other_user = User.query.filter_by(email="other@example.com").first()
            creator_uuid = creator.uuid
            other_uuid = other_user.uuid
        
        # Add other user to group
        member_data = {"user_id": other_uuid, "role": "member"}
        client.post(
            f"/api/groups/{group_uuid}/members/",
            data=json.dumps(member_data),
            headers=get_auth_headers(creator_key)
        )
        
        # Create expense as creator
        expense_data = {
            "amount": 60.00,
            "description": "Creator's Expense",
            "participants": [
                {"user_id": creator_uuid, "share": 60.00, "paid": 60.00}
            ]
        }
        response = client.post(
            f"/api/groups/{group_uuid}/expenses/",
            data=json.dumps(expense_data),
            headers=get_auth_headers(creator_key)
        )
        expense_uuid = json.loads(response.data)["expense"]["id"]
        
        # Try to update as non-creator
        update_data = {"description": "Unauthorized Update"}
        response = client.put(
            f"/api/expenses/{expense_uuid}",
            data=json.dumps(update_data),
            headers=get_auth_headers(other_key)
        )
        assert response.status_code == 403
        assert "creator" in json.loads(response.data)["message"]
    
    def test_delete_expense_creator(self, client):
        """Test DELETE /api/expenses/<expense_id> as creator - Should delete expense"""
        # Create user
        api_key = create_user(client)
        
        # Create a group via API
        group_data = {
            "name": "Expense Group",
            "description": "Group for testing expense deletion"
        }
        response = client.post(
            "/api/groups/",
            data=json.dumps(group_data),
            headers=get_auth_headers(api_key)
        )
        group_uuid = json.loads(response.data)["group"]["id"]
        
        # Get user UUID
        with app.app_context():
            user = User.query.first()
            user_uuid = user.uuid
        
        # Create expense
        expense_data = {
            "amount": 100.00,
            "description": "Expense to Delete",
            "participants": [
                {"user_id": user_uuid, "share": 100.00, "paid": 100.00}
            ]
        }
        response = client.post(
            f"/api/groups/{group_uuid}/expenses/",
            data=json.dumps(expense_data),
            headers=get_auth_headers(api_key)
        )
        expense_uuid = json.loads(response.data)["expense"]["id"]
        
        # Delete expense
        response = client.delete(
            f"/api/expenses/{expense_uuid}",
            headers=get_auth_headers(api_key)
        )
        assert response.status_code == 204
        
        # Verify expense was deleted
        with app.app_context():
            deleted_expense = Expense.query.first()
            assert deleted_expense is None
    
    def test_delete_expense_as_admin(self, client):
        """Test DELETE /api/expenses/<expense_id> as group admin - Should delete expense"""
        # Create admin user
        admin_key = create_user(client, name="Admin", email="admin@example.com")
        
        # Create member user
        member_key = create_user(client, name="Member", email="member@example.com")
        
        # Create a group via API as admin
        group_data = {
            "name": "Admin Group",
            "description": "Group for testing admin expense deletion"
        }
        response = client.post(
            "/api/groups/",
            data=json.dumps(group_data),
            headers=get_auth_headers(admin_key)
        )
        group_uuid = json.loads(response.data)["group"]["id"]
        
        # Get user UUIDs
        with app.app_context():
            admin = User.query.filter_by(email="admin@example.com").first()
            member = User.query.filter_by(email="member@example.com").first()
            admin_uuid = admin.uuid
            member_uuid = member.uuid
        
        # Add member to group
        member_data = {"user_id": member_uuid, "role": "member"}
        client.post(
            f"/api/groups/{group_uuid}/members/",
            data=json.dumps(member_data),
            headers=get_auth_headers(admin_key)
        )
        
        # Create expense as member
        expense_data = {
            "amount": 30.00,
            "description": "Member's Expense",
            "participants": [
                {"user_id": member_uuid, "share": 30.00, "paid": 30.00}
            ]
        }
        response = client.post(
            f"/api/groups/{group_uuid}/expenses/",
            data=json.dumps(expense_data),
            headers=get_auth_headers(member_key)
        )
        expense_uuid = json.loads(response.data)["expense"]["id"]
        
        # Delete expense as admin (not creator)
        response = client.delete(
            f"/api/expenses/{expense_uuid}",
            headers=get_auth_headers(admin_key)
        )
        assert response.status_code == 204
        
        # Verify expense was deleted
        with app.app_context():
            deleted_expense = Expense.query.first()
            assert deleted_expense is None

class TestExpenseParticipantEndpoints:
    """Test cases for ExpenseParticipant-related endpoints"""
    
    def test_get_expense_participants(self, client):
        """Test GET /api/expenses/<expense_id>/participants/ - Should return list of participants"""
        # Create user
        api_key = create_user(client)
        
        # Create a group via API
        group_data = {
            "name": "Participant Group",
            "description": "Group for testing expense participants"
        }
        response = client.post(
            "/api/groups/",
            data=json.dumps(group_data),
            headers=get_auth_headers(api_key)
        )
        group_uuid = json.loads(response.data)["group"]["id"]
        
        # Get user UUID
        with app.app_context():
            user = User.query.first()
            user_uuid = user.uuid
        
        # Create expense with participant
        expense_data = {
            "amount": 120.00,
            "description": "Shared Expense",
            "participants": [
                {"user_id": user_uuid, "share": 120.00, "paid": 120.00}
            ]
        }
        response = client.post(
            f"/api/groups/{group_uuid}/expenses/",
            data=json.dumps(expense_data),
            headers=get_auth_headers(api_key)
        )
        expense_uuid = json.loads(response.data)["expense"]["id"]
        
        # Get participants
        response = client.get(f"/api/expenses/{expense_uuid}/participants/")
        assert response.status_code == 200
        data = json.loads(response.data)
        assert "participants" in data
        assert len(data["participants"]) == 1
        assert float(data["participants"][0]["share"]) == 120.00
        assert float(data["participants"][0]["paid"]) == 120.00

if __name__ == "__main__":
    pytest.main()