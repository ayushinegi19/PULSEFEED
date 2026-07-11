from flask import Blueprint

auth_bp = Blueprint("auth", __name__)
news_bp = Blueprint("news", __name__)
prefs_bp = Blueprint("preferences", __name__)
saved_bp = Blueprint("saved", __name__)
health_bp = Blueprint("health", __name__)
trending_bp = Blueprint("trending", __name__)
