import os
from flask import request, g
from werkzeug.exceptions import NotFound, Forbidden
from expenses.models import User, ApiKey, Group, Expense
from werkzeug.routing import BaseConverter

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
