"""API module for the expenses application.

This module defines the Flask Blueprint and RESTful API 
routes for the expenses application.
"""

from flask import Blueprint
from flask_restful import Api, Resource
from expenses.resources.user import UserCollection, UserItem
from expenses.resources.group import GroupCollection, GroupItem
from expenses.resources.group_member import GroupMemberCollection, GroupMemberItem
from expenses.resources.expense import ExpenseCollection, ExpenseItem, ExpenseParticipantCollection
from expenses import available_routes

api_bp = Blueprint("api", __name__, url_prefix="/api")
api = Api(api_bp)

# Simple root endpoint
class Root(Resource):
    def get(self):
        return {"available_routes": available_routes}, 200

# Register API endpoints
api.add_resource(Root, '/')
api.add_resource(UserCollection, '/users/')
api.add_resource(UserItem, '/users/<user:user>')
api.add_resource(GroupCollection, '/groups/')
api.add_resource(GroupItem, '/groups/<group:group>')
api.add_resource(GroupMemberCollection, '/groups/<group:group>/members/')
api.add_resource(GroupMemberItem, '/groups/<group:group>/members/<user:user>')
api.add_resource(ExpenseCollection, '/groups/<group:group>/expenses/')
api.add_resource(ExpenseItem, '/expenses/<expense:expense>')
api.add_resource(ExpenseParticipantCollection, '/expenses/<expense:expense>/participants/')

