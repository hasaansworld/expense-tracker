"""
Expense tracking application module.

This module initializes the Flask application with database,
caching, and API routing configurations.
"""
import os
from flask import Flask, redirect, request, jsonify, url_for
from flask_sqlalchemy import SQLAlchemy
from flask_caching import Cache
from werkzeug.exceptions import NotFound, Conflict, BadRequest, UnsupportedMediaType, Forbidden

# Import these at the top level to avoid import-outside-toplevel warnings

db = SQLAlchemy()
cache = Cache()

# json error handlers
def handle_not_found(error):
    """
    Custom 404 error handler that returns a JSON response with the error message first,
    followed by available API endpoints.
    """
    # Define available API endpoints with descriptions and methods.
    available_routes = [
        {
            "url": url_for("api.usercollection", _external=True),
            "description": "Manage users",
            "methods": ["GET", "POST"]
        },
        {
            "url": url_for("api.useritem", user="1", _external=True),
            "description": "Manage a specific user",
            "methods": ["GET", "PUT", "DELETE"]
        },
        {
            "url": url_for("api.groupcollection", _external=True),
            "description": "Manage groups",
            "methods": ["GET", "POST"]
        },
        {
            "url": url_for("api.groupitem", group="1", _external=True),
            "description": "Manage a specific group",
            "methods": ["GET", "PUT", "DELETE"]
        },
        {
            "url": url_for("api.expensecollection", group="1", _external=True),
            "description": "Manage group expenses",
            "methods": ["GET", "POST"]
        },
    ]

    return jsonify({
        "error": "Not Found",
        "message": f"The requested URL {error.description} was not found on the server.",
        "available_routes": available_routes  # This comes last now
    }), 404



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


