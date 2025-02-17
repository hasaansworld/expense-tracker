from flask import Flask
from models import db, User, Group, GroupMember, Expense, ExpenseParticipant, Balance, Payment
from werkzeug.security import generate_password_hash

def create_app():
    app = Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///expense_tracker.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    db.init_app(app)
    return app

def populate_db():
    # Create users
    users = [
        User(
            name='John Doe',
            email='john@example.com',
            password_hash=generate_password_hash('password123')
        ),
        User(
            name='Jane Smith',
            email='jane@example.com',
            password_hash=generate_password_hash('password456')
        ),
        User(
            name='Bob Wilson',
            email='bob@example.com',
            password_hash=generate_password_hash('password789')
        )
    ]
    
    for user in users:
        db.session.add(user)
    db.session.commit()

    # Create a group
    group = Group(
        name='Roommates',
        description='Apartment expenses',
        created_by=users[0].id
    )
    db.session.add(group)
    db.session.commit()

    # Add members to the group
    members = [
        GroupMember(user_id=user.id, group_id=group.id)
        for user in users
    ]
    for member in members:
        db.session.add(member)
    db.session.commit()

    # Create an expense
    expense = Expense(
        group_id=group.id,
        created_by=users[0].id,
        amount=150.00,
        description='Groceries',
        category='Food',
        expense_type='regular'
    )
    db.session.add(expense)
    db.session.commit()

    # Add expense participants
    participants = [
        ExpenseParticipant(
            expense_id=expense.id,
            user_id=users[0].id,
            share=50.00,
            paid=150.00
        ),
        ExpenseParticipant(
            expense_id=expense.id,
            user_id=users[1].id,
            share=50.00,
            paid=0.00
        ),
        ExpenseParticipant(
            expense_id=expense.id,
            user_id=users[2].id,
            share=50.00,
            paid=0.00
        )
    ]
    for participant in participants:
        db.session.add(participant)
    db.session.commit()

    # Create balances
    balances = [
        Balance(
            group_id=group.id,
            user_id=users[1].id,
            owed_to=users[0].id,
            amount=50.00
        ),
        Balance(
            group_id=group.id,
            user_id=users[2].id,
            owed_to=users[0].id,
            amount=50.00
        )
    ]
    for balance in balances:
        db.session.add(balance)
    db.session.commit()

    # Create a payment
    payment = Payment(
        group_id=group.id,
        payer_id=users[1].id,
        receiver_id=users[0].id,
        amount=50.00,
        payment_method='card',
        status='completed'
    )
    db.session.add(payment)
    db.session.commit()

if __name__ == '__main__':
    app = create_app()
    with app.app_context():
        db.create_all()
        populate_db()
        print("Database populated successfully!")
