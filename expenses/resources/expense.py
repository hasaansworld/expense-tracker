"""Expense resources module for the expenses API."""

from flask import request, g
from flask_restful import Resource
from jsonschema import validate, ValidationError
from werkzeug.exceptions import BadRequest, UnsupportedMediaType, Forbidden

from expenses import cache
from expenses.models import db, User, GroupMember, Expense, ExpenseParticipant
from expenses.utils import require_api_key, make_links


class ExpenseCollection(Resource):
    """Resource for collection of Expense objects in a group"""

    @cache.cached(timeout=30)
    def get(self, group):
        """Get all expenses in a group"""
        expenses = Expense.query.filter_by(group_id=group.id).all()
        return {
            "expenses": [
                {
                    "expense": expense.serialize(),
                    "_links": make_links("expenses", expense.id, {}, full_path=f"/api/groups/{group.id}/expenses/{expense.id}")
                }
                for expense in expenses
            ]
        }, 200

    @require_api_key
    def post(self, group):
        """Create a new expense in a group"""
        member = GroupMember.query.filter_by(user_id=g.user_id, group_id=group.id).first()
        if not member:
            raise Forbidden("Only group members can create expenses")

        if not request.json:
            raise UnsupportedMediaType("Request must be JSON")

        try:
            validate(instance=request.json, schema=Expense.get_schema())
        except ValidationError as e:
            raise BadRequest(f"Validation error: {e.message}") from e

        expense = Expense(created_by=g.user_id, group_id=group.id)
        expense.deserialize(request.json)

        db.session.add(expense)
        db.session.flush()

        if "participants" in request.json:
            total_share = 0
            for participant_data in request.json["participants"]:
                user_uuid = participant_data["user_id"]
                participant_user = User.query.filter_by(uuid=user_uuid).first()
                if not participant_user:
                    db.session.rollback()
                    raise BadRequest(f"User {user_uuid} does not exist")

                participant_member = GroupMember.query.filter_by(
                    user_id=participant_user.id, group_id=group.id).first()
                if not participant_member:
                    db.session.rollback()
                    raise BadRequest(f"User {user_uuid} is not a member of this group")

                participant = ExpenseParticipant(
                    expense_id=expense.id,
                    user_id=participant_user.id,
                    share=participant_data["share"],
                )

                if "paid" in participant_data:
                    participant.paid = participant_data["paid"]

                total_share += float(participant.share)
                db.session.add(participant)

            if abs(total_share - float(expense.amount)) > 0.01:
                db.session.rollback()
                raise BadRequest(
                    f"Total participant shares ({total_share}) must equal expense amount ({expense.amount})"
                )

        db.session.commit()
        cache.delete(f"groups/{group.uuid}/expenses")

        return {
            "expense": expense.serialize(),
            "_links": make_links("expenses", expense.id, {
                "participants": {
                    "href": f"/expenses/{expense.id}/participants/",
                    "method": "GET"
                }
            }, full_path=f"/expenses/{expense.id}")
        }, 201


class ExpenseItem(Resource):
    """Resource for individual Expense objects"""

    @cache.cached(timeout=30)
    def get(self, expense):
        """Get expense details"""
        return {
            "expense": expense.serialize(),
            "_links": make_links("expenses", expense.id, {}, full_path=f"/api/groups/{expense.group_id}/expenses/{expense.id}")
        }, 200

    @require_api_key
    def put(self, expense):
        """Update expense details"""
        if g.user_id != expense.created_by:
            raise Forbidden("Only the creator can update the expense")

        if not request.json:
            raise UnsupportedMediaType("Request must be JSON")

        if "amount" in request.json or "description" in request.json:
            update_schema = {
                "type": "object",
                "properties": {
                    "amount": {"type": "number", "minimum": 0},
                    "description": {"type": "string"},
                },
            }

            try:
                validate(instance=request.json, schema=update_schema)
            except ValidationError as e:
                raise BadRequest(f"Validation error: {e.message}") from e

        expense.deserialize(request.json)

        if "participants" in request.json:
            ExpenseParticipant.query.filter_by(expense_id=expense.id).delete()

            total_share = 0
            for participant_data in request.json["participants"]:
                try:
                    validate(
                        instance=participant_data,
                        schema=ExpenseParticipant.get_schema(),
                    )
                except ValidationError as e:
                    db.session.rollback()
                    raise BadRequest(f"Participant validation error: {e.message}") from e

                user_uuid = participant_data["user_id"]
                participant_user = User.query.filter_by(uuid=user_uuid).first()
                if not participant_user:
                    db.session.rollback()
                    raise BadRequest(f"User {user_uuid} does not exist")

                participant_member = GroupMember.query.filter_by(
                    user_id=participant_user.id, group_id=expense.group_id).first()
                if not participant_member:
                    db.session.rollback()
                    raise BadRequest(f"User {user_uuid} is not a member of this group")

                participant = ExpenseParticipant(
                    expense_id=expense.id,
                    user_id=participant_user.id,
                    share=participant_data["share"],
                )

                if "paid" in participant_data:
                    participant.paid = participant_data["paid"]

                total_share += float(participant.share)
                db.session.add(participant)

            if abs(total_share - float(expense.amount)) > 0.01:
                db.session.rollback()
                raise BadRequest(
                    f"Total participant shares ({total_share}) must equal expense amount ({expense.amount})"
                )

        db.session.commit()
        cache.delete(f"expenses/{expense.uuid}")
        cache.delete(f"groups/{expense.group.uuid}/expenses")

        return {
            "expense": expense.serialize(),
            "_links": make_links("expenses", expense.id, {}, full_path=f"/api/groups/{expense.group_id}/expenses/{expense.id}")
        }, 200

    @require_api_key
    def delete(self, expense):
        """Delete expense"""
        if g.user_id != expense.created_by:
            admin_check = GroupMember.query.filter_by(
                user_id=g.user_id, group_id=expense.group_id, role="admin").first()
            if not admin_check:
                raise Forbidden("Only the creator or group admin can delete the expense")

        db.session.delete(expense)
        db.session.commit()

        cache.delete(f"expenses/{expense.uuid}")
        cache.delete(f"groups/{expense.group.uuid}/expenses")

        return "", 204


class ExpenseParticipantCollection(Resource):
    """Resource for collection of ExpenseParticipant objects in an expense"""

    @cache.cached(timeout=30)
    def get(self, expense):
        """Get all participants in an expense"""
        participants = ExpenseParticipant.query.filter_by(expense_id=expense.id).all()
        return {
            "participants": [
                {
                    **participant.serialize(),
                    "_links": make_links("expenses", expense.id, {
                        "user": {"href": f"/users/{participant.user_id}", "method": "GET"}
                    }, full_path=f"/expenses/{expense.id}/participants/")
                }
                for participant in participants
            ],
            "_links": make_links("expenses", expense.id, {
                "add": {"href": f"/expenses/{expense.id}/participants/", "method": "POST"}
            }, full_path=f"/expenses/{expense.id}/participants/")
        }, 200
