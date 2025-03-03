import unittest
from flask import Flask
from app.models import db, User, Group, GroupMember, Expense, ExpenseParticipant
from werkzeug.security import generate_password_hash

class TestModels(unittest.TestCase):
    def setUp(self):
        self.app = Flask(__name__)
        self.app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        self.app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
        db.init_app(self.app)
        
        with self.app.app_context():
            db.create_all()
            
            # Create test user
            self.test_user = User(
                name='Test User',
                email='test@example.com',
                password_hash=generate_password_hash('password123')
            )
            db.session.add(self.test_user)
            db.session.commit()
            
            # Store the user ID for later use
            self.user_id = self.test_user.id

    def tearDown(self):
        with self.app.app_context():
            db.session.remove()
            db.drop_all()

    def test_user_creation(self):
        with self.app.app_context():
            user = User.query.filter_by(email='test@example.com').first()
            self.assertIsNotNone(user)
            self.assertEqual(user.name, 'Test User')

    def test_group_creation(self):
        with self.app.app_context():
            group = Group(
                name='Test Group',
                description='Test Description',
                created_by=self.user_id
            )
            db.session.add(group)
            db.session.commit()

            saved_group = Group.query.filter_by(name='Test Group').first()
            self.assertIsNotNone(saved_group)
            self.assertEqual(saved_group.description, 'Test Description')

    def test_expense_creation(self):
        with self.app.app_context():
            # Create a group first
            group = Group(
                name='Test Group',
                description='Test Description',
                created_by=self.user_id
            )
            db.session.add(group)
            db.session.commit()

            # Create an expense
            expense = Expense(
                group_id=group.id,
                created_by=self.user_id,
                amount=100.00,
                description='Test Expense',
                category='Test Category'
            )
            db.session.add(expense)
            db.session.commit()

            saved_expense = Expense.query.filter_by(description='Test Expense').first()
            self.assertIsNotNone(saved_expense)
            self.assertEqual(float(saved_expense.amount), 100.00)
            self.assertEqual(saved_expense.category, 'Test Category')

    def test_relationships(self):
        with self.app.app_context():
            # Create a group
            group = Group(
                name='Test Group',
                description='Test Description',
                created_by=self.user_id
            )
            db.session.add(group)
            db.session.commit()

            # Create group membership
            membership = GroupMember(
                user_id=self.user_id,
                group_id=group.id,
                role='admin'
            )
            db.session.add(membership)
            db.session.commit()

            # Test relationships
            user = User.query.get(self.user_id)
            self.assertEqual(len(user.group_memberships), 1)
            self.assertEqual(user.group_memberships[0].group, group)
            self.assertEqual(group.members[0].user, user)
            self.assertEqual(group.members[0].role, 'admin')

    def test_expense_participants(self):
        with self.app.app_context():
            # Create a group
            group = Group(
                name='Test Group',
                created_by=self.user_id
            )
            db.session.add(group)
            db.session.commit()

            # Create an expense
            expense = Expense(
                group_id=group.id,
                created_by=self.user_id,
                amount=100.00,
                description='Test Expense',
                category='Food'
            )
            db.session.add(expense)
            db.session.commit()

            # Create expense participant
            participant = ExpenseParticipant(
                expense_id=expense.id,
                user_id=self.user_id,
                share=50.00,
                paid=25.00
            )
            db.session.add(participant)
            db.session.commit()

            # Test relationships and amounts
            saved_expense = Expense.query.get(expense.id)
            self.assertEqual(len(saved_expense.participants), 1)
            self.assertEqual(float(saved_expense.participants[0].share), 50.00)
            self.assertEqual(float(saved_expense.participants[0].paid), 25.00)

    def test_multiple_participants(self):
        with self.app.app_context():
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
                created_by=self.user_id
            )
            db.session.add(group)
            db.session.commit()

            # Add both users as members
            for user_id in [self.user_id, user2.id]:
                membership = GroupMember(
                    user_id=user_id,
                    group_id=group.id
                )
                db.session.add(membership)
            db.session.commit()

            # Create an expense
            expense = Expense(
                group_id=group.id,
                created_by=self.user_id,
                amount=100.00,
                description='Shared Expense'
            )
            db.session.add(expense)
            db.session.commit()

            # First user paid full amount
            participant1 = ExpenseParticipant(
                expense_id=expense.id,
                user_id=self.user_id,
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
            self.assertEqual(len(saved_expense.participants), 2)
            
            # Check if the first user paid more than their share
            user1_participant = ExpenseParticipant.query.filter_by(
                expense_id=expense.id, 
                user_id=self.user_id
            ).first()
            self.assertEqual(float(user1_participant.paid), 100.00)
            self.assertEqual(float(user1_participant.share), 50.00)
            
            # Check if the second user owes money
            user2_participant = ExpenseParticipant.query.filter_by(
                expense_id=expense.id, 
                user_id=user2.id
            ).first()
            self.assertEqual(float(user2_participant.paid), 0.00)
            self.assertEqual(float(user2_participant.share), 50.00)

if __name__ == '__main__':
    unittest.main()