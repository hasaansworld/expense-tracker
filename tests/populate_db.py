import os
from flask import Flask
from app.models import db, User, Group, GroupMember, Expense, ExpenseParticipant
from werkzeug.security import generate_password_hash

def create_app():
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    db_path = os.path.join(project_root, 'expense_tracker.db')
    app = Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{db_path}'
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
    # Make the first user an admin
    members[0].role = 'admin'
    
    for member in members:
        db.session.add(member)
    db.session.commit()

    # Create an expense
    expense = Expense(
        group_id=group.id,
        created_by=users[0].id,
        amount=150.00,
        description='Groceries',
        category='Food'
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

if __name__ == '__main__':
    app = create_app()
    with app.app_context():
        db.create_all()
        populate_db()
        print("Database populated successfully!")