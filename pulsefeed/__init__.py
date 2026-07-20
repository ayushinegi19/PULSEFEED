from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_migrate import Migrate
from werkzeug.routing import BuildError
import logging
import sys
import flask

db = SQLAlchemy()
login_manager = LoginManager()
migrate = Migrate()

BARE_ENDPOINT_MAP = {
    "index": "news.index",
    "get_news": "news.get_news",
    "search_news": "news.search_news",
    "log_interaction": "news.log_interaction",
    "login": "auth.login",
    "register": "auth.register",
    "logout": "auth.logout",
    "set_preferences": "preferences.set_preferences",
    "saved": "saved.saved",
    "save_article": "saved.save_article",
    "get_saved_articles": "saved.get_saved_articles",
    "delete_saved_article": "saved.delete_saved_article",
    "search_saved_articles": "saved.search_saved_articles",
    "manage_keys": "api_keys.manage_keys",
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
    migrate.init_app(app, db)

    # Models must be imported before create_all so tables register
    from . import models  # noqa: F401

    # Register blueprints
    from .routes.auth import auth_bp
    from .routes.news import news_bp
    from .routes.preferences import prefs_bp
    from .routes.saved import saved_bp
    from .routes.health import health_bp
    from .routes.api_keys import api_keys_bp
    from .routes.api_v1 import api_v1_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(news_bp)
    app.register_blueprint(prefs_bp)
    app.register_blueprint(saved_bp)
    app.register_blueprint(health_bp)
    app.register_blueprint(api_keys_bp)
    app.register_blueprint(api_v1_bp)

    # Phase 6: Initialize Flask-Mail when newsletter is enabled
    if app.config.get("ENABLE_NEWSLETTER", False):
        from .services.email_service import init_mail
        init_mail(app)

    # Phase 6: Start APScheduler when enabled
    if app.config.get("SCHEDULER_ENABLED", True):
        from .scheduler import init_scheduler
        init_scheduler(app)

    # Handle bare endpoint names in url_for (templates use unqualified names)
    def _remap_bare_endpoint(error, endpoint, values):
        if endpoint in BARE_ENDPOINT_MAP:
            return flask.url_for(BARE_ENDPOINT_MAP[endpoint], **values)
        raise error

    app.url_build_error_handlers.append(_remap_bare_endpoint)

    return app