import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_caching import Cache
from models import init_db_command
from api import api_bp
from expenses.utils import UserConverter, GroupConverter, ExpenseConverter
    

db = SQLAlchemy()
cache = Cache()

def create_app(test_config=None):
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

    app.cli.add_command(init_db_command)

    # Register URL converters
    app.url_map.converters['user'] = UserConverter
    app.url_map.converters['group'] = GroupConverter
    app.url_map.converters['expense'] = ExpenseConverter

    app.register_blueprint(api_bp)

    return app