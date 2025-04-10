# PWP SPRING 2025

# Expense Tracker API

A Flask-based expense tracking API that helps users manage shared expenses within groups.

## Group Information

- Student 1. Hasaan Ahmed (hasaan.ahmed@student.oulu.fi)
- Student 2. Aqib Ilyas (aqib.ilyas@student.oulu.fi)
- Student 3. Muhammad Hassan Sultan (hassan.sultan@student.oulu.fi)
- Student 4. Hassan Abdullah (hassan.abdullah@student.oulu.fi)

## Features

- User management with authentication
- Group creation and membership management
- Expense tracking with participant shares
- API for creating, updating, and querying expenses

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

4. Initialize the database:

```bash
export FLASK_APP=expenses
flask init-db
```

On Windows, use `set FLASK_APP=expenses` instead of `export`.

5. (Optional) Generate test data:

```bash
export FLASK_APP=expenses
flask testgen
```

This will create sample data including:

- Three users (John, Jane, and Bob)
- A "Roommates" group
- A sample expense for groceries
- Sample balances between users

## Running the Application

To start the application:

```bash
export FLASK_APP=expenses
export FLASK_DEBUG=1  # Optional: for development mode
flask run
```

On Windows:

```bash
set FLASK_APP=expenses
set FLASK_DEBUG=1  # Optional: for development mode
flask run
```

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

The project includes both database tests and API resources' tests.

```bash
python -m pytest
```

### Database Tests

To run the db tests:

```bash
python -m pytest tests/db_test.py
```

These tests verify:

- Model creation
- Relationships between models
- Data integrity

### API Tests

To run the API resources' tests:

```bash
python -m pytest tests/api_test.py
```

For more concise output with less traceback information:

```bash
python -m pytest tests/api_test.py -v --no-header --tb=line
```

The API tests verify:

- Endpoint functionality
- Authentication requirements
- Error handling
- Data validation




# Hypermedia Implementation

This API implements **HATEOAS (Hypermedia as the Engine of Application State)** by embedding `_links` in all responses that represent resources. These links describe the available actions the client can take next, making the API self-descriptive and navigable without relying on external documentation.

### Design Goal

Enable clients to dynamically explore and interact with the API using hypermedia controls instead of hardcoding endpoint paths.

---

## Endpoints Enhanced with Hypermedia

Each resource now includes a `_links` object in its JSON response, showing available operations (`self`, `update`, `delete`, etc.) and related sub-resources.

###  `/groups/` – `GroupCollection`

Returns a list of groups with each item containing:

```json
"_links": {
  "self": "/groups/<group_id>",
  "members": { "href": "/groups/<group_id>/members/", "method": "GET" },
  "expenses": { "href": "/groups/<group_id>/expenses/", "method": "GET" }
}
```

---

### `/groups/<group_id>` – `GroupItem`

Returns full group details with:

```json
"_links": {
  "self": "/groups/<group_id>",
  "members": { "href": "/groups/<group_id>/members/", "method": "GET" },
  "expenses": { "href": "/groups/<group_id>/expenses/", "method": "GET" },
  "update": { "href": "/groups/<group_id>", "method": "PUT" },
  "delete": { "href": "/groups/<group_id>", "method": "DELETE" }
}
```

---

### `/groups/<group_id>/members/` – `GroupMemberCollection`

Each member includes:

```json
"_links": {
  "self": "/groups/<group_id>/members/<user_id>",
  "delete": { "href": "/groups/<group_id>/members/<user_id>", "method": "DELETE" },
  "user": { "href": "/users/<user_id>", "method": "GET" }
}
```

---

### `/groups/<group_id>/expenses/` – `ExpenseCollection`

Each expense includes:

```json
"_links": {
  "self": "/expenses/<expense_id>",
  "update": { "href": "/expenses/<expense_id>", "method": "PUT" },
  "delete": { "href": "/expenses/<expense_id>", "method": "DELETE" }
}
```

---

### `/expenses/<expense_id>` – `ExpenseItem`

Full expense object includes:

```json
"_links": {
  "self": "/expenses/<expense_id>",
  "update": { "href": "/expenses/<expense_id>", "method": "PUT" },
  "delete": { "href": "/expenses/<expense_id>", "method": "DELETE" },
  "participants": { "href": "/expenses/<expense_id>/participants/", "method": "GET" }
}
```

---

### `/expenses/<expense_id>/participants/` – `ExpenseParticipantCollection`

Each participant includes:

```json
"_links": {
  "self": "/expenses/<expense_id>/participants/",
  "user": { "href": "/users/<user_id>", "method": "GET" }
}
```

And the collection-level `_links`:

```json
"_links": {
  "self": "/expenses/<expense_id>/participants/",
  "add": { "href": "/expenses/<expense_id>/participants/", "method": "POST" }
}
```

---

### `/users/` – `UserCollection`

Each user includes:

```json
"_links": {
  "self": "/users/<user_id>",
  "update": { "href": "/users/<user_id>", "method": "PUT" }
}
```

---

### `/users/<user_id>` – `UserItem`

```json
"_links": {
  "self": "/users/<user_id>",
  "update": { "href": "/users/<user_id>", "method": "PUT" }
}
```

---

## How It’s Implemented

Hypermedia links are generated dynamically inside each `get()` or `post()` method in the Flask-RESTful resource classes.

- Each link reflects the actual path and available actions for the resource
- Methods and URLs are hardcoded using Python string formatting (e.g., `f"/groups/{group.id}"`)
- `_links` are injected into every resource-level response (`GET`, `POST`, etc.)

---

## Example: Expense Response with Hypermedia

```json
{
  "id": "abc123",
  "amount": 150.00,
  "description": "Groceries",
  "_links": {
    "self": "/expenses/abc123",
    "update": { "href": "/expenses/abc123", "method": "PUT" },
    "delete": { "href": "/expenses/abc123", "method": "DELETE" },
    "participants": { "href": "/expenses/abc123/participants/", "method": "GET" }
  }
}
```


## License

This project is for educational purposes as part of the PWP course at the University of Oulu.
