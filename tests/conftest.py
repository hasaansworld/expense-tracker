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
