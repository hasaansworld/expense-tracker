"""
Expense tracking application module.

This module initializes the Flask application with database,
caching, and API routing configurations.
"""
import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_caching import Cache
from werkzeug.exceptions import NotFound, Conflict, BadRequest, UnsupportedMediaType, Forbidden

# Import these at the top level to avoid import-outside-toplevel warnings

db = SQLAlchemy()
cache = Cache()

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

    api_bp.errorhandler(NotFound)(handle_not_found)
    api_bp.errorhandler(BadRequest)(handle_bad_request)
    api_bp.errorhandler(UnsupportedMediaType)(handle_unsupported_media_type)
    api_bp.errorhandler(Conflict)(handle_conflict)
    api_bp.errorhandler(Forbidden)(handle_forbidden)

    return app


# json error handlers
def handle_not_found(error):
    """
    Handle 404 Not Found errors by returning JSON response.
    
    Args:
        error: The exception object raised.
        
    Returns:
        tuple: JSON error response and 404 status code.
    """
    return {"message": str(error)}, 404

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
