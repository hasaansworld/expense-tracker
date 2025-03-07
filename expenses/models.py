"""
Database models for the expense tracking application.

This module defines SQLAlchemy models that represent the main entities in the
expense tracking system: users, groups, expenses, and related relationships.
"""

import hashlib
import uuid
from datetime import datetime, UTC

import click
from flask.cli import with_appcontext
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash

db = SQLAlchemy()


def get_uuid():
    """Generate a unique UUID string for model IDs."""
    return str(uuid.uuid4())


def get_current_time():
    """Get current UTC time for timestamps."""
    return datetime.now(UTC)


class User(db.Model):
    """
    User model representing application users.

    Each user can create groups, be a member of groups, create expenses,
    and participate in expenses.
    """

    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    uuid = db.Column(db.String(36), unique=True, default=get_uuid)
    name = db.Column(db.String(255), nullable=False)
    email = db.Column(db.String(255), nullable=False, unique=True)
    password_hash = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime(timezone=True), default=get_current_time)
    updated_at = db.Column(
        db.DateTime(timezone=True), default=get_current_time, onupdate=get_current_time
    )

    # Relationships
    created_groups = db.relationship(
        "Group", backref="creator", lazy=True, cascade="all, delete-orphan"
    )
    group_memberships = db.relationship(
        "GroupMember", backref="user", lazy=True, cascade="all, delete-orphan"
    )
    created_expenses = db.relationship(
        "Expense", backref="creator", lazy=True, cascade="all, delete-orphan"
    )
    expense_participations = db.relationship(
        "ExpenseParticipant", backref="user", lazy=True, cascade="all, delete-orphan"
    )

    def serialize(self, short_form=False):
        """
        Serialize User object to dictionary.

        Args:
            short_form (bool): Whether to include only basic information.

        Returns:
            dict: Serialized user data.
        """
        data = {
            "id": self.uuid,
            "name": self.name,
            "email": self.email,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

        if not short_form:
            data["created_groups"] = [group.uuid for group in self.created_groups]
            data["group_memberships"] = [
                membership.group.uuid for membership in self.group_memberships
            ]

        return data

    def deserialize(self, data):
        """
        Update User object from dictionary.

        Args:
            data (dict): Dictionary containing user data to update.
        """
        if "name" in data:
            self.name = data["name"]
        if "email" in data:
            self.email = data["email"]
        if "password_hash" in data:
            self.password_hash = data["password_hash"]

    @staticmethod
    def get_schema():
        """
        Get JSON schema for User validation.

        Returns:
            dict: JSON schema for user data validation.
        """
        return {
            "type": "object",
            "required": ["name", "email", "password_hash"],
            "properties": {
                "name": {"type": "string"},
                "email": {"type": "string", "format": "email"},
                "password_hash": {"type": "string"},
            },
        }


class ApiKey(db.Model):
    """
    API Key model for authenticating API requests.

    Each user can have multiple API keys.
    """

    __tablename__ = "api_keys"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    uuid = db.Column(db.String(36), unique=True, default=get_uuid)
    key_hash = db.Column(db.String(64), nullable=False, unique=True)
    user_id = db.Column(
        db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    created_at = db.Column(db.DateTime(timezone=True), default=get_current_time)

    # Relationship
    user = db.relationship(
        "User",
        backref=db.backref("api_keys", lazy=True, cascade="all, delete-orphan"),
        cascade="all, delete",
    )

    def serialize(self, short_form=False):
        """
        Serialize ApiKey object to dictionary.
        
        Args:
            short_form (bool): Whether to include only basic information.
            
        Returns:
            dict: Serialized API key data.
        """
        data = {
            "id": self.uuid,
            "user_id": self.user.uuid,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }
        
        if not short_form:
            # Add additional fields for detailed view if needed
            pass
            
        return data

    @staticmethod
    def get_hash(key):
        """
        Get hash of API key.

        Args:
            key (str): API key to hash.

        Returns:
            str: SHA-256 hash of the API key.
        """
        return hashlib.sha256(key.encode()).hexdigest()


class Group(db.Model):
    """
    Group model representing a collection of users who share expenses.

    Each group can have multiple members and expenses.
    """

    __tablename__ = "groups"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    uuid = db.Column(db.String(36), unique=True, default=get_uuid)
    name = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text)
    created_by = db.Column(
        db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    created_at = db.Column(db.DateTime(timezone=True), default=get_current_time)
    updated_at = db.Column(
        db.DateTime(timezone=True), default=get_current_time, onupdate=get_current_time
    )

    # Relationships
    members = db.relationship(
        "GroupMember", backref="group", lazy=True, cascade="all, delete-orphan"
    )
    expenses = db.relationship(
        "Expense", backref="group", lazy=True, cascade="all, delete-orphan"
    )

    def serialize(self, short_form=False):
        """
        Serialize Group object to dictionary.

        Args:
            short_form (bool): Whether to include only basic information.

        Returns:
            dict: Serialized group data.
        """
        data = {
            "id": self.uuid,
            "name": self.name,
            "description": self.description,
            "created_by": self.creator.uuid,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

        if not short_form:
            data["members"] = [
                member.serialize(short_form=True) for member in self.members
            ]
            data["expenses"] = [expense.uuid for expense in self.expenses]

        return data

    def deserialize(self, data):
        """
        Update Group object from dictionary.

        Args:
            data (dict): Dictionary containing group data to update.
        """
        if "name" in data:
            self.name = data["name"]
        if "description" in data:
            self.description = data["description"]

    @staticmethod
    def get_schema():
        """
        Get JSON schema for Group validation.

        Returns:
            dict: JSON schema for group data validation.
        """
        return {
            "type": "object",
            "required": ["name"],
            "properties": {"name": {"type": "string"}},
        }


class GroupMember(db.Model):
    """
    GroupMember model representing a user's membership in a group.

    Each group member has a role (admin or member).
    """

    __tablename__ = "group_members"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    uuid = db.Column(db.String(36), unique=True, default=get_uuid)
    user_id = db.Column(
        db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    group_id = db.Column(
        db.Integer, db.ForeignKey("groups.id", ondelete="CASCADE"), nullable=False
    )
    role = db.Column(db.String(50), default="member")
    joined_at = db.Column(db.DateTime(timezone=True), default=get_current_time)

    def serialize(self, short_form=False):
        """
        Serialize GroupMember object to dictionary.
        
        Args:
            short_form (bool): Whether to include only basic information.
            
        Returns:
            dict: Serialized group member data.
        """
        data = {
            "id": self.uuid,
            "user_id": self.user.uuid,
            "group_id": self.group.uuid,
            "role": self.role,
            "joined_at": self.joined_at.isoformat() if self.joined_at else None,
        }
        
        if not short_form:
            # Add user name for convenience in the detailed view
            data["user_name"] = self.user.name
            
        return data

    def deserialize(self, data):
        """
        Update GroupMember object from dictionary.

        Args:
            data (dict): Dictionary containing group member data to update.
        """
        if "role" in data:
            self.role = data["role"]


class Expense(db.Model):
    """
    Expense model representing a shared expense within a group.

    Each expense has participants who share the cost.
    """

    __tablename__ = "expenses"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    uuid = db.Column(db.String(36), unique=True, default=get_uuid)
    group_id = db.Column(
        db.Integer, db.ForeignKey("groups.id", ondelete="CASCADE"), nullable=False
    )
    created_by = db.Column(
        db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    amount = db.Column(db.Numeric(10, 2), nullable=False)
    description = db.Column(db.Text, nullable=False)
    category = db.Column(db.String(100))
    created_at = db.Column(db.DateTime(timezone=True), default=get_current_time)
    updated_at = db.Column(
        db.DateTime(timezone=True), default=get_current_time, onupdate=get_current_time
    )

    # Relationships
    participants = db.relationship(
        "ExpenseParticipant", backref="expense", lazy=True, cascade="all, delete-orphan"
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.amount is not None:
            self.amount = float(self.amount)

    def serialize(self, short_form=False):
        """
        Serialize Expense object to dictionary.

        Args:
            short_form (bool): Whether to include only basic information.

        Returns:
            dict: Serialized expense data.
        """
        data = {
            "id": self.uuid,
            "group_id": self.group.uuid,
            "created_by": self.creator.uuid,
            "amount": float(self.amount) if self.amount is not None else None,
            "description": self.description,
            "category": self.category,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

        if not short_form:
            data["participants"] = [
                participant.serialize(short_form=True)
                for participant in self.participants
            ]

        return data

    def deserialize(self, data):
        """
        Update Expense object from dictionary.

        Args:
            data (dict): Dictionary containing expense data to update.
        """
        if "amount" in data:
            self.amount = float(data["amount"])
        if "description" in data:
            self.description = data["description"]
        if "category" in data:
            self.category = data["category"]

    @staticmethod
    def get_schema():
        """
        Get JSON schema for Expense validation.

        Returns:
            dict: JSON schema for expense data validation.
        """
        return {
            "type": "object",
            "required": ["amount", "description"],
            "properties": {
                "amount": {"type": "number", "minimum": 0},
                "description": {"type": "string"},
            },
        }


class ExpenseParticipant(db.Model):
    """
    ExpenseParticipant model representing a user's participation in an expense.

    Each participant has a share of the expense and an amount they paid.
    """

    __tablename__ = "expense_participants"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    uuid = db.Column(db.String(36), unique=True, default=get_uuid)
    expense_id = db.Column(
        db.Integer, db.ForeignKey("expenses.id", ondelete="CASCADE"), nullable=False
    )
    user_id = db.Column(
        db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    share = db.Column(db.Numeric(10, 2), nullable=False)
    paid = db.Column(db.Numeric(10, 2), default=0)

    def __init__(self, *args, **kwargs):
        """Initialize ExpenseParticipant with type conversion for numeric values."""
        super().__init__(*args, **kwargs)
        if self.share is not None:
            self.share = float(self.share)
        if self.paid is not None:
            self.paid = float(self.paid)

    def serialize(self, short_form=False):
        """
        Serialize ExpenseParticipant object to dictionary.
        
        Args:
            short_form (bool): Whether to include only basic information.
            
        Returns:
            dict: Serialized expense participant data.
        """
        data = {
            "id": self.uuid,
            "expense_id": self.expense.uuid,
            "user_id": self.user.uuid,
            "share": float(self.share) if self.share is not None else None,
            "paid": float(self.paid) if self.paid is not None else None,
        }
        
        if not short_form:
            # Add user name and balance information for a more detailed view
            data["user_name"] = self.user.name
            data["balance"] = float(self.paid) - float(self.share) if (self.paid is not None and self.share is not None) else None
            
        return data

    def deserialize(self, data):
        """
        Update ExpenseParticipant object from dictionary.

        Args:
            data (dict): Dictionary containing expense participant data to update.
        """
        if "share" in data:
            self.share = float(data["share"])
        if "paid" in data:
            self.paid = float(data["paid"])

    @staticmethod
    def get_schema():
        """
        Get JSON schema for ExpenseParticipant validation.

        Returns:
            dict: JSON schema for expense participant data validation.
        """
        return {
            "type": "object",
            "required": ["user_id", "share"],
            "properties": {
                "user_id": {"type": "string"},
                "share": {"type": "number", "minimum": 0},
            },
        }


@click.command("init-db")
@with_appcontext
def init_db_command():
    """Initialize the database with required tables."""
    db.create_all()


@click.command("testgen")
@with_appcontext
def generate_test_data():
    """Generate test data for the expense tracker application."""
    try:
        # Create users
        users = [
            User(
                name="John Doe",
                email="john@example.com",
                password_hash=generate_password_hash("password123"),
            ),
            User(
                name="Jane Smith",
                email="jane@example.com",
                password_hash=generate_password_hash("password456"),
            ),
            User(
                name="Bob Wilson",
                email="bob@example.com",
                password_hash=generate_password_hash("password789"),
            ),
        ]

        for user in users:
            db.session.add(user)
        db.session.commit()

        # Create a group
        group = Group(
            name="Roommates", description="Apartment expenses", created_by=users[0].id
        )
        db.session.add(group)
        db.session.commit()

        # Add members to the group
        members = [GroupMember(user_id=user.id, group_id=group.id) for user in users]
        # Make the first user an admin
        members[0].role = "admin"

        for member in members:
            db.session.add(member)
        db.session.commit()

        # Create an expense
        expense = Expense(
            group_id=group.id,
            created_by=users[0].id,
            amount=150.00,
            description="Groceries",
            category="Food",
        )
        db.session.add(expense)
        db.session.commit()

        # Add expense participants
        participants = [
            ExpenseParticipant(
                expense_id=expense.id, user_id=users[0].id, share=50.00, paid=150.00
            ),
            ExpenseParticipant(
                expense_id=expense.id, user_id=users[1].id, share=50.00, paid=0.00
            ),
            ExpenseParticipant(
                expense_id=expense.id, user_id=users[2].id, share=50.00, paid=0.00
            ),
        ]
        for participant in participants:
            db.session.add(participant)
        db.session.commit()

        click.echo("Test data generated successfully!")
    except Exception as e:  # pylint: disable=broad-exception-caught
        click.echo(f"Error generating test data: {str(e)}", err=True)
