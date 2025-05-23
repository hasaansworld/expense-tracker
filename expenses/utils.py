"""
Utility functions and classes for the expense tracker application.

This module contains helper functions, decorators, and URL converters
that are used throughout the application.
"""

from flask import request, g
from werkzeug.exceptions import NotFound, Forbidden
from werkzeug.routing import BaseConverter

from expenses.models import User, ApiKey, Group, Expense


# Authentication helpers
def require_api_key(func):
    """
    Decorator to require API key for a resource method.

    Args:
        func: The function to decorate

    Returns:
        Function wrapper that checks for a valid API key
    """

    def wrapper(*args, **kwargs):
        api_key = request.headers.get("X-API-Key")
        if not api_key:
            raise Forbidden("API key is required")

        key_hash = ApiKey.get_hash(api_key)
        db_key = ApiKey.query.filter_by(key_hash=key_hash).first()

        if not db_key:
            raise Forbidden("Invalid API key")

        g.user_id = db_key.user_id
        return func(*args, **kwargs)

    return wrapper


class UserConverter(BaseConverter):
    """
    URL converter for User model.

    Converts between URL parameters and User objects.
    """

    def to_python(self, value):
        """
        Convert a UUID string from the URL to a User object.

        Args:
            value: UUID string from the URL

        Returns:
            User: The user object

        Raises:
            NotFound: If the user with the given UUID does not exist
        """
        user = User.query.filter_by(uuid=value).first()
        if not user:
            raise NotFound(f"User {value} does not exist")
        return user

    def to_url(self, value):
        """
        Convert a User object to a string for URL generation.

        Args:
            value: User object or string UUID

        Returns:
            str: UUID string for the URL
        """
        return value.uuid if isinstance(value, User) else str(value)


class GroupConverter(BaseConverter):
    """
    URL converter for Group model.

    Converts between URL parameters and Group objects.
    """

    def to_python(self, value):
        """
        Convert a UUID string from the URL to a Group object.

        Args:
            value: UUID string from the URL

        Returns:
            Group: The group object

        Raises:
            NotFound: If the group with the given UUID does not exist
        """
        group = Group.query.filter_by(uuid=value).first()
        if not group:
            raise NotFound(f"Group {value} does not exist")
        return group

    def to_url(self, value):
        """
        Convert a Group object to a string for URL generation.

        Args:
            value: Group object or string UUID

        Returns:
            str: UUID string for the URL
        """
        return value.uuid if isinstance(value, Group) else str(value)


class ExpenseConverter(BaseConverter):
    """
    URL converter for Expense model.

    Converts between URL parameters and Expense objects.
    """

    def to_python(self, value):
        """
        Convert a UUID string from the URL to an Expense object.

        Args:
            value: UUID string from the URL

        Returns:
            Expense: The expense object

        Raises:
            NotFound: If the expense with the given UUID does not exist
        """
        expense = Expense.query.filter_by(uuid=value).first()
        if not expense:
            raise NotFound(f"Expense {value} does not exist")
        return expense

    def to_url(self, value):
        """
        Convert an Expense object to a string for URL generation.

        Args:
            value: Expense object or string UUID

        Returns:
            str: UUID string for the URL
        """
        return value.uuid if isinstance(value, Expense) else str(value)


def make_links(resource: str, resource_id: int, extras: dict = None, full_path: str = None) -> dict:
    """
    Generate hypermedia _links for a REST resource.

    Args:
        resource (str): The base resource path (e.g. 'groups', 'expenses').
        resource_id (int): The ID of the resource.
        extras (dict): Additional custom links to merge.

    Returns:
        dict: A dictionary with standard and custom _links.
    """
    path = full_path or f"/{resource}/{resource_id}"
    links = {
        "self": {"href": path},
        "update": {"href": path, "method": "PUT"},
        "delete": {"href": path, "method": "DELETE"}
    }
    if extras:
        links.update(extras)
    return links


class MasonBuilder(dict):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def add_namespace(self, ns, uri):
        self.setdefault("@namespaces", {})
        self["@namespaces"][ns] = {"name": uri}

    def add_control(self, ctrl_name, href, **kwargs):
        self.setdefault("@controls", {})
        self["@controls"][ctrl_name] = {"href": href, **kwargs}

    def add_error(self, title, details):
        self["@error"] = {
            "@message": title,
            "@messages": [details]
        }

    def add_controls_bulk(self, controls: dict):
        for name, params in controls.items():
            self.add_control(name, **params)

