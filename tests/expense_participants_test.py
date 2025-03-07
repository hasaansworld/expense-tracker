"""
Tests for ExpenseParticipant-related API endpoints.

This module contains test cases for the expense participant features
including retrieving participants and managing participant details.
"""

import json

from expenses.models import User, Expense, ExpenseParticipant
from tests.conftest import create_user, get_auth_headers


class TestExpenseParticipantEndpoints:
    """Test cases for ExpenseParticipant-related endpoints"""

    def test_get_expense_participants(self, client):
        """Test GET /api/expenses/<expense_id>/participants/ - Should return list of participants"""
        # Create user
        api_key = create_user(client)

        # Create a group via API
        group_data = {
            "name": "Participant Group",
            "description": "Group for testing expense participants",
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
            "amount": 120.00,
            "description": "Shared Expense",
            "participants": [{"user_id": user_uuid, "share": 120.00, "paid": 120.00}],
        }
        response = client.post(
            f"/api/groups/{group_uuid}/expenses/",
            data=json.dumps(expense_data),
            headers=get_auth_headers(api_key),
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

    def test_update_participant_share(self, client):
        """Test updating a participant's share amount"""
        # Create a user
        api_key = create_user(client)

        # Create a group
        group_data = {
            "name": "Update Test Group",
            "description": "Testing participant updates",
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
            "amount": 50.00,
            "description": "Expense for participant update",
            "participants": [{"user_id": user_uuid, "share": 50.00, "paid": 50.00}],
        }
        response = client.post(
            f"/api/groups/{group_uuid}/expenses/",
            data=json.dumps(expense_data),
            headers=get_auth_headers(api_key),
        )
        expense_uuid = json.loads(response.data)["expense"]["id"]

        # Get participant ID
        expense = Expense.query.first()
        participant = ExpenseParticipant.query.filter_by(expense_id=expense.id).first()
        participant_id = participant.id

        # Update participant's share
        update_data = {"share": 40.00}
        response = client.put(
            f"/api/expenses/{expense_uuid}/participants/{participant_id}",
            data=json.dumps(update_data),
            headers=get_auth_headers(api_key),
        )

    def test_add_participant_to_expense(self, client):
        """Test adding a new participant to an existing expense"""
        # Create two users
        admin_key = create_user(client, name="Admin", email="admin@example.com")
        create_user(client, name="Member", email="member@example.com")

        # Create a group
        group_data = {"name": "Multiple Participants Group"}
        response = client.post(
            "/api/groups/",
            data=json.dumps(group_data),
            headers=get_auth_headers(admin_key),
        )
        group_uuid = json.loads(response.data)["group"]["id"]

        # Get user UUIDs
        admin = User.query.filter_by(email="admin@example.com").first()
        member = User.query.filter_by(email="member@example.com").first()
        admin_uuid = admin.uuid
        member_uuid = member.uuid

        # Add member to group
        member_data = {"user_id": member_uuid, "role": "member"}
        client.post(
            f"/api/groups/{group_uuid}/members/",
            data=json.dumps(member_data),
            headers=get_auth_headers(admin_key),
        )

        expense_data = {
            "amount": 100.00,
            "description": "Group Dinner",
            "participants": [{"user_id": admin_uuid, "share": 100.00, "paid": 100.00}],
        }
        response = client.post(
            f"/api/groups/{group_uuid}/expenses/",
            data=json.dumps(expense_data),
            headers=get_auth_headers(admin_key),
        )
        expense_uuid = json.loads(response.data)["expense"]["id"]

        new_participant_data = {"user_id": member_uuid, "share": 50.00, "paid": 0.00}

        response = client.post(
            f"/api/expenses/{expense_uuid}/participants/",
            data=json.dumps(new_participant_data),
            headers=get_auth_headers(admin_key),
        )

    def test_get_participants_nonexistent_expense(self, client):
        """Test GET /api/expenses/<nonexistent_id>/participants/ - Should return appropriate error"""
        response = client.get(
            "/api/expenses/00000000-0000-0000-0000-000000000000/participants/"
        )
        assert response.status_code in [
            404,
            400,
        ]  # Either is acceptable depending on implementation

    def test_add_multiple_participants(self, client):
        """Test multiple participants in an expense - Should properly handle all participants"""
        # Create users
        admin_key = create_user(client, name="Admin", email="admin@example.com")
        create_user(client, name="Member1", email="member1@example.com")
        create_user(client, name="Member2", email="member2@example.com")

        # Create a group
        group_data = {"name": "Multi-Participant Group"}
        response = client.post(
            "/api/groups/",
            data=json.dumps(group_data),
            headers=get_auth_headers(admin_key),
        )
        group_uuid = json.loads(response.data)["group"]["id"]

        # Get user UUIDs
        admin = User.query.filter_by(email="admin@example.com").first()
        member1 = User.query.filter_by(email="member1@example.com").first()
        member2 = User.query.filter_by(email="member2@example.com").first()
        admin_uuid = admin.uuid
        member1_uuid = member1.uuid
        member2_uuid = member2.uuid

        # Add members to group
        for member_uuid in [member1_uuid, member2_uuid]:
            member_data = {"user_id": member_uuid, "role": "member"}
            client.post(
                f"/api/groups/{group_uuid}/members/",
                data=json.dumps(member_data),
                headers=get_auth_headers(admin_key),
            )

        # Create expense with multiple participants
        expense_data = {
            "amount": 150.00,
            "description": "Group Dinner",
            "participants": [
                {"user_id": admin_uuid, "share": 50.00, "paid": 150.00},
                {"user_id": member1_uuid, "share": 50.00, "paid": 0.00},
                {"user_id": member2_uuid, "share": 50.00, "paid": 0.00},
            ],
        }
        response = client.post(
            f"/api/groups/{group_uuid}/expenses/",
            data=json.dumps(expense_data),
            headers=get_auth_headers(admin_key),
        )
        expense_uuid = json.loads(response.data)["expense"]["id"]

        # Get participants
        response = client.get(f"/api/expenses/{expense_uuid}/participants/")
        assert response.status_code == 200
        data = json.loads(response.data)
        assert "participants" in data
        assert len(data["participants"]) == 3

        # Verify each participant's share and payment
        participants = data["participants"]
        admin_participant = next(
            p for p in participants if p["user_id"] == str(admin_uuid)
        )
        member1_participant = next(
            p for p in participants if p["user_id"] == str(member1_uuid)
        )
        member2_participant = next(
            p for p in participants if p["user_id"] == str(member2_uuid)
        )

        assert float(admin_participant["share"]) == 50.00
        assert float(admin_participant["paid"]) == 150.00
        assert float(member1_participant["share"]) == 50.00
        assert float(member1_participant["paid"]) == 0.00
        assert float(member2_participant["share"]) == 50.00
        assert float(member2_participant["paid"]) == 0.00

    def test_expense_participant_balance_calculation(self, client):
        """Test balance calculation for participants - Should correctly calculate balances"""
        # Create users
        admin_key = create_user(client, name="Admin", email="admin@example.com")
        create_user(client, name="Member", email="member@example.com")

        # Create a group
        group_data = {"name": "Balance Test Group"}
        response = client.post(
            "/api/groups/",
            data=json.dumps(group_data),
            headers=get_auth_headers(admin_key),
        )
        group_uuid = json.loads(response.data)["group"]["id"]

        # Get user UUIDs
        admin = User.query.filter_by(email="admin@example.com").first()
        member = User.query.filter_by(email="member@example.com").first()
        admin_uuid = admin.uuid
        member_uuid = member.uuid

        # Add member to group
        member_data = {"user_id": member_uuid, "role": "member"}
        client.post(
            f"/api/groups/{group_uuid}/members/",
            data=json.dumps(member_data),
            headers=get_auth_headers(admin_key),
        )

        # Create expense where admin paid everything
        expense_data = {
            "amount": 100.00,
            "description": "Shared Expense",
            "participants": [
                {"user_id": admin_uuid, "share": 50.00, "paid": 100.00},
                {"user_id": member_uuid, "share": 50.00, "paid": 0.00},
            ],
        }
        response = client.post(
            f"/api/groups/{group_uuid}/expenses/",
            data=json.dumps(expense_data),
            headers=get_auth_headers(admin_key),
        )
        expense_uuid = json.loads(response.data)["expense"]["id"]

        # Get participants to check balances
        response = client.get(f"/api/expenses/{expense_uuid}/participants/")
        participants_data = json.loads(response.data)

        # If balance is included in the response, verify it's correct
        # Otherwise, manually calculate and verify
        admin_participant = next(
            p
            for p in participants_data["participants"]
            if p["user_id"] == str(admin_uuid)
        )
        member_participant = next(
            p
            for p in participants_data["participants"]
            if p["user_id"] == str(member_uuid)
        )

        # Calculate expected balances
        admin_balance = float(admin_participant["paid"]) - float(
            admin_participant["share"]
        )
        member_balance = float(member_participant["paid"]) - float(
            member_participant["share"]
        )

        assert admin_balance == 50.00  # Admin paid 50 more than their share
        assert member_balance == -50.00  # Member owes 50

        # If balance is in the API response, uncomment and adjust these assertions
        # assert float(admin_participant["balance"]) == 50.00
        # assert float(member_participant["balance"]) == -50.00

    def test_update_expense_with_invalid_participant_schema(self, client):
        """Test PUT /api/expenses/<expense_id> with invalid participant schema - Should return 400"""
        # Create user
        api_key = create_user(client)

        # Create a group via API
        group_data = {"name": "Validation Test Group"}
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
            "description": "Test Expense",
            "participants": [{"user_id": user_uuid, "share": 100.00, "paid": 100.00}],
        }
        response = client.post(
            f"/api/groups/{group_uuid}/expenses/",
            data=json.dumps(expense_data),
            headers=get_auth_headers(api_key),
        )
        expense_uuid = json.loads(response.data)["expense"]["id"]

        # Update with invalid participant data (missing required field)
        update_data = {
            "amount": 100.00,
            "participants": [
                # Missing "share" field which should be required
                {"user_id": user_uuid, "paid": 100.00}
            ],
        }
        response = client.put(
            f"/api/expenses/{expense_uuid}",
            data=json.dumps(update_data),
            headers=get_auth_headers(api_key),
        )
        assert response.status_code == 400
        assert "validation error" in json.loads(response.data)["message"].lower()

    def test_expense_with_zero_participants(self, client):
        """Test POST /api/groups/<group_id>/expenses/ with no participants - Should behave appropriately"""
        # Create user
        api_key = create_user(client)

        # Create a group via API
        group_data = {"name": "Zero Participants Test"}
        response = client.post(
            "/api/groups/",
            data=json.dumps(group_data),
            headers=get_auth_headers(api_key),
        )
        group_uuid = json.loads(response.data)["group"]["id"]

        # Create expense without participants array
        expense_data = {
            "amount": 50.00,
            "description": "Expense without participants",
        }
        response = client.post(
            f"/api/groups/{group_uuid}/expenses/",
            data=json.dumps(expense_data),
            headers=get_auth_headers(api_key),
        )

        # The API might either accept this (201) or reject it (400)
        # Either behavior is valid depending on the implementation
        assert response.status_code in [201, 400]

        if response.status_code == 201:
            expense_uuid = json.loads(response.data)["expense"]["id"]

            # Get participants to verify
            response = client.get(f"/api/expenses/{expense_uuid}/participants/")
            assert response.status_code == 200
            data = json.loads(response.data)
            assert len(data["participants"]) == 0  # Should have no participants

    def test_partial_participants_update(self, client):
        """Test updating only some participant fields - Should correctly handle partial updates"""
        # Create user
        api_key = create_user(client)

        # Create a group via API
        group_data = {"name": "Partial Update Group"}
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
            "description": "Original Expense",
            "participants": [{"user_id": user_uuid, "share": 100.00, "paid": 0.00}],
        }
        response = client.post(
            f"/api/groups/{group_uuid}/expenses/",
            data=json.dumps(expense_data),
            headers=get_auth_headers(api_key),
        )
        expense_uuid = json.loads(response.data)["expense"]["id"]

        # Update only the 'paid' field of the participant
        update_data = {
            "participants": [{"user_id": user_uuid, "share": 100.00, "paid": 100.00}],
        }
        response = client.put(
            f"/api/expenses/{expense_uuid}",
            data=json.dumps(update_data),
            headers=get_auth_headers(api_key),
        )
        assert response.status_code == 200

        # Verify the update
        response = client.get(f"/api/expenses/{expense_uuid}/participants/")
        data = json.loads(response.data)
        participant = data["participants"][0]
        assert float(participant["share"]) == 100.00
        assert float(participant["paid"]) == 100.00

    def test_complex_split_expense(self, client):
        """Test creating expense with complex split among multiple participants"""
        # Create main user and two additional users
        admin_key = create_user(client, name="Admin", email="admin@example.com")
        create_user(client, name="User1", email="user1@example.com")
        create_user(client, name="User2", email="user2@example.com")

        # Create a group
        group_data = {"name": "Complex Split Group"}
        response = client.post(
            "/api/groups/",
            data=json.dumps(group_data),
            headers=get_auth_headers(admin_key),
        )
        group_uuid = json.loads(response.data)["group"]["id"]

        # Get user UUIDs
        admin = User.query.filter_by(email="admin@example.com").first()
        user1 = User.query.filter_by(email="user1@example.com").first()
        user2 = User.query.filter_by(email="user2@example.com").first()
        admin_uuid = admin.uuid
        user1_uuid = user1.uuid
        user2_uuid = user2.uuid

        # Add users to the group
        for user_uuid in [user1_uuid, user2_uuid]:
            member_data = {"user_id": user_uuid, "role": "member"}
            client.post(
                f"/api/groups/{group_uuid}/members/",
                data=json.dumps(member_data),
                headers=get_auth_headers(admin_key),
            )

        # Create complex expense with uneven split and different payment amounts
        expense_data = {
            "amount": 120.00,
            "description": "Complex Split Dinner",
            "category": "Food",
            "participants": [
                {
                    "user_id": admin_uuid,
                    "share": 50.00,
                    "paid": 90.00,
                },  # Admin paid most
                {
                    "user_id": user1_uuid,
                    "share": 40.00,
                    "paid": 30.00,
                },  # User1 paid some
                {
                    "user_id": user2_uuid,
                    "share": 30.00,
                    "paid": 0.00,
                },  # User2 paid nothing
            ],
        }
        response = client.post(
            f"/api/groups/{group_uuid}/expenses/",
            data=json.dumps(expense_data),
            headers=get_auth_headers(admin_key),
        )
        assert response.status_code == 201
        expense_uuid = json.loads(response.data)["expense"]["id"]

        # Get expense details to verify
        response = client.get(f"/api/expenses/{expense_uuid}")
        assert response.status_code == 200
        expense_data = json.loads(response.data)["expense"]
        assert float(expense_data["amount"]) == 120.00

        # Get participants to verify their shares and payments
        response = client.get(f"/api/expenses/{expense_uuid}/participants/")
        participants_data = json.loads(response.data)["participants"]

        # Verify each participant
        admin_participant = next(
            p for p in participants_data if p["user_id"] == str(admin_uuid)
        )
        user1_participant = next(
            p for p in participants_data if p["user_id"] == str(user1_uuid)
        )
        user2_participant = next(
            p for p in participants_data if p["user_id"] == str(user2_uuid)
        )

        assert float(admin_participant["share"]) == 50.00
        assert float(admin_participant["paid"]) == 90.00
        assert float(user1_participant["share"]) == 40.00
        assert float(user1_participant["paid"]) == 30.00
        assert float(user2_participant["share"]) == 30.00
        assert float(user2_participant["paid"]) == 0.00
