from flask import Blueprint

auth_bp = Blueprint("auth", __name__)
news_bp = Blueprint("news", __name__)
prefs_bp = Blueprint("preferences", __name__)
saved_bp = Blueprint("saved", __name__)
health_bp = Blueprint("health", __name__)
api_keys_bp = Blueprint("api_keys", __name__)
api_v1_bp = Blueprint("api_v1", __name__, url_prefix="/api/v1")