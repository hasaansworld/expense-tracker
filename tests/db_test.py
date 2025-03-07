import pytest
from flask import Flask
from expenses.models import db, User, Group, GroupMember, Expense, ExpenseParticipant
from werkzeug.security import generate_password_hash


@pytest.fixture
def app():
    app = Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    db.init_app(app)
    
    return app


@pytest.fixture
def client(app):
    with app.app_context():
        db.create_all()
        
        # Create test user
        test_user = User(
            name='Test User',
            email='test@example.com',
            password_hash=generate_password_hash('password123')
        )
        db.session.add(test_user)
        db.session.commit()
        
        user_id = test_user.id
        
        yield {'app': app, 'user_id': user_id}
        
        db.session.remove()
        db.drop_all()


def test_user_creation(client):
    with client['app'].app_context():
        user = User.query.filter_by(email='test@example.com').first()
        assert user is not None
        assert user.name == 'Test User'


def test_group_creation(client):
    with client['app'].app_context():
        group = Group(
            name='Test Group',
            description='Test Description',
            created_by=client['user_id']
        )
        db.session.add(group)
        db.session.commit()

        saved_group = Group.query.filter_by(name='Test Group').first()
        assert saved_group is not None
        assert saved_group.description == 'Test Description'


def test_expense_creation(client):
    with client['app'].app_context():
        # Create a group first
        group = Group(
            name='Test Group',
            description='Test Description',
            created_by=client['user_id']
        )
        db.session.add(group)
        db.session.commit()

        # Create an expense
        expense = Expense(
            group_id=group.id,
            created_by=client['user_id'],
            amount=100.00,
            description='Test Expense',
            category='Test Category'
        )
        db.session.add(expense)
        db.session.commit()

        saved_expense = Expense.query.filter_by(description='Test Expense').first()
        assert saved_expense is not None
        assert float(saved_expense.amount) == 100.00
        assert saved_expense.category == 'Test Category'


def test_relationships(client):
    with client['app'].app_context():
        # Create a group
        group = Group(
            name='Test Group',
            description='Test Description',
            created_by=client['user_id']
        )
        db.session.add(group)
        db.session.commit()

        # Create group membership
        membership = GroupMember(
            user_id=client['user_id'],
            group_id=group.id,
            role='admin'
        )
        db.session.add(membership)
        db.session.commit()

        # Test relationships
        user = User.query.get(client['user_id'])
        assert len(user.group_memberships) == 1
        assert user.group_memberships[0].group == group
        assert group.members[0].user == user
        assert group.members[0].role == 'admin'


def test_expense_participants(client):
    with client['app'].app_context():
        # Create a group
        group = Group(
            name='Test Group',
            created_by=client['user_id']
        )
        db.session.add(group)
        db.session.commit()

        # Create an expense
        expense = Expense(
            group_id=group.id,
            created_by=client['user_id'],
            amount=100.00,
            description='Test Expense',
            category='Food'
        )
        db.session.add(expense)
        db.session.commit()

        # Create expense participant
        participant = ExpenseParticipant(
            expense_id=expense.id,
            user_id=client['user_id'],
            share=50.00,
            paid=25.00
        )
        db.session.add(participant)
        db.session.commit()

        # Test relationships and amounts
        saved_expense = Expense.query.get(expense.id)
        assert len(saved_expense.participants) == 1
        assert float(saved_expense.participants[0].share) == 50.00
        assert float(saved_expense.participants[0].paid) == 25.00


def test_multiple_participants(client):
    with client['app'].app_context():
        # Create another user
        user2 = User(
            name='Test User 2',
            email='test2@example.com',
            password_hash=generate_password_hash('password456')
        )
        db.session.add(user2)
        db.session.commit()

        # Create a group
        group = Group(
            name='Test Group',
            created_by=client['user_id']
        )
        db.session.add(group)
        db.session.commit()

        # Add both users as members
        for user_id in [client['user_id'], user2.id]:
            membership = GroupMember(
                user_id=user_id,
                group_id=group.id
            )
            db.session.add(membership)
        db.session.commit()

        # Create an expense
        expense = Expense(
            group_id=group.id,
            created_by=client['user_id'],
            amount=100.00,
            description='Shared Expense'
        )
        db.session.add(expense)
        db.session.commit()

        # First user paid full amount
        participant1 = ExpenseParticipant(
            expense_id=expense.id,
            user_id=client['user_id'],
            share=50.00,
            paid=100.00
        )
        # Second user owes their share
        participant2 = ExpenseParticipant(
            expense_id=expense.id,
            user_id=user2.id,
            share=50.00,
            paid=0.00
        )
        db.session.add_all([participant1, participant2])
        db.session.commit()

        # Test expense participants
        saved_expense = Expense.query.get(expense.id)
        assert len(saved_expense.participants) == 2
        
        # Check if the first user paid more than their share
        user1_participant = ExpenseParticipant.query.filter_by(
            expense_id=expense.id, 
            user_id=client['user_id']
        ).first()
        assert float(user1_participant.paid) == 100.00
        assert float(user1_participant.share) == 50.00
        
        # Check if the second user owes money
        user2_participant = ExpenseParticipant.query.filter_by(
            expense_id=expense.id, 
            user_id=user2.id
        ).first()
        assert float(user2_participant.paid) == 0.00
        assert float(user2_participant.share) == 50.00