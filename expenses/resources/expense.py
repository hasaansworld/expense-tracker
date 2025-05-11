"""Expense resources module for the expenses API."""

from flask import request, g
from flask_restful import Resource
from jsonschema import validate, ValidationError
from werkzeug.exceptions import BadRequest, UnsupportedMediaType, Forbidden

from expenses import cache
from expenses.models import db, User, GroupMember, Expense, ExpenseParticipant
from expenses.utils import require_api_key, MasonBuilder


def build_expense_controls(expense):
    return {
        "self": {"href": f"/expenses/{expense.id}"},
        "update": {
            "href": f"/expenses/{expense.id}",
            "method": "PUT",
            "encoding": "json",
            "schema": Expense.get_schema()
        },
        "delete": {"href": f"/expenses/{expense.id}", "method": "DELETE"},
        "participants": {"href": f"/expenses/{expense.id}/participants/", "method": "GET"},
        "group": {"href": f"/groups/{expense.group_id}", "method": "GET"}
    }


class ExpenseCollection(Resource):
    """Resource for collection of Expense objects in a group"""

    @cache.cached(timeout=30)
    def get(self, group):
        """Get all expenses in a group"""
        expenses = Expense.query.filter_by(group_id=group.id).all()
        res = MasonBuilder()
        res["expenses"] = []

        for expense in expenses:
            e_doc = MasonBuilder(**expense.serialize())
            for name, props in build_expense_controls(expense).items():
                e_doc.add_control(name, **props)
            res["expenses"].append(e_doc)

        res.add_control("self", f"/groups/{group.id}/expenses/")
        res.add_control("create", f"/groups/{group.id}/expenses/", method="POST", encoding="json", schema=Expense.get_schema())
        return res, 200

    @require_api_key
    def post(self, group):
        # g.user_id = 1
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

        res = MasonBuilder(**expense.serialize())
        for name, props in build_expense_controls(expense).items():
            res.add_control(name, **props)

        return res, 201


class ExpenseItem(Resource):
    """Resource for individual Expense objects"""

    @cache.cached(timeout=30)
    def get(self, expense):
        """Get expense details"""
        res = MasonBuilder(**expense.serialize())
        for name, props in build_expense_controls(expense).items():
            res.add_control(name, **props)
        return res, 200

    @require_api_key
    def put(self, expense):
        """Update expense details"""
        if g.user_id != expense.created_by:
            raise Forbidden("Only the creator can update the expense")

        if not request.json:
            raise UnsupportedMediaType("Request must be JSON")

        try:
            validate(instance=request.json, schema=Expense.get_schema())
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

        res = MasonBuilder(**expense.serialize())
        for name, props in build_expense_controls(expense).items():
            res.add_control(name, **props)
        return res, 200

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

        res = MasonBuilder()
        res["participants"] = []

        for participant in participants:
            p_doc = MasonBuilder(**participant.serialize(short_form=True))
            p_doc.add_control("user", f"/users/{participant.user_id}", method="GET")
            res["participants"].append(p_doc)

        res.add_control("self", f"/expenses/{expense.id}/participants/")
        res.add_control("add", f"/expenses/{expense.id}/participants/", method="POST", encoding="json", schema=ExpenseParticipant.get_schema())

        return res, 200
