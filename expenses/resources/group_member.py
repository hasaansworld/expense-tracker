"""Group Member resources module for the expenses API."""

from flask import request, g
from flask_restful import Resource
from werkzeug.exceptions import (
    Conflict,
    NotFound,
    BadRequest,
    UnsupportedMediaType,
    Forbidden,
)

from expenses import cache
from expenses.utils import require_api_key, MasonBuilder
from expenses.models import db, User, GroupMember


def build_member_controls(group_id, user_id):
    return {
        "self": {"href": f"/groups/{group_id}/members/{user_id}"},
        "delete": {"href": f"/groups/{group_id}/members/{user_id}", "method": "DELETE"},
        "user": {"href": f"/users/{user_id}", "method": "GET"}
    }


def build_member_collection_controls(group_id):
    return {
        "self": {"href": f"/groups/{group_id}/members/"},
        "add": {
            "href": f"/groups/{group_id}/members/",
            "method": "POST",
            "encoding": "json",
            "schema": {
                "type": "object",
                "required": ["user_id"],
                "properties": {
                    "user_id": {"type": "string"},
                    "role": {"type": "string"}
                }
            }
        }
    }


class GroupMemberCollection(Resource):
    """Resource for collection of GroupMember objects in a group"""

    def get(self, group):
        """Get all members of a group"""
        res = MasonBuilder()
        res["members"] = []

        members = GroupMember.query.filter_by(group_id=group.id).all()
        for member in members:
            member_data = MasonBuilder(**member.serialize())
            for name, props in build_member_controls(group.uuid, member.user_id).items():
                member_data.add_control(name, **props)
            res["members"].append(member_data)

        for name, props in build_member_collection_controls(group.uuid).items():
            res.add_control(name, **props)

        return res, 200

    @require_api_key
    def post(self, group):
        """Add a member to a group"""
        member_check = GroupMember.query.filter_by(
            user_id=g.user_id, group_id=group.id
        ).first()
        if not member_check or member_check.role != "admin":
            raise Forbidden("Only group admins can add members")

        if not request.json:
            raise UnsupportedMediaType("Request must be JSON")

        user_uuid = request.json["user_id"]
        user = User.query.filter_by(uuid=user_uuid).first()
        if not user:
            raise BadRequest(f"User {user_uuid} does not exist")

        existing_member = GroupMember.query.filter_by(
            user_id=user.id, group_id=group.id
        ).first()
        if existing_member:
            raise Conflict(f"User {user_uuid} is already a member of this group")

        member = GroupMember(user_id=user.id, group_id=group.id)
        if "role" in request.json:
            member.role = request.json["role"]

        db.session.add(member)
        db.session.commit()

        res = MasonBuilder(**member.serialize())
        for name, props in build_member_controls(group.uuid, user.id).items():
            res.add_control(name, **props)

        return res, 201


class GroupMemberItem(Resource):
    """Resource for individual GroupMember objects"""

    @require_api_key
    def delete(self, group, user):
        """Remove member from group"""
        if g.user_id != user.id:
            admin_check = GroupMember.query.filter_by(
                user_id=g.user_id, group_id=group.id, role="admin"
            ).first()
            if not admin_check:
                raise Forbidden("Only group admins can remove other members")

        member = GroupMember.query.filter_by(user_id=user.id, group_id=group.id).first()
        if not member:
            raise NotFound(f"User {user.uuid} is not a member of group {group.uuid}")

        if member.role == "admin":
            admin_count = GroupMember.query.filter_by(
                group_id=group.id, role="admin"
            ).count()
            if admin_count <= 1:
                raise BadRequest("Cannot remove the last admin of the group")

        db.session.delete(member)
        db.session.commit()

        cache.delete(f"groups/{group.uuid}/members")
        cache.delete(f"groups/{group.uuid}")

        return "", 204
