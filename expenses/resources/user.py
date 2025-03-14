"""User resources module for the expenses API.

This module defines the RESTful resources for User objects, including
collection and individual item endpoints with CRUD operations.
"""

import secrets
from flask import request, g
from flask_restful import Resource
from jsonschema import validate, ValidationError
from werkzeug.exceptions import Conflict, BadRequest, UnsupportedMediaType, Forbidden
from expenses import cache
from expenses.utils import require_api_key
from expenses.models import db, User, ApiKey


class UserCollection(Resource):
    """Resource for collection of User objects"""

    @cache.cached(timeout=60)
    def get(self):
        """Get all users"""
        users = User.query.all()
        return {"users": [user.serialize(short_form=True) for user in users]}, 200

    def post(self):
        """Create a new user"""
        if not request.json:
            raise UnsupportedMediaType("Request must be JSON")

        # Validate required fields
        try:
            validate(instance=request.json, schema=User.get_schema())
        except ValidationError as e:
            raise BadRequest(f"Validation error: {e.message}") from e

        existing_user = User.query.filter_by(email=request.json["email"]).first()
        if existing_user:
            raise Conflict(f"User with email {request.json['email']} already exists")

        # Create new user
        user = User()
        user.deserialize(request.json)

        db.session.add(user)
        db.session.commit()

        # Create API key for the user
        api_key = secrets.token_urlsafe(32)
        db_key = ApiKey(key_hash=ApiKey.get_hash(api_key), user_id=user.id)
        db.session.add(db_key)
        db.session.commit()

        # Clear cache
        cache.delete("users")

        return {"user": user.serialize(), "api_key": api_key}, 201


class UserItem(Resource):
    """Resource for individual User objects"""

    @cache.cached(timeout=60)
    def get(self, user):
        """Get user details"""
        return {"user": user.serialize()}, 200

    @require_api_key
    def put(self, user):
        """Update user details"""
        if g.user_id != user.id:
            raise Forbidden("You can only update your own account")

        if not request.json:
            raise UnsupportedMediaType("Request must be JSON")

        # Check if email already exists (if being changed)
        if "email" in request.json and request.json["email"] != user.email:
            existing_user = User.query.filter_by(email=request.json["email"]).first()
            if existing_user:
                raise Conflict(
                    f"User with email {request.json['email']} already exists"
                )

        user.deserialize(request.json)
        db.session.commit()

        # Clear cache
        cache.delete(f"users/{user.uuid}")
        cache.delete("users")

        return {"user": user.serialize()}, 200

    @require_api_key
    def delete(self, user):
        """Delete user"""
        if g.user_id != user.id:
            raise Forbidden("You can only delete your own account")

        db.session.delete(user)
        db.session.commit()

        # Clear cache
        cache.delete(f"users/{user.uuid}")
        cache.delete("users")

        return "", 204
