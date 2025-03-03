from flask import Flask, request, Response, g
from flask_restful import Api, Resource
from flask_caching import Cache
from jsonschema import validate, ValidationError, draft7_format_checker
from werkzeug.exceptions import NotFound, Conflict, BadRequest, UnsupportedMediaType, Forbidden
from werkzeug.routing import BaseConverter
import secrets
from app.models import db, User, ApiKey, Group, GroupMember, Expense, ExpenseParticipant

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///expense_tracker.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["CACHE_TYPE"] = "SimpleCache"
app.config["CACHE_DEFAULT_TIMEOUT"] = 300

db.init_app(app)
api = Api(app)
cache = Cache(app)

# Content type for JSON
JSON = "application/json"

# Authentication helpers
def require_api_key(func):
    """Decorator to require API key for a resource method"""
    def wrapper(*args, **kwargs):
        api_key = request.headers.get('X-API-Key')
        if not api_key:
            raise Forbidden("API key is required")
        
        key_hash = ApiKey.get_hash(api_key)
        db_key = ApiKey.query.filter_by(key_hash=key_hash).first()
        
        if not db_key:
            raise Forbidden("Invalid API key")
        
        g.user_id = db_key.user_id
        return func(*args, **kwargs)
    
    return wrapper

class UserConverter(BaseConverter):
    """URL converter for User model"""
    def to_python(self, value):
        user = User.query.filter_by(uuid=value).first()
        if not user:
            raise NotFound(f"User {value} does not exist")
        return user
    
    def to_url(self, value):
        return value.uuid if isinstance(value, User) else str(value)

class GroupConverter(BaseConverter):
    """URL converter for Group model"""
    def to_python(self, value):
        group = Group.query.filter_by(uuid=value).first()
        if not group:
            raise NotFound(f"Group {value} does not exist")
        return group
    
    def to_url(self, value):
        return value.uuid if isinstance(value, Group) else str(value)

class ExpenseConverter(BaseConverter):
    """URL converter for Expense model"""
    def to_python(self, value):
        expense = Expense.query.filter_by(uuid=value).first()
        if not expense:
            raise NotFound(f"Expense {value} does not exist")
        return expense
    
    def to_url(self, value):
        return value.uuid if isinstance(value, Expense) else str(value)

# Register URL converters
app.url_map.converters['user'] = UserConverter
app.url_map.converters['group'] = GroupConverter
app.url_map.converters['expense'] = ExpenseConverter

# Resource Classes
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
        
        return {
            "user": user.serialize(),
            "api_key": api_key
        }, 201

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
                raise Conflict(f"User with email {request.json['email']} already exists")
        
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

class GroupCollection(Resource):
    """Resource for collection of Group objects"""
    
    @cache.cached(timeout=30)
    def get(self):
        """Get all groups"""
        groups = Group.query.all()
        return {"groups": [group.serialize(short_form=True) for group in groups]}, 200
    
    @require_api_key
    def post(self):
        """Create a new group"""
        if not request.json:
            raise UnsupportedMediaType("Request must be JSON")
        
        # Create new group
        group = Group(created_by=g.user_id)
        group.deserialize(request.json)
        
        db.session.add(group)
        db.session.flush()
        
        # Add creator as a member with admin role
        member = GroupMember(user_id=g.user_id, group_id=group.id, role='admin')
        db.session.add(member)
        
        db.session.commit()
        
        # Clear cache
        cache.delete("groups")
        
        return {"group": group.serialize()}, 201

