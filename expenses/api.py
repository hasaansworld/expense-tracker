from flask import Blueprint
from flask_restful import Api
from resources.user import UserCollection, UserItem
from resources.group import GroupCollection, GroupItem
from resources.group_member import GroupMemberCollection, GroupMemberItem
from resources.expense import ExpenseCollection, ExpenseItem, ExpenseParticipantCollection

api_bp = Blueprint("api", __name__, url_prefix="/api")
api = Api(api_bp)

# Register API endpoints
api.add_resource(UserCollection, '/api/users/')
api.add_resource(UserItem, '/api/users/<user:user>')
api.add_resource(GroupCollection, '/api/groups/')
api.add_resource(GroupItem, '/api/groups/<group:group>')
api.add_resource(GroupMemberCollection, '/api/groups/<group:group>/members/')
api.add_resource(GroupMemberItem, '/api/groups/<group:group>/members/<user:user>')
api.add_resource(ExpenseCollection, '/api/groups/<group:group>/expenses/')
api.add_resource(ExpenseItem, '/api/expenses/<expense:expense>')
api.add_resource(ExpenseParticipantCollection, '/api/expenses/<expense:expense>/participants/')
