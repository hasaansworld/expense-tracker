# PWP SPRING 2025

# Expense Tracker API

A Flask based expense tracking API that helps users manage shared expenses within groups.

# Group information

- Student 1. Hasaan Ahmed (hasaan.ahmed@student.oulu.fi)
- Student 2. Aqib Ilyas (aqib.ilyas@student.oulu.fi)
- Student 3. Muhammad Hassan Sultan (hassan.sultan@student.oulu.fi)
- Student 4. Hassan Abudllah

## Dependencies

The project requires the following Python packages:

```
Flask==2.0.1
Flask-SQLAlchemy==2.5.1
SQLAlchemy==1.4.23
Werkzeug==2.0.1
```

You can install all dependencies using:

```bash
pip install -r requirements.txt
```

## Database

The project uses SQLite as the database. The database file will be created as `expense_tracker.db` in the project root directory when you run the population script.

## Setup Instructions

1. Clone the repository:

```bash
git clone git@github.com:hasaansworld/expense-tracker.git
cd expense-tracker
```

2. Create and activate a virtual environment (optional but recommended):

```bash
python -m venv venv
source venv/bin/activate  # On Windows use: venv\Scripts\activate
```

3. Install dependencies:

```bash
pip install -r requirements.txt
```

4. Create and populate the database:

```bash
python populate_db.py
```

This will create the database with sample data including:

- Three users (John, Jane, and Bob)
- A group called "Roommates"
- A sample expense for groceries
- Sample balances between users
- A sample payment

## Testing

To run the tests:

```bash
python -m unittest test_models.py
```

The tests use an in-memory SQLite database and verify:

- Model creation
- Relationships between models
- Data integrity
- Basic CRUD operations

**Remember to include all required documentation and HOWTOs, including how to create and populate the database, how to run and test the API, the url to the entrypoint, instructions on how to setup and run the client, instructions on how to setup and run the axiliary service and instructions on how to deploy the api in a production environment**
