from datetime import datetime, UTC
import uuid
from flask_sqlalchemy import SQLAlchemy
import hashlib

db = SQLAlchemy()

def get_uuid():
    return str(uuid.uuid4())

def get_current_time():
    return datetime.now(UTC)

class User(db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    uuid = db.Column(db.String(36), unique=True, default=get_uuid)
    name = db.Column(db.String(255), nullable=False)
    email = db.Column(db.String(255), nullable=False, unique=True)
    password_hash = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime(timezone=True), default=get_current_time)
    updated_at = db.Column(db.DateTime(timezone=True), default=get_current_time, onupdate=get_current_time)

    # Relationships
    created_groups = db.relationship('Group', backref='creator', lazy=True, cascade="all, delete-orphan")
    group_memberships = db.relationship('GroupMember', backref='user', lazy=True, cascade="all, delete-orphan")
    created_expenses = db.relationship('Expense', backref='creator', lazy=True, cascade="all, delete-orphan")
    expense_participations = db.relationship('ExpenseParticipant', backref='user', lazy=True, cascade="all, delete-orphan")

    def serialize(self, short_form=False):
        """
        Serialize User object to dictionary
        """
        data = {
            "id": self.uuid,
            "name": self.name,
            "email": self.email,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }
        
        if not short_form:
            data["created_groups"] = [group.uuid for group in self.created_groups]
            data["group_memberships"] = [membership.group.uuid for membership in self.group_memberships]
        
        return data
    
    def deserialize(self, data):
        """
        Update User object from dictionary
        """
        if "name" in data:
            self.name = data["name"]
        if "email" in data:
            self.email = data["email"]
        if "password_hash" in data:
            self.password_hash = data["password_hash"]

class ApiKey(db.Model):
    __tablename__ = 'api_keys'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    uuid = db.Column(db.String(36), unique=True, default=get_uuid)
    key_hash = db.Column(db.String(64), nullable=False, unique=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    created_at = db.Column(db.DateTime(timezone=True), default=get_current_time)
    
    # Relationship
    user = db.relationship('User', backref=db.backref('api_keys', lazy=True, cascade="all, delete-orphan"), cascade="all, delete")
    
    @staticmethod
    def get_hash(key):
        """
        Get hash of API key
        """
        return hashlib.sha256(key.encode()).hexdigest()

class Group(db.Model):
    __tablename__ = 'groups'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    uuid = db.Column(db.String(36), unique=True, default=get_uuid)
    name = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text)
    created_by = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    created_at = db.Column(db.DateTime(timezone=True), default=get_current_time)
    updated_at = db.Column(db.DateTime(timezone=True), default=get_current_time, onupdate=get_current_time)

    # Relationships
    members = db.relationship('GroupMember', backref='group', lazy=True, cascade="all, delete-orphan")
    expenses = db.relationship('Expense', backref='group', lazy=True, cascade="all, delete-orphan")
    
    def serialize(self, short_form=False):
        """
        Serialize Group object to dictionary
        """
        data = {
            "id": self.uuid,
            "name": self.name,
            "description": self.description,
            "created_by": self.creator.uuid,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }
        
        if not short_form:
            data["members"] = [member.serialize(short_form=True) for member in self.members]
            data["expenses"] = [expense.uuid for expense in self.expenses]
        
        return data
    
    def deserialize(self, data):
        """
        Update Group object from dictionary
        """
        if "name" in data:
            self.name = data["name"]
        if "description" in data:
            self.description = data["description"]

class GroupMember(db.Model):
    __tablename__ = 'group_members'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    uuid = db.Column(db.String(36), unique=True, default=get_uuid)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    group_id = db.Column(db.Integer, db.ForeignKey('groups.id', ondelete='CASCADE'), nullable=False)
    role = db.Column(db.String(50), default='member')
    joined_at = db.Column(db.DateTime(timezone=True), default=get_current_time)

    def serialize(self, short_form=False):
        """
        Serialize GroupMember object to dictionary
        """
        data = {
            "id": self.uuid,
            "user_id": self.user.uuid,
            "group_id": self.group.uuid,
            "role": self.role,
            "joined_at": self.joined_at.isoformat() if self.joined_at else None
        }
        
        return data
    
    def deserialize(self, data):
        """
        Update GroupMember object from dictionary
        """
        if "role" in data:
            self.role = data["role"]

class Expense(db.Model):
    __tablename__ = 'expenses'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    uuid = db.Column(db.String(36), unique=True, default=get_uuid)
    group_id = db.Column(db.Integer, db.ForeignKey('groups.id', ondelete='CASCADE'), nullable=False)
    created_by = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    amount = db.Column(db.Numeric(10, 2), nullable=False)
    description = db.Column(db.Text, nullable=False)
    category = db.Column(db.String(100))
    created_at = db.Column(db.DateTime(timezone=True), default=get_current_time)
    updated_at = db.Column(db.DateTime(timezone=True), default=get_current_time, onupdate=get_current_time)

    # Relationships
    participants = db.relationship('ExpenseParticipant', backref='expense', lazy=True, cascade="all, delete-orphan")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.amount is not None:
            self.amount = float(self.amount)
    
    def serialize(self, short_form=False):
        """
        Serialize Expense object to dictionary
        """
        data = {
            "id": self.uuid,
            "group_id": self.group.uuid,
            "created_by": self.creator.uuid,
            "amount": float(self.amount) if self.amount is not None else None,
            "description": self.description,
            "category": self.category,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }
        
        if not short_form:
            data["participants"] = [participant.serialize(short_form=True) for participant in self.participants]
        
        return data
    
    def deserialize(self, data):
        """
        Update Expense object from dictionary
        """
        if "amount" in data:
            self.amount = float(data["amount"])
        if "description" in data:
            self.description = data["description"]
        if "category" in data:
            self.category = data["category"]

class ExpenseParticipant(db.Model):
    __tablename__ = 'expense_participants'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    uuid = db.Column(db.String(36), unique=True, default=get_uuid)
    expense_id = db.Column(db.Integer, db.ForeignKey('expenses.id', ondelete='CASCADE'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    share = db.Column(db.Numeric(10, 2), nullable=False)
    paid = db.Column(db.Numeric(10, 2), default=0)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.share is not None:
            self.share = float(self.share)
        if self.paid is not None:
            self.paid = float(self.paid)
    
    def serialize(self, short_form=False):
        """
        Serialize ExpenseParticipant object to dictionary
        """
        data = {
            "id": self.uuid,
            "expense_id": self.expense.uuid,
            "user_id": self.user.uuid,
            "share": float(self.share) if self.share is not None else None,
            "paid": float(self.paid) if self.paid is not None else None
        }
        
        return data
    
    def deserialize(self, data):
        """
        Update ExpenseParticipant object from dictionary
        """
        if "share" in data:
            self.share = float(data["share"])
        if "paid" in data:
            self.paid = float(data["paid"])