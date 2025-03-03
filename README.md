# PWP SPRING 2025
# Expense Tracker API

A Flask-based expense tracking API that helps users manage shared expenses within groups.

## Group Information

- Student 1. Hasaan Ahmed (hasaan.ahmed@student.oulu.fi)
- Student 2. Aqib Ilyas (aqib.ilyas@student.oulu.fi)
- Student 3. Muhammad Hassan Sultan (hassan.sultan@student.oulu.fi)
- Student 4. Hassan Abdullah

## Features

- User management with authentication
- Group creation and membership management
- Expense tracking with participant shares
- API for creating, updating, and querying expenses

## Dependencies

The project requires the following Python packages:

```
Flask==2.0.1
Flask-RESTful==0.3.9
Flask-SQLAlchemy==2.5.1
Flask-Caching==1.10.1
SQLAlchemy==1.4.23
Werkzeug==2.0.1
jsonschema==4.4.0
pytest==7.0.0
```

You can install all dependencies using:

```bash
pip install -r requirements.txt
```

## Database

The project uses SQLite as the database. The database file will be created as `expense_tracker.db` in the project root directory when you run the application or population script.

## Project Structure

```
expense-tracker/
├── app/
│   ├── models.py    # Database models
│   ├── app.py       # API endpoints and routes
├── tests/
│   ├── test_models.py  # Unit tests for models
│   ├── test_app.py     # Functional tests for API
│   ├── populate_db.py  # Script to populate test data
├── requirements.txt
└── README.md
```

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
python -m tests.populate_db
```

This will create the database with sample data including:
- Three users (John, Jane, and Bob)
- A group called "Roommates"
- A sample expense for groceries
- Sample balances between users

## Running the Application

To start the application:

```bash
python -m app.app
```

The API server will start on `http://localhost:5000/` by default.

## API Endpoints

The API provides the following endpoints:

### User Endpoints
- `GET /api/users/` - Get all users
- `POST /api/users/` - Create a new user
- `GET /api/users/<user_id>` - Get a specific user
- `PUT /api/users/<user_id>` - Update a user
- `DELETE /api/users/<user_id>` - Delete a user

### Group Endpoints
- `GET /api/groups/` - Get all groups
- `POST /api/groups/` - Create a new group
- `GET /api/groups/<group_id>` - Get a specific group
- `PUT /api/groups/<group_id>` - Update a group
- `DELETE /api/groups/<group_id>` - Delete a group

### Group Member Endpoints
- `GET /api/groups/<group_id>/members/` - Get all members of a group
- `POST /api/groups/<group_id>/members/` - Add a member to a group
- `DELETE /api/groups/<group_id>/members/<user_id>` - Remove a member from a group

### Expense Endpoints
- `GET /api/groups/<group_id>/expenses/` - Get all expenses in a group
- `POST /api/groups/<group_id>/expenses/` - Create a new expense in a group
- `GET /api/expenses/<expense_id>` - Get a specific expense
- `PUT /api/expenses/<expense_id>` - Update an expense
- `DELETE /api/expenses/<expense_id>` - Delete an expense

### Expense Participant Endpoints
- `GET /api/expenses/<expense_id>/participants/` - Get all participants in an expense

## Authentication

The API uses API keys for authentication. When creating a user, you'll receive an API key that should be included in the `X-API-Key` header for authenticated requests.

Example:
```bash
curl -X POST \
  http://localhost:5000/api/groups/ \
  -H 'Content-Type: application/json' \
  -H 'X-API-Key: your_api_key' \
  -d '{"name":"New Group","description":"Group description"}'
```

## Testing

The project includes both model tests and API integration tests.

### Model Tests

To run the model tests:

```bash
python -m tests.test_models
```

These tests verify:
- Model creation
- Relationships between models
- Data integrity

### API Tests

To run the API integration tests:

```bash
python -m tests.test_app
```

For more concise output with less traceback information:

```bash
python -m tests.test_app -v --no-header --tb=line
```

The API tests verify:
- Endpoint functionality
- Authentication requirements
- Error handling
- Data validation


## License

This project is for educational purposes as part of the PWP course at the University of Oulu.
