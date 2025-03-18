"""
Expense tracking application module.

This module initializes the Flask application with database,
caching, and API routing configurations.
"""
import os, json
from flask import Flask, redirect, request, Response, url_for
from flask_sqlalchemy import SQLAlchemy
from flask_caching import Cache
from werkzeug.exceptions import NotFound, Conflict, BadRequest, UnsupportedMediaType, Forbidden

# Import these at the top level to avoid import-outside-toplevel warnings

db = SQLAlchemy()
cache = Cache()



def handle_not_found(error):
    """
    Custom 404 error handler that returns a JSON response with the error message first,
    followed by available API endpoints.
    """
    response_data = {
        "error": "Not Found",
        "message": "The requested URL was not found on the server.",
        "available_routes": {
            "User Endpoints": [
                {"method": "GET", "url": "/api/users/", "description": "Get all users"},
                {"method": "POST", "url": "/api/users/", "description": "Create a new user"},
                {"method": "GET", "url": "/api/users/<user_id>", "description": "Get a specific user"},
                {"method": "PUT", "url": "/api/users/<user_id>", "description": "Update a user"},
                {"method": "DELETE", "url": "/api/users/<user_id>", "description": "Delete a user"}
            ],
            "Group Endpoints": [
                {"method": "GET", "url": "/api/groups/", "description": "Get all groups"},
                {"method": "POST", "url": "/api/groups/", "description": "Create a new group"},
                {"method": "GET", "url": "/api/groups/<group_id>", "description": "Get a specific group"},
                {"method": "PUT", "url": "/api/groups/<group_id>", "description": "Update a group"},
                {"method": "DELETE", "url": "/api/groups/<group_id>", "description": "Delete a group"}
            ],
            "Expense Endpoints": [
                {"method": "GET", "url": "/api/groups/<group_id>/expenses/", "description": "Get all expenses in a group"},
                {"method": "POST", "url": "/api/groups/<group_id>/expenses/", "description": "Create a new expense in a group"},
                {"method": "GET", "url": "/api/expenses/<expense_id>", "description": "Get a specific expense"},
                {"method": "PUT", "url": "/api/expenses/<expense_id>", "description": "Update an expense"},
                {"method": "DELETE", "url": "/api/expenses/<expense_id>", "description": "Delete an expense"}
            ]
        }
    }

    # Convert to JSON string with `ensure_ascii=False` to prevent escaping
    response_json = json.dumps(response_data, ensure_ascii=False, indent=4)

    return Response(response_json, status=404, mimetype="application/json")




def handle_bad_request(error):
    """
    Handle 400 Bad Request errors by returning JSON response.
    
    Args:
        error: The exception object raised.
        
    Returns:
        tuple: JSON error response and 400 status code.
    """
    return {"message": str(error)}, 400

def handle_unsupported_media_type(error):
    """
    Handle 415 Unsupported Media Type errors by returning JSON response.
    
    Args:
        error: The exception object raised.
        
    Returns:
        tuple: JSON error response and 415 status code.
    """
    return {"message": str(error)}, 415

def handle_conflict(error):
    """
    Handle 409 Conflict errors by returning JSON response.
    
    Args:
        error: The exception object raised.
        
    Returns:
        tuple: JSON error response and 409 status code.
    """
    return {"message": str(error)}, 409

def handle_forbidden(error):
    """
    Handle 403 Forbidden errors by returning JSON response.
    
    Args:
        error: The exception object raised.
        
    Returns:
        tuple: JSON error response and 403 status code.
    """
    return {"message": str(error)}, 403






def create_app(test_config=None):
    """
    Create and configure the Flask application.
    
    Args:
        test_config (dict, optional): Test configuration to override default settings.
        
    Returns:
        Flask: Configured Flask application instance.
    """
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_mapping(
        SECRET_KEY="dev",
        SQLALCHEMY_DATABASE_URI="sqlite:///" + os.path.join(app.instance_path, "development.db"),
        SQLALCHEMY_TRACK_MODIFICATIONS=False,
        CACHE_TYPE="FileSystemCache",
        CACHE_DIR=os.path.join(app.instance_path, "cache"),
    )

    if test_config is None:
        app.config.from_pyfile("config.py", silent=True)
    else:
        app.config.from_mapping(test_config)

    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass

    db.init_app(app)
    cache.init_app(app)

    from expenses.models import init_db_command
    from expenses.utils import UserConverter, GroupConverter, ExpenseConverter
    
    app.cli.add_command(init_db_command)

    # Register URL converters
    app.url_map.converters['user'] = UserConverter
    app.url_map.converters['group'] = GroupConverter
    app.url_map.converters['expense'] = ExpenseConverter


    from expenses.api import api_bp
    
    app.register_blueprint(api_bp)

    @app.before_request
    def redirect_if_missing_api():

        path = request.path
        valid_api_routes = ["/users", "/groups", "/expenses"]

        for route in valid_api_routes:
            if path.startswith(route) and not path.startswith("/api"):
                return redirect(f"/api{path}/", code=301)  # Permanent redirect

    app.errorhandler(NotFound)(handle_not_found)
    app.errorhandler(BadRequest)(handle_bad_request)
    app.errorhandler(UnsupportedMediaType)(handle_unsupported_media_type)
    app.errorhandler(Conflict)(handle_conflict)
    app.errorhandler(Forbidden)(handle_forbidden)


    

    return app


