"""Group resources module for the expenses API with Mason hypermedia support.

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
from expenses.utils import require_api_key, MasonBuilder  # ⬅️ Replaced make_links with MasonBuilder
from expenses.models import db, Group, GroupMember


def build_group_controls(group_id):
    return {
        "self": {"href": f"/groups/{group_id}"},
        "update": {
            "href": f"/groups/{group_id}",
            "method": "PUT",
            "encoding": "json",
            "schema": Group.get_schema()
        },
        "delete": {"href": f"/groups/{group_id}", "method": "DELETE"},
        "members": {"href": f"/groups/{group_id}/members/", "method": "GET"},
        "expenses": {"href": f"/groups/{group_id}/expenses/", "method": "GET"}
    }




class GroupCollection(Resource):
    """Resource for collection of Group objects"""

    def get(self):
        """Get all groups"""
        groups = Group.query.all()
        return {
            "groups": [
                MasonBuilder(
                    **group.serialize(short_form=True),
                    **{"@controls": build_group_controls(group.id)}
                )
                for group in groups
            ],
            "@controls": {
                "self": {"href": "/groups/"},
                "create": {
                    "href": "/groups/",
                    "method": "POST",
                    "encoding": "json",
                    "schema": Group.get_schema()
                }
            }
        }, 200

    @require_api_key
    def post(self):
        """Create a new group"""
        # g.user_id = 1
        if not request.json:
            raise UnsupportedMediaType("Request must be JSON")

        try:
            validate(instance=request.json, schema=Group.get_schema())
        except ValidationError as e:
            raise BadRequest(f"Validation error: {e.message}") from e

        group = Group(created_by=g.user_id)
        group.deserialize(request.json)

        db.session.add(group)
        db.session.flush()

        member = GroupMember(user_id=g.user_id, group_id=group.id, role="admin")
        db.session.add(member)

        db.session.commit()

        cache.delete("groups")

        response = MasonBuilder(**group.serialize())
        for name, props in build_group_controls(group.uuid).items():
            response.add_control(name, **props)

        return response, 201


class GroupItem(Resource):
    """Resource for individual Group objects"""

    @cache.cached(timeout=30)
    def get(self, group):
        """Get group details"""
        response = MasonBuilder(**group.serialize())
        for name, props in build_group_controls(group.id).items():
            response.add_control(name, **props)
        return response, 200

    @require_api_key
    def put(self, group):
        """Update group details"""
        member = GroupMember.query.filter_by(
            user_id=g.user_id, group_id=group.id
        ).first()
        if not member or member.role != "admin":
            raise Forbidden("Only group admins can update group details")

        if not request.json:
            raise UnsupportedMediaType("Request must be JSON")

        group.deserialize(request.json)
        db.session.commit()

        cache.delete(f"groups/{group.uuid}")
        cache.delete("groups")
        cache.delete(f"groups/{group.uuid}/members")

        response = MasonBuilder(**group.serialize())
        for name, props in build_group_controls(group.uuid).items():
            response.add_control(name, **props)

        return response, 200

    @require_api_key
    def delete(self, group):
        """Delete group"""
        member = GroupMember.query.filter_by(
            user_id=g.user_id, group_id=group.id
        ).first()
        if not member or member.role != "admin":
            raise Forbidden("Only group admins can delete the group")

        db.session.delete(group)
        db.session.commit()

        cache.delete(f"groups/{group.uuid}")
        cache.delete("groups")
        cache.delete(f"groups/{group.uuid}/members")

        return "", 204
