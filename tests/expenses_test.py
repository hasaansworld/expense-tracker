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
