"""Group Member resources module for the expenses API.

This module defines the RESTful resources for GroupMember objects, including
collection and individual item endpoints with CRUD operations.
It handles the management of group membership, including adding members,
removing members, and enforcing admin role permissions.
"""

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
from expenses.utils import require_api_key
from expenses.models import db, User, GroupMember


class GroupMemberCollection(Resource):
    """Resource for collection of GroupMember objects in a group"""

    @cache.cached(timeout=30)
    def get(self, group):
        """Get all members of a group"""
        members = GroupMember.query.filter_by(group_id=group.id).all()
        return {"members": [member.serialize() for member in members]}, 200

    @require_api_key
    def post(self, group):
        """Add a member to a group"""
        # Check if user is admin
        member_check = GroupMember.query.filter_by(
            user_id=g.user_id, group_id=group.id
        ).first()
        if not member_check or member_check.role != "admin":
            raise Forbidden("Only group admins can add members")

        if not request.json:
            raise UnsupportedMediaType("Request must be JSON")

        # Check if user exists
        user_uuid = request.json["user_id"]
        user = User.query.filter_by(uuid=user_uuid).first()
        if not user:
            raise BadRequest(f"User {user_uuid} does not exist")

        # Check if user is already a member
        existing_member = GroupMember.query.filter_by(
            user_id=user.id, group_id=group.id
        ).first()

        if existing_member:
            raise Conflict(f"User {user_uuid} is already a member of this group")

        # Create new membership
        member = GroupMember(user_id=user.id, group_id=group.id)
        if "role" in request.json:
            member.role = request.json["role"]

        db.session.add(member)
        db.session.commit()

        # Clear cache
        cache.delete(f"groups/{group.uuid}/members")
        cache.delete(f"groups/{group.uuid}")

        return {"member": member.serialize()}, 201


class GroupMemberItem(Resource):
    """Resource for individual GroupMember objects"""

    @require_api_key
    def delete(self, group, user):
        """Remove member from group"""
        # User can remove self or admin can remove anyone
        if g.user_id != user.id:
            admin_check = GroupMember.query.filter_by(
                user_id=g.user_id, group_id=group.id, role="admin"
            ).first()
            if not admin_check:
                raise Forbidden("Only group admins can remove other members")

        member = GroupMember.query.filter_by(user_id=user.id, group_id=group.id).first()
        if not member:
            raise NotFound(f"User {user.uuid} is not a member of group {group.uuid}")

        # Check if last admin
        if member.role == "admin":
            admin_count = GroupMember.query.filter_by(
                group_id=group.id, role="admin"
            ).count()
            if admin_count <= 1:
                raise BadRequest("Cannot remove the last admin of the group")

        db.session.delete(member)
        db.session.commit()

        # Clear cache
        cache.delete(f"groups/{group.uuid}/members")
        cache.delete(f"groups/{group.uuid}")

        return "", 204
