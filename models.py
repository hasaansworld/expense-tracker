from datetime import datetime, UTC
import uuid
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

def get_uuid():
    return str(uuid.uuid4())

def get_current_time():
    return datetime.now(UTC)

class User(db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.String(36), primary_key=True, default=get_uuid)
    name = db.Column(db.String(255), nullable=False)
    email = db.Column(db.String(255), nullable=False, unique=True)
    password_hash = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime(timezone=True), default=get_current_time)
    updated_at = db.Column(db.DateTime(timezone=True), default=get_current_time, onupdate=get_current_time)

    # Relationships
    created_groups = db.relationship('Group', backref='creator', lazy=True)
    group_memberships = db.relationship('GroupMember', backref='user', lazy=True)
    created_expenses = db.relationship('Expense', backref='creator', lazy=True)
    expense_participations = db.relationship('ExpenseParticipant', backref='user', lazy=True)

class Group(db.Model):
    __tablename__ = 'groups'
    
    id = db.Column(db.String(36), primary_key=True, default=get_uuid)
    name = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text)
    created_by = db.Column(db.String(36), db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    created_at = db.Column(db.DateTime(timezone=True), default=get_current_time)
    updated_at = db.Column(db.DateTime(timezone=True), default=get_current_time, onupdate=get_current_time)

    # Relationships
    members = db.relationship('GroupMember', backref='group', lazy=True)
    expenses = db.relationship('Expense', backref='group', lazy=True)
    balances = db.relationship('Balance', backref='group', lazy=True)

class GroupMember(db.Model):
    __tablename__ = 'group_members'
    
    id = db.Column(db.String(36), primary_key=True, default=get_uuid)
    user_id = db.Column(db.String(36), db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    group_id = db.Column(db.String(36), db.ForeignKey('groups.id', ondelete='CASCADE'), nullable=False)
    role = db.Column(db.String(50), default='member')
    joined_at = db.Column(db.DateTime(timezone=True), default=get_current_time)

class Expense(db.Model):
    __tablename__ = 'expenses'
    
    id = db.Column(db.String(36), primary_key=True, default=get_uuid)
    group_id = db.Column(db.String(36), db.ForeignKey('groups.id', ondelete='CASCADE'), nullable=False)
    created_by = db.Column(db.String(36), db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    amount = db.Column(db.Numeric(10, 2), nullable=False)
    description = db.Column(db.Text, nullable=False)
    category = db.Column(db.String(100))
    expense_type = db.Column(db.String(50), default='regular')
    created_at = db.Column(db.DateTime(timezone=True), default=get_current_time)
    updated_at = db.Column(db.DateTime(timezone=True), default=get_current_time, onupdate=get_current_time)

    # Relationships
    participants = db.relationship('ExpenseParticipant', backref='expense', lazy=True)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.amount is not None:
            self.amount = float(self.amount)

class ExpenseParticipant(db.Model):
    __tablename__ = 'expense_participants'
    
    id = db.Column(db.String(36), primary_key=True, default=get_uuid)
    expense_id = db.Column(db.String(36), db.ForeignKey('expenses.id', ondelete='CASCADE'), nullable=False)
    user_id = db.Column(db.String(36), db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    share = db.Column(db.Numeric(10, 2), nullable=False)
    paid = db.Column(db.Numeric(10, 2), default=0)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.share is not None:
            self.share = float(self.share)
        if self.paid is not None:
            self.paid = float(self.paid)

class Balance(db.Model):
    __tablename__ = 'balances'
    
    id = db.Column(db.String(36), primary_key=True, default=get_uuid)
    group_id = db.Column(db.String(36), db.ForeignKey('groups.id', ondelete='CASCADE'), nullable=False)
    user_id = db.Column(db.String(36), db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    owed_to = db.Column(db.String(36), db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    amount = db.Column(db.Numeric(10, 2), nullable=False)
    created_at = db.Column(db.DateTime(timezone=True), default=get_current_time)
    updated_at = db.Column(db.DateTime(timezone=True), default=get_current_time, onupdate=get_current_time)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.amount is not None:
            self.amount = float(self.amount)

class Payment(db.Model):
    __tablename__ = 'payments'
    
    id = db.Column(db.String(36), primary_key=True, default=get_uuid)
    group_id = db.Column(db.String(36), db.ForeignKey('groups.id', ondelete='CASCADE'), nullable=False)
    payer_id = db.Column(db.String(36), db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    receiver_id = db.Column(db.String(36), db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    amount = db.Column(db.Numeric(10, 2), nullable=False)
    stripe_transaction_id = db.Column(db.String(255), unique=True)
    stripe_payment_intent_id = db.Column(db.String(255), unique=True)
    payment_method = db.Column(db.String(50))
    status = db.Column(db.String(20), default='pending')
    created_at = db.Column(db.DateTime(timezone=True), default=get_current_time)
    updated_at = db.Column(db.DateTime(timezone=True), default=get_current_time, onupdate=get_current_time)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.amount is not None:
            self.amount = float(self.amount)
