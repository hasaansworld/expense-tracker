"""
Tests for Expense-related API endpoints.

This module contains test cases for the expense management features
including expense creation, retrieval, update, and deletion.
"""

import json

from expenses.models import User, Expense, ExpenseParticipant
from tests.conftest import create_user, get_auth_headers


class TestExpenseEndpoints:
    """Test cases for Expense-related endpoints"""

    def test_get_group_expenses(self, client):
        """Test GET /api/groups/<group_id>/expenses/ - Should return list of expenses"""
        # Create a user
        api_key = create_user(client)

        # Create a group via API
        group_data = {
            "name": "Expense Group",
            "description": "Group for testing expenses",
        }
        response = client.post(
            "/api/groups/",
            data=json.dumps(group_data),
            headers=get_auth_headers(api_key),
        )
        group_uuid = json.loads(response.data)["group"]["id"]

        # Get user UUID
        user = User.query.first()
        user_uuid = user.uuid

        # Create expense with participant
        expense_data = {
            "amount": 100.00,
            "description": "Dinner",
            "category": "Food",
            "participants": [{"user_id": user_uuid, "share": 100.00, "paid": 100.00}],
        }
        response = client.post(
            f"/api/groups/{group_uuid}/expenses/",
            data=json.dumps(expense_data),
            headers=get_auth_headers(api_key),
        )
        assert response.status_code == 201
        data = json.loads(response.data)
        assert data["expense"]["description"] == "Dinner"
        assert float(data["expense"]["amount"]) == 100.00

        # Verify expense and participant were created
        expense = Expense.query.first()
        assert expense is not None
        assert expense.description == "Dinner"

        participant = ExpenseParticipant.query.first()
        assert participant is not None
        assert float(participant.share) == 100.00
        assert float(participant.paid) == 100.00

    def test_create_expense_valid(self, client):
        """Test POST /api/groups/<group_id>/expenses/ with valid data - Should create expense"""
        # Create user
        api_key = create_user(client)

        # Create a group via API
        group_data = {
            "name": "Expense Group",
            "description": "Group for testing expense creation",
        }
        response = client.post(
            "/api/groups/",
            data=json.dumps(group_data),
            headers=get_auth_headers(api_key),
        )
        group_uuid = json.loads(response.data)["group"]["id"]

        # Get user UUID
        user = User.query.first()
        user_uuid = user.uuid

        # Create an expense
        expense_data = {
            "amount": 50.00,
            "description": "Test Expense",
            "participants": [{"user_id": user_uuid, "share": 50.00, "paid": 50.00}],
        }
        client.post(
            f"/api/groups/{group_uuid}/expenses/",
            data=json.dumps(expense_data),
            headers=get_auth_headers(api_key),
        )

        # Get expenses
        response = client.get(f"/api/groups/{group_uuid}/expenses/")
        assert response.status_code == 200
        data = json.loads(response.data)
        assert "expenses" in data
        assert len(data["expenses"]) == 1
        assert data["expenses"][0]["description"] == "Test Expense"
        assert float(data["expenses"][0]["amount"]) == 50.00

    def test_create_expense_non_member(self, client):
        """Test POST /api/groups/<group_id>/expenses/ as non-member - Should return 403 Forbidden"""
        # Create member user
        member_key = create_user(client, name="Member", email="member@example.com")

        # Create a non-member user
        non_member_key = create_user(
            client, name="Non-Member", email="nonmember@example.com"
        )

        # Create a group via API as member
        group_data = {
            "name": "Member Group",
            "description": "Group for testing non-member expense creation",
        }
        response = client.post(
            "/api/groups/",
            data=json.dumps(group_data),
            headers=get_auth_headers(member_key),
        )
        group_uuid = json.loads(response.data)["group"]["id"]

        # Get non-member's UUID
        non_member = User.query.filter_by(email="nonmember@example.com").first()
        non_member_uuid = non_member.uuid

        # Try to create expense as non-member
        expense_data = {
            "amount": 50.00,
            "description": "Unauthorized Expense",
            "participants": [
                {"user_id": non_member_uuid, "share": 50.00, "paid": 50.00}
            ],
        }
        response = client.post(
            f"/api/groups/{group_uuid}/expenses/",
            data=json.dumps(expense_data),
            headers=get_auth_headers(non_member_key),
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
            "description": "Group for testing invalid expense shares",
        }
        response = client.post(
            "/api/groups/",
            data=json.dumps(group_data),
            headers=get_auth_headers(api_key),
        )
        group_uuid = json.loads(response.data)["group"]["id"]

        # Get user UUID
        user = User.query.first()
        user_uuid = user.uuid

        # Create expense with incorrect shares
        expense_data = {
            "amount": 100.00,
            "description": "Invalid Shares",
            "participants": [
                {
                    "user_id": user_uuid,
                    "share": 50.00,  # Share doesn't match amount
                    "paid": 100.00,
                }
            ],
        }
        response = client.post(
            f"/api/groups/{group_uuid}/expenses/",
            data=json.dumps(expense_data),
            headers=get_auth_headers(api_key),
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
            "description": "Group for testing expense details",
        }
        response = client.post(
            "/api/groups/",
            data=json.dumps(group_data),
            headers=get_auth_headers(api_key),
        )
        group_uuid = json.loads(response.data)["group"]["id"]

        # Get user UUID
        user = User.query.first()
        user_uuid = user.uuid

        # Create expense
        expense_data = {
            "amount": 75.50,
            "description": "Detailed Expense",
            "category": "Entertainment",
            "participants": [{"user_id": user_uuid, "share": 75.50, "paid": 75.50}],
        }
        response = client.post(
            f"/api/groups/{group_uuid}/expenses/",
            data=json.dumps(expense_data),
            headers=get_auth_headers(api_key),
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
            "description": "Group for testing expense updates",
        }
        response = client.post(
            "/api/groups/",
            data=json.dumps(group_data),
            headers=get_auth_headers(api_key),
        )
        group_uuid = json.loads(response.data)["group"]["id"]

        # Get user UUID
        user = User.query.first()
        user_uuid = user.uuid

        # Create expense
        expense_data = {
            "amount": 50.00,
            "description": "Original Expense",
            "participants": [{"user_id": user_uuid, "share": 50.00, "paid": 50.00}],
        }
        response = client.post(
            f"/api/groups/{group_uuid}/expenses/",
            data=json.dumps(expense_data),
            headers=get_auth_headers(api_key),
        )
        expense_uuid = json.loads(response.data)["expense"]["id"]

        # Update expense
        update_data = {
            "amount": 75.00,
            "description": "Updated Expense",
            "category": "Updated Category",
        }
        response = client.put(
            f"/api/expenses/{expense_uuid}",
            data=json.dumps(update_data),
            headers=get_auth_headers(api_key),
        )
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data["expense"]["description"] == "Updated Expense"
        assert float(data["expense"]["amount"]) == 75.00

        # Verify expense was updated
        updated_expense = Expense.query.first()
        assert updated_expense.description == "Updated Expense"
        assert float(updated_expense.amount) == 75.00

    def test_delete_expense_creator(self, client):
        """Test DELETE /api/expenses/<expense_id> as creator - Should delete expense"""
        # Create user
        api_key = create_user(client)

        # Create a group via API
        group_data = {
            "name": "Expense Group",
            "description": "Group for testing expense deletion",
        }
        response = client.post(
            "/api/groups/",
            data=json.dumps(group_data),
            headers=get_auth_headers(api_key),
        )
        group_uuid = json.loads(response.data)["group"]["id"]

        # Get user UUID
        user = User.query.first()
        user_uuid = user.uuid

        # Create expense
        expense_data = {
            "amount": 100.00,
            "description": "Expense to Delete",
            "participants": [{"user_id": user_uuid, "share": 100.00, "paid": 100.00}],
        }
        response = client.post(
            f"/api/groups/{group_uuid}/expenses/",
            data=json.dumps(expense_data),
            headers=get_auth_headers(api_key),
        )
        expense_uuid = json.loads(response.data)["expense"]["id"]

        # Delete expense
        response = client.delete(
            f"/api/expenses/{expense_uuid}", headers=get_auth_headers(api_key)
        )
        assert response.status_code == 204

        # Verify expense was deleted
        deleted_expense = Expense.query.first()
        assert deleted_expense is None

    def test_expense_missing_required_fields(self, client):
        """Test POST /api/groups/<group_id>/expenses/ with missing fields - Should return 400"""
        # Create user
        api_key = create_user(client)

        # Create a group via API
        group_data = {"name": "Expense Group"}
        response = client.post(
            "/api/groups/",
            data=json.dumps(group_data),
            headers=get_auth_headers(api_key),
        )
        group_uuid = json.loads(response.data)["group"]["id"]

        # Create expense with missing required fields
        incomplete_data = {"description": "Missing Amount"}
        response = client.post(
            f"/api/groups/{group_uuid}/expenses/",
            data=json.dumps(incomplete_data),
            headers=get_auth_headers(api_key),
        )
        assert response.status_code == 400
        assert "Validation error" in json.loads(response.data)["message"]

    def test_expense_participant_nonexistent_user(self, client):
        """Test POST /api/groups/<group_id>/expenses/ with nonexistent user - Should return 400"""
        # Create user
        api_key = create_user(client)

        # Create a group via API
        group_data = {"name": "Expense Group"}
        response = client.post(
            "/api/groups/",
            data=json.dumps(group_data),
            headers=get_auth_headers(api_key),
        )
        group_uuid = json.loads(response.data)["group"]["id"]

        # Create expense with nonexistent user
        expense_data = {
            "amount": 100.00,
            "description": "Test Expense",
            "participants": [
                {
                    "user_id": "00000000-0000-0000-0000-000000000000",  # Nonexistent UUID
                    "share": 100.00,
                    "paid": 100.00,
                }
            ],
        }
        response = client.post(
            f"/api/groups/{group_uuid}/expenses/",
            data=json.dumps(expense_data),
            headers=get_auth_headers(api_key),
        )
        assert response.status_code == 400
        assert "does not exist" in json.loads(response.data)["message"]

    def test_expense_participant_non_group_member(self, client):
        """Test POST with participant who is not group member - Should return 400"""
        # Create two users
        group_creator_key = create_user(
            client, name="Creator", email="creator@example.com"
        )
        non_member_user = create_user(
            client, name="NonMember", email="nonmember@example.com"
        )

        # Create a group via API
        group_data = {"name": "Expense Group"}
        response = client.post(
            "/api/groups/",
            data=json.dumps(group_data),
            headers=get_auth_headers(group_creator_key),
        )
        group_uuid = json.loads(response.data)["group"]["id"]

        # Get non-member UUID
        non_member = User.query.filter_by(email="nonmember@example.com").first()
        non_member_uuid = non_member.uuid

        # Create expense with non-member participant
        expense_data = {
            "amount": 100.00,
            "description": "Test Expense",
            "participants": [
                {"user_id": non_member_uuid, "share": 100.00, "paid": 100.00}
            ],
        }
        response = client.post(
            f"/api/groups/{group_uuid}/expenses/",
            data=json.dumps(expense_data),
            headers=get_auth_headers(group_creator_key),
        )
        assert response.status_code == 400
        assert "not a member" in json.loads(response.data)["message"]

    def test_update_expense_non_creator(self, client):
        """Test PUT /api/expenses/<expense_id> as non-creator - Should return 403"""
        # Create two users
        creator_key = create_user(client, name="Creator", email="creator@example.com")
        other_user_key = create_user(
            client, name="OtherUser", email="other@example.com"
        )

        # Create a group via API
        group_data = {"name": "Expense Group"}
        response = client.post(
            "/api/groups/",
            data=json.dumps(group_data),
            headers=get_auth_headers(creator_key),
        )
        group_uuid = json.loads(response.data)["group"]["id"]

        # Get user UUIDs
        creator = User.query.filter_by(email="creator@example.com").first()
        other_user = User.query.filter_by(email="other@example.com").first()
        creator_uuid = creator.uuid
        other_user_uuid = other_user.uuid

        # Add other user to group
        member_data = {"user_id": other_user_uuid, "role": "member"}
        client.post(
            f"/api/groups/{group_uuid}/members/",
            data=json.dumps(member_data),
            headers=get_auth_headers(creator_key),
        )

        # Create expense as creator
        expense_data = {
            "amount": 100.00,
            "description": "Creator's Expense",
            "participants": [
                {"user_id": creator_uuid, "share": 100.00, "paid": 100.00}
            ],
        }
        response = client.post(
            f"/api/groups/{group_uuid}/expenses/",
            data=json.dumps(expense_data),
            headers=get_auth_headers(creator_key),
        )
        expense_uuid = json.loads(response.data)["expense"]["id"]

        # Try to update expense as other user
        update_data = {"description": "Unauthorized Update"}
        response = client.put(
            f"/api/expenses/{expense_uuid}",
            data=json.dumps(update_data),
            headers=get_auth_headers(other_user_key),
        )
        assert response.status_code == 403
        assert "Only the creator" in json.loads(response.data)["message"]

    def test_delete_expense_as_admin(self, client):
        """Test DELETE /api/expenses/<expense_id> as group admin - Should delete expense"""
        # Create two users
        creator_key = create_user(client, name="Creator", email="creator@example.com")
        admin_key = create_user(client, name="Admin", email="admin@example.com")

        # Create a group via API
        group_data = {"name": "Expense Group"}
        response = client.post(
            "/api/groups/",
            data=json.dumps(group_data),
            headers=get_auth_headers(creator_key),
        )
        group_uuid = json.loads(response.data)["group"]["id"]

        # Get user UUIDs
        creator = User.query.filter_by(email="creator@example.com").first()
        admin = User.query.filter_by(email="admin@example.com").first()
        creator_uuid = creator.uuid
        admin_uuid = admin.uuid

        # Add admin to group with admin role
        member_data = {"user_id": admin_uuid, "role": "admin"}
        client.post(
            f"/api/groups/{group_uuid}/members/",
            data=json.dumps(member_data),
            headers=get_auth_headers(creator_key),
        )

        # Create expense as creator
        expense_data = {
            "amount": 100.00,
            "description": "Expense for Admin Deletion",
            "participants": [
                {"user_id": creator_uuid, "share": 100.00, "paid": 100.00}
            ],
        }
        response = client.post(
            f"/api/groups/{group_uuid}/expenses/",
            data=json.dumps(expense_data),
            headers=get_auth_headers(creator_key),
        )
        expense_uuid = json.loads(response.data)["expense"]["id"]

        # Delete expense as admin
        response = client.delete(
            f"/api/expenses/{expense_uuid}", headers=get_auth_headers(admin_key)
        )
        assert response.status_code == 204

        # Verify expense was deleted
        deleted_expense = Expense.query.first()
        assert deleted_expense is None

    def test_delete_expense_unauthorized(self, client):
        """Test DELETE /api/expenses/<expense_id> as regular member - Should return 403"""
        # Create two users
        creator_key = create_user(client, name="Creator", email="creator@example.com")
        member_key = create_user(client, name="Member", email="member@example.com")

        # Create a group via API
        group_data = {"name": "Expense Group"}
        response = client.post(
            "/api/groups/",
            data=json.dumps(group_data),
            headers=get_auth_headers(creator_key),
        )
        group_uuid = json.loads(response.data)["group"]["id"]

        # Get user UUIDs
        creator = User.query.filter_by(email="creator@example.com").first()
        member = User.query.filter_by(email="member@example.com").first()
        creator_uuid = creator.uuid
        member_uuid = member.uuid

        # Add member to group with regular member role
        member_data = {"user_id": member_uuid, "role": "member"}
        client.post(
            f"/api/groups/{group_uuid}/members/",
            data=json.dumps(member_data),
            headers=get_auth_headers(creator_key),
        )

        # Create expense as creator
        expense_data = {
            "amount": 100.00,
            "description": "Expense for Unauthorized Deletion",
            "participants": [
                {"user_id": creator_uuid, "share": 100.00, "paid": 100.00}
            ],
        }
        response = client.post(
            f"/api/groups/{group_uuid}/expenses/",
            data=json.dumps(expense_data),
            headers=get_auth_headers(creator_key),
        )
        expense_uuid = json.loads(response.data)["expense"]["id"]

        # Try to delete expense as regular member
        response = client.delete(
            f"/api/expenses/{expense_uuid}", headers=get_auth_headers(member_key)
        )
        assert response.status_code == 403
        assert "creator or group admin" in json.loads(response.data)["message"]

    def test_update_expense_with_participants(self, client):
        """Test PUT /api/expenses/<expense_id> with updated participants - Should update expense"""
        # Create user
        api_key = create_user(client)

        # Create a group via API
        group_data = {"name": "Expense Group"}
        response = client.post(
            "/api/groups/",
            data=json.dumps(group_data),
            headers=get_auth_headers(api_key),
        )
        group_uuid = json.loads(response.data)["group"]["id"]

        # Get user UUID
        user = User.query.first()
        user_uuid = user.uuid

        # Create expense
        expense_data = {
            "amount": 50.00,
            "description": "Original Expense",
            "participants": [{"user_id": user_uuid, "share": 50.00, "paid": 50.00}],
        }
        response = client.post(
            f"/api/groups/{group_uuid}/expenses/",
            data=json.dumps(expense_data),
            headers=get_auth_headers(api_key),
        )
        expense_uuid = json.loads(response.data)["expense"]["id"]

        # Update expense with new amount and participants
        update_data = {
            "amount": 75.00,
            "description": "Updated Expense",
            "participants": [{"user_id": user_uuid, "share": 75.00, "paid": 75.00}],
        }
        response = client.put(
            f"/api/expenses/{expense_uuid}",
            data=json.dumps(update_data),
            headers=get_auth_headers(api_key),
        )
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data["expense"]["description"] == "Updated Expense"
        assert float(data["expense"]["amount"]) == 75.00

        # Get participants to verify update
        response = client.get(f"/api/expenses/{expense_uuid}/participants/")
        participants_data = json.loads(response.data)
        assert len(participants_data["participants"]) == 1
        assert float(participants_data["participants"][0]["share"]) == 75.00

    def test_update_expense_invalid_participant_data(self, client):
        """Test PUT /api/expenses/<expense_id> with invalid participant data - Should return 400"""
        # Create user
        api_key = create_user(client)

        # Create a group via API
        group_data = {"name": "Expense Group"}
        response = client.post(
            "/api/groups/",
            data=json.dumps(group_data),
            headers=get_auth_headers(api_key),
        )
        group_uuid = json.loads(response.data)["group"]["id"]

        # Get user UUID
        user = User.query.first()
        user_uuid = user.uuid

        # Create expense
        expense_data = {
            "amount": 100.00,
            "description": "Original Expense",
            "participants": [{"user_id": user_uuid, "share": 100.00, "paid": 100.00}],
        }
        response = client.post(
            f"/api/groups/{group_uuid}/expenses/",
            data=json.dumps(expense_data),
            headers=get_auth_headers(api_key),
        )
        expense_uuid = json.loads(response.data)["expense"]["id"]

        # Update expense with invalid participant data (negative share)
        update_data = {
            "amount": 100.00,
            "participants": [{"user_id": user_uuid, "share": -50.00, "paid": 100.00}],
        }
        response = client.put(
            f"/api/expenses/{expense_uuid}",
            data=json.dumps(update_data),
            headers=get_auth_headers(api_key),
        )
        assert response.status_code == 400
        assert "validation error" in json.loads(response.data)["message"].lower()

    def test_update_expense_participants_amount_mismatch(self, client):
        """Test PUT /api/expenses/<expense_id> with participant total not matching amount - Should return 400"""
        # Create user
        api_key = create_user(client)

        # Create a group via API
        group_data = {"name": "Expense Group"}
        response = client.post(
            "/api/groups/",
            data=json.dumps(group_data),
            headers=get_auth_headers(api_key),
        )
        group_uuid = json.loads(response.data)["group"]["id"]

        # Get user UUID
        user = User.query.first()
        user_uuid = user.uuid

        # Create expense
        expense_data = {
            "amount": 100.00,
            "description": "Original Expense",
            "participants": [{"user_id": user_uuid, "share": 100.00, "paid": 100.00}],
        }
        response = client.post(
            f"/api/groups/{group_uuid}/expenses/",
            data=json.dumps(expense_data),
            headers=get_auth_headers(api_key),
        )
        expense_uuid = json.loads(response.data)["expense"]["id"]

        # Update expense with mismatched shares
        update_data = {
            "amount": 100.00,
            "participants": [{"user_id": user_uuid, "share": 80.00, "paid": 100.00}],
        }
        response = client.put(
            f"/api/expenses/{expense_uuid}",
            data=json.dumps(update_data),
            headers=get_auth_headers(api_key),
        )
        assert response.status_code == 400
        assert "shares" in json.loads(response.data)["message"].lower()
        assert "expense amount" in json.loads(response.data)["message"].lower()
