"""Group resources module for the expenses API.

This module defines the RESTful resources for Group objects, including
collection and individual item endpoints with CRUD operations.
It handles the creation, retrieval, updating, and deletion of groups,
with appropriate permission checks for group administrators.
"""

from flask import request, g
from flask_restful import Resource
from jsonschema import validate, ValidationError
from werkzeug.exceptions import BadRequest, UnsupportedMediaType, Forbidden
from expenses import cache
from expenses.utils import require_api_key, make_links
from expenses.models import db, Group, GroupMember


class GroupCollection(Resource):
    """Resource for collection of Group objects"""

    @cache.cached(timeout=30)
    def get(self):
        """Get all groups"""
        groups = Group.query.all()
        return {
            "groups": [
                {
                    **group.serialize(short_form=True),
                    "_links": make_links("groups", group.id, {
                        "members": {
                            "href": f"/groups/{group.id}/members/",
                            "method": "GET"
                        },
                        "expenses": {
                            "href": f"/groups/{group.id}/expenses/",
                            "method": "GET"
                        }
                    })
                } for group in groups
            ]
        }, 200

    @require_api_key
    def post(self):
        """Create a new group"""
        if not request.json:
            raise UnsupportedMediaType("Request must be JSON")

        # Validate required fields
        try:
            validate(instance=request.json, schema=Group.get_schema())
        except ValidationError as e:
            raise BadRequest(f"Validation error: {e.message}") from e

        # Create new group
        group = Group(created_by=g.user_id)
        group.deserialize(request.json)

        db.session.add(group)
        db.session.flush()

        # Add creator as a member with admin role
        member = GroupMember(user_id=g.user_id, group_id=group.id, role="admin")
        db.session.add(member)

        db.session.commit()

        # Clear cache
        cache.delete("groups")

        return {
            "group": group.serialize(),
            "_links": make_links("groups", group.id, {
                "members": {
                    "href": f"/groups/{group.id}/members/",
                    "method": "GET"
                },
                "expenses": {
                    "href": f"/groups/{group.id}/expenses/",
                    "method": "GET"
                }
            })
        }, 201


class GroupItem(Resource):
    """Resource for individual Group objects"""

    @cache.cached(timeout=30)
    def get(self, group):
        """Get group details"""
        return {
            "group": group.serialize(),
            "_links": make_links("groups", group.id, {
                "members": {
                    "href": f"/groups/{group.id}/members/",
                    "method": "GET"
                },
                "expenses": {
                    "href": f"/groups/{group.id}/expenses/",
                    "method": "GET"
                }
            })
        }, 200

    @require_api_key
    def put(self, group):
        """Update group details"""
        # Check if user is admin
        member = GroupMember.query.filter_by(
            user_id=g.user_id, group_id=group.id
        ).first()
        if not member or member.role != "admin":
            raise Forbidden("Only group admins can update group details")

        if not request.json:
            raise UnsupportedMediaType("Request must be JSON")

        group.deserialize(request.json)
        db.session.commit()

        # Clear cache
        cache.delete(f"groups/{group.uuid}")
        cache.delete("groups")
        cache.delete(f"groups/{group.uuid}/members")

        return {
            "group": group.serialize(),
            "_links": make_links("groups", group.id)
        }, 200

    @require_api_key
    def delete(self, group):
        """Delete group"""
        # Check if user is admin
        member = GroupMember.query.filter_by(
            user_id=g.user_id, group_id=group.id
        ).first()
        if not member or member.role != "admin":
            raise Forbidden("Only group admins can delete the group")

        db.session.delete(group)
        db.session.commit()

        # Clear cache
        cache.delete(f"groups/{group.uuid}")
        cache.delete("groups")
        cache.delete(f"groups/{group.uuid}/members")

        return "", 204