class GroupItem(Resource):
    """Resource for individual Group objects"""
    
    @cache.cached(timeout=30)
    def get(self, group):
        """Get group details"""
        return {"group": group.serialize()}, 200
    
    @require_api_key
    def put(self, group):
        """Update group details"""
        # Check if user is admin
        member = GroupMember.query.filter_by(user_id=g.user_id, group_id=group.id).first()
        if not member or member.role != 'admin':
            raise Forbidden("Only group admins can update group details")
        
        if not request.json:
            raise UnsupportedMediaType("Request must be JSON")
        
        group.deserialize(request.json)
        db.session.commit()
        
        # Clear cache
        cache.delete(f"groups/{group.uuid}")
        cache.delete("groups")
        cache.delete(f"groups/{group.uuid}/members")
        
        return {"group": group.serialize()}, 200
    
    @require_api_key
    def delete(self, group):
        """Delete group"""
        # Check if user is admin
        member = GroupMember.query.filter_by(user_id=g.user_id, group_id=group.id).first()
        if not member or member.role != 'admin':
            raise Forbidden("Only group admins can delete the group")
        
        db.session.delete(group)
        db.session.commit()
        
        # Clear cache
        cache.delete(f"groups/{group.uuid}")
        cache.delete("groups")
        cache.delete(f"groups/{group.uuid}/members")
        
        return "", 204

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
        member_check = GroupMember.query.filter_by(user_id=g.user_id, group_id=group.id).first()
        if not member_check or member_check.role != 'admin':
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
            user_id=user.id,
            group_id=group.id
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
            admin_check = GroupMember.query.filter_by(user_id=g.user_id, group_id=group.id, role='admin').first()
            if not admin_check:
                raise Forbidden("Only group admins can remove other members")
        
        member = GroupMember.query.filter_by(user_id=user.id, group_id=group.id).first()
        if not member:
            raise NotFound(f"User {user.uuid} is not a member of group {group.uuid}")
        
        # Check if last admin
        if member.role == 'admin':
            admin_count = GroupMember.query.filter_by(group_id=group.id, role='admin').count()
            if admin_count <= 1:
                raise BadRequest("Cannot remove the last admin of the group")
        
        db.session.delete(member)
        db.session.commit()
        
        # Clear cache
        cache.delete(f"groups/{group.uuid}/members")
        cache.delete(f"groups/{group.uuid}")
        
        return "", 204

class ExpenseCollection(Resource):
    """Resource for collection of Expense objects in a group"""
    
    @cache.cached(timeout=30)
    def get(self, group):
        """Get all expenses in a group"""
        expenses = Expense.query.filter_by(group_id=group.id).all()
        return {"expenses": [expense.serialize(short_form=True) for expense in expenses]}, 200
    
    @require_api_key
    def post(self, group):
        """Create a new expense in a group"""
        # Check if user is member
        member = GroupMember.query.filter_by(user_id=g.user_id, group_id=group.id).first()
        if not member:
            raise Forbidden("Only group members can create expenses")
        
        if not request.json:
            raise UnsupportedMediaType("Request must be JSON")
        
        # Create new expense
        expense = Expense(created_by=g.user_id, group_id=group.id)
        expense.deserialize(request.json)
        
        db.session.add(expense)
        db.session.flush()
        
        # Process participants if included
        if "participants" in request.json:
            total_share = 0
            for participant_data in request.json["participants"]:
                # Check if user exists and is member of the group
                user_uuid = participant_data["user_id"]
                participant_user = User.query.filter_by(uuid=user_uuid).first()
                if not participant_user:
                    db.session.rollback()
                    raise BadRequest(f"User {user_uuid} does not exist")
                
                participant_member = GroupMember.query.filter_by(
                    user_id=participant_user.id,
                    group_id=group.id
                ).first()
                
                if not participant_member:
                    db.session.rollback()
                    raise BadRequest(f"User {user_uuid} is not a member of this group")
                
                participant = ExpenseParticipant(
                    expense_id=expense.id,
                    user_id=participant_user.id,
                    share=participant_data["share"]
                )
                
                if "paid" in participant_data:
                    participant.paid = participant_data["paid"]
                
                total_share += float(participant.share)
                
                db.session.add(participant)
            
            # Verify that total share equals expense amount
            if abs(total_share - float(expense.amount)) > 0.01:
                db.session.rollback()
                raise BadRequest(f"Total participant shares ({total_share}) must equal expense amount ({expense.amount})")
        
        db.session.commit()
        
        # Clear cache
        cache.delete(f"groups/{group.uuid}/expenses")
        
        return {"expense": expense.serialize()}, 201

