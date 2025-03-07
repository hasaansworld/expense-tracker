"""
Common test fixtures and utilities for the Expenses API tests.

This module contains shared fixtures and helper functions used
across multiple test files for the Expenses application.
"""

import json
import pytest

from expenses import create_app
from expenses.models import db

# Create application with test configuration
app = create_app({"TESTING": True})


@pytest.fixture(name="client")
def fixture_client():
    """
    Configure a test client with an in-memory database for testing.
    This fixture is accessible to all test modules that import from conftest.
    """
    # Save original config to restore it later
    original_db_uri = app.config["SQLALCHEMY_DATABASE_URI"]
    original_testing = app.config.get("TESTING", False)

    # Configure for testing with in-memory SQLite database
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///:memory:"
    app.config["TESTING"] = True
    app.config["CACHE_TYPE"] = "NullCache"  # Disable caching for tests

    with app.test_client() as test_client:
        with app.app_context():
            db.create_all()
            yield test_client
            db.session.remove()
            db.drop_all()

    # Restore original configuration
    app.config["SQLALCHEMY_DATABASE_URI"] = original_db_uri
    app.config["TESTING"] = original_testing


def create_user(test_client, name="Test User", email="test@example.com"):
    """
    Helper function to create a user and return the API key.

    Args:
        test_client: Flask test client
        name: User's full name
        email: User's email address

    Returns:
        API key string for the created user
    """
    user_data = {"name": name, "email": email, "password_hash": "securepassword"}
    response = test_client.post(
        "/api/users/", data=json.dumps(user_data), content_type="application/json"
    )
    return json.loads(response.data)["api_key"]


def get_auth_headers(api_key):
    """
    Helper to generate headers with API key for authenticated requests.

    Args:
        api_key: The API key to include in the headers

    Returns:
        Dictionary with Content-Type and X-API-Key headers
    """
    return {"Content-Type": "application/json", "X-API-Key": api_key}


@pytest.fixture(name="app_context")
def app_context():
    """Provides an application context for tests that need direct DB access."""
    with app.app_context() as context:
        yield context


"""
Additional pytest fixtures for testing expense-related endpoints.

This module provides helper fixtures to simplify and improve
the expense and expense participant test modules.
"""

import pytest
from flask import Flask
import json

from expenses.models import db, User, Group, GroupMember, Expense, ExpenseParticipant
from tests.conftest import create_user, get_auth_headers


@pytest.fixture
def setup_group_with_members(client):
    """
    Set up a group with admin and two members.

    Returns:
        tuple: (admin_key, member1_key, member2_key, group_uuid, user_uuids)
            - admin_key: API key for admin user
            - member1_key: API key for first member
            - member2_key: API key for second member
            - group_uuid: UUID of created group
            - user_uuids: Dict mapping role to user UUID
    """
    admin_key = create_user(client, name="Admin", email="admin@example.com")
    member1_key = create_user(client, name="Member1", email="member1@example.com")
    member2_key = create_user(client, name="Member2", email="member2@example.com")

    # Create group as admin
    group_data = {"name": "Test Group", "description": "Group for testing expenses"}
    response = client.post(
        "/api/groups/", data=json.dumps(group_data), headers=get_auth_headers(admin_key)
    )
    group_uuid = json.loads(response.data)["group"]["id"]

    # Get user UUIDs
    admin = User.query.filter_by(email="admin@example.com").first()
    member1 = User.query.filter_by(email="member1@example.com").first()
    member2 = User.query.filter_by(email="member2@example.com").first()

    admin_uuid = admin.uuid
    member1_uuid = member1.uuid
    member2_uuid = member2.uuid

    # Add members to the group
    for member_uuid in [member1_uuid, member2_uuid]:
        member_data = {"user_id": member_uuid, "role": "member"}
        client.post(
            f"/api/groups/{group_uuid}/members/",
            data=json.dumps(member_data),
            headers=get_auth_headers(admin_key),
        )

    user_uuids = {"admin": admin_uuid, "member1": member1_uuid, "member2": member2_uuid}

    return admin_key, member1_key, member2_key, group_uuid, user_uuids


@pytest.fixture
def create_test_expense(client, setup_group_with_members):
    """
    Create a test expense with specified participants.

    Args:
        client: Flask test client
        setup_group_with_members: Fixture with group and member info

    Returns:
        function: Function to create expense with specified parameters
    """
    admin_key, _, _, group_uuid, user_uuids = setup_group_with_members

    def _create_expense(amount=100.00, description="Test Expense", participants=None):
        """
        Create an expense with given parameters.

        Args:
            amount: Expense amount
            description: Expense description
            participants: List of participant dicts with user_id, share, and paid fields
                          If None, defaults to admin paying everything

        Returns:
            str: UUID of created expense
        """
        if participants is None:
            participants = [
                {"user_id": user_uuids["admin"], "share": amount, "paid": amount}
            ]

        expense_data = {
            "amount": amount,
            "description": description,
            "participants": participants,
        }

        response = client.post(
            f"/api/groups/{group_uuid}/expenses/",
            data=json.dumps(expense_data),
            headers=get_auth_headers(admin_key),
        )

        assert response.status_code == 201
        return json.loads(response.data)["expense"]["id"]

    return _create_expense


@pytest.fixture
def mock_cache(mocker):
    """Mock the cache functions for tests."""
    mock_cached = mocker.patch("expenses.cache.cached", return_value=lambda f: f)
    mock_delete = mocker.patch("expenses.cache.delete")

    return {"cached": mock_cached, "delete": mock_delete}
