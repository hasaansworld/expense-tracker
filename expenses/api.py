from flask import Blueprint
from flask_restful import Api
from expenses.resources.user import UserCollection, UserItem
from expenses.resources.group import GroupCollection, GroupItem
from expenses.resources.group_member import GroupMemberCollection, GroupMemberItem
from expenses.resources.expense import ExpenseCollection, ExpenseItem, ExpenseParticipantCollection

api_bp = Blueprint("api", __name__, url_prefix="/api")
api = Api(api_bp)

# Register API endpoints
api.add_resource(UserCollection, '/users/')
api.add_resource(UserItem, '/users/<user:user>')
api.add_resource(GroupCollection, '/groups/')
api.add_resource(GroupItem, '/groups/<group:group>')
api.add_resource(GroupMemberCollection, '/groups/<group:group>/members/')
api.add_resource(GroupMemberItem, '/groups/<group:group>/members/<user:user>')
api.add_resource(ExpenseCollection, '/groups/<group:group>/expenses/')
api.add_resource(ExpenseItem, '/expenses/<expense:expense>')
api.add_resource(ExpenseParticipantCollection, '/expenses/<expense:expense>/participants/')
