from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from werkzeug.routing import BuildError
import logging
import sys
import flask

db = SQLAlchemy()
login_manager = LoginManager()

# Map bare endpoint names (used in templates) to blueprint-qualified endpoints
BARE_ENDPOINT_MAP = {
    "index": "news.index",
    "get_news": "news.get_news",
    "search_news": "news.search_news",
    "login": "auth.login",
    "register": "auth.register",
    "logout": "auth.logout",
    "set_preferences": "preferences.set_preferences",
    "saved": "saved.saved",
    "save_article": "saved.save_article",
    "get_saved_articles": "saved.get_saved_articles",
    "delete_saved_article": "saved.delete_saved_article",
    "search_saved_articles": "saved.search_saved_articles",
}


def create_app(config_class=None):
    app = Flask(
        __name__,
        template_folder="templates",
        static_folder="static",
    )

    if config_class is None:
        from .config import Config
        config_class = Config

    app.config.from_object(config_class)

    # Logging
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(
        logging.Formatter(
            "%(asctime)s %(levelname)s [%(name)s] %(message)s"
        )
    )
    app.logger.addHandler(handler)
    app.logger.setLevel(logging.DEBUG if app.config.get("DEBUG") else logging.INFO)

    # Extensions
    db.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = "auth.login"

    # Models must be imported before create_all so tables register
    from . import models  # noqa: F401

    # Register blueprints
    from .routes.auth import auth_bp
    from .routes.news import news_bp
    from .routes.preferences import prefs_bp
    from .routes.saved import saved_bp
    from .routes.health import health_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(news_bp)
    app.register_blueprint(prefs_bp)
    app.register_blueprint(saved_bp)
    app.register_blueprint(health_bp)

    # Handle bare endpoint names in url_for (templates use unqualified names)
    def _remap_bare_endpoint(error, endpoint, values):
        if endpoint in BARE_ENDPOINT_MAP:
            return flask.url_for(BARE_ENDPOINT_MAP[endpoint], **values)
        raise error

    app.url_build_error_handlers.append(_remap_bare_endpoint)

    with app.app_context():
        db.create_all()

    return app