class ExpenseItem(Resource):
    """Resource for individual Expense objects"""
    
    @cache.cached(timeout=30)
    def get(self, expense):
        """Get expense details"""
        return {"expense": expense.serialize()}, 200
    
    @require_api_key
    def put(self, expense):
        """Update expense details"""
        # Check if user is creator
        if g.user_id != expense.created_by:
            raise Forbidden("Only the creator can update the expense")
        
        if not request.json:
            raise UnsupportedMediaType("Request must be JSON")
        
        # Update expense
        expense.deserialize(request.json)
        
        # Update participants if included
        if "participants" in request.json:
            # Delete existing participants
            ExpenseParticipant.query.filter_by(expense_id=expense.id).delete()
            
            total_share = 0
            for participant_data in request.json["participants"]:
                # Check if user exists and is member of the group
                user_uuid = participant_data["user_id"]
                participant_user = User.query.filter_by(uuid=user_uuid).first()
                if not participant_user:
                    db.session.rollback()
                    raise BadRequest(f"User {user_uuid} does not exist")
                
                participant_member = GroupMember.query.filter_by(
                    user_id=participant_user.id,
                    group_id=expense.group_id
                ).first()
                
                if not participant_member:
                    db.session.rollback()
                    raise BadRequest(f"User {user_uuid} is not a member of this group")
                
                participant = ExpenseParticipant(
                    expense_id=expense.id,
                    user_id=participant_user.id,
                    share=participant_data["share"]
                )
                
                if "paid" in participant_data:
                    participant.paid = participant_data["paid"]
                
                total_share += float(participant.share)
                
                db.session.add(participant)
                
            # Verify that total share equals expense amount
            if abs(total_share - float(expense.amount)) > 0.01:
                db.session.rollback()
                raise BadRequest(f"Total participant shares ({total_share}) must equal expense amount ({expense.amount})")
        
        db.session.commit()
        
        # Clear cache
        cache.delete(f"expenses/{expense.uuid}")
        cache.delete(f"groups/{expense.group.uuid}/expenses")
        
        return {"expense": expense.serialize()}, 200
    
    @require_api_key
    def delete(self, expense):
        """Delete expense"""
        # Check if user is creator or group admin
        if g.user_id != expense.created_by:
            admin_check = GroupMember.query.filter_by(
                user_id=g.user_id, 
                group_id=expense.group_id,
                role='admin'
            ).first()
            
            if not admin_check:
                raise Forbidden("Only the creator or group admin can delete the expense")
        
        # Delete expense (cascade will delete participants)
        db.session.delete(expense)
        db.session.commit()
        
        # Clear cache
        cache.delete(f"expenses/{expense.uuid}")
        cache.delete(f"groups/{expense.group.uuid}/expenses")
        
        return "", 204

class ExpenseParticipantCollection(Resource):
    """Resource for collection of ExpenseParticipant objects in an expense"""
    
    @cache.cached(timeout=30)
    def get(self, expense):
        """Get all participants in an expense"""
        participants = ExpenseParticipant.query.filter_by(expense_id=expense.id).all()
        return {"participants": [participant.serialize() for participant in participants]}, 200

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

# Error handlers
@app.errorhandler(NotFound)
def handle_not_found(error):
    return {"message": str(error)}, 404

@app.errorhandler(BadRequest)
def handle_bad_request(error):
    return {"message": str(error)}, 400

@app.errorhandler(UnsupportedMediaType)
def handle_unsupported_media_type(error):
    return {"message": str(error)}, 415

@app.errorhandler(Conflict)
def handle_conflict(error):
    return {"message": str(error)}, 409

@app.errorhandler(Forbidden)
def handle_forbidden(error):
    return {"message": str(error)}, 403

# Create database tables
@app.before_first_request
def create_tables():
    db.create_all()
        
if __name__ == '__main__':
    app.run(debug=True)