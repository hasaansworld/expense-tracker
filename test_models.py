import unittest
from flask import Flask
from models import db, User, Group, GroupMember, Expense, ExpenseParticipant, Balance, Payment
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
                description='Test Expense'
            )
            db.session.add(expense)
            db.session.commit()

            saved_expense = Expense.query.filter_by(description='Test Expense').first()
            self.assertIsNotNone(saved_expense)
            self.assertEqual(float(saved_expense.amount), 100.00)

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
                group_id=group.id
            )
            db.session.add(membership)
            db.session.commit()

            # Test relationships
            user = User.query.get(self.user_id)
            self.assertEqual(len(user.group_memberships), 1)
            self.assertEqual(user.group_memberships[0].group, group)
            self.assertEqual(group.members[0].user, user)

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
                description='Test Expense'
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

    def test_balance_creation(self):
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

            # Create balance
            balance = Balance(
                group_id=group.id,
                user_id=user2.id,
                owed_to=self.user_id,
                amount=75.50
            )
            db.session.add(balance)
            db.session.commit()

            # Test balance
            saved_balance = Balance.query.filter_by(user_id=user2.id).first()
            self.assertIsNotNone(saved_balance)
            self.assertEqual(float(saved_balance.amount), 75.50)

    def test_payment_creation(self):
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

            # Create payment
            payment = Payment(
                group_id=group.id,
                payer_id=user2.id,
                receiver_id=self.user_id,
                amount=100.00,
                payment_method='card',
                status='completed'
            )
            db.session.add(payment)
            db.session.commit()

            # Test payment
            saved_payment = Payment.query.filter_by(payer_id=user2.id).first()
            self.assertIsNotNone(saved_payment)
            self.assertEqual(float(saved_payment.amount), 100.00)
            self.assertEqual(saved_payment.status, 'completed')

if __name__ == '__main__':
    unittest.main()
