import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY")

    # Database: prefer Neon/Postgres via DATABASE_URL; fall back to local sqlite
    DATABASE_URL = os.environ.get("DATABASE_URL")
    if DATABASE_URL:
        SQLALCHEMY_DATABASE_URI = DATABASE_URL
    else:
        SQLALCHEMY_DATABASE_URI = os.environ.get(
            "SQLALCHEMY_DATABASE_URI", "sqlite:///database.db"
        )

    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # NewsData.io
    NEWSDATA_API_KEY = os.environ.get("NEWSDATA_API_KEY", "")
    NEWSDATA_BASE_URL = "https://newsdata.io/api/1"
    NEWSDATA_TIMEOUT = int(os.environ.get("NEWSDATA_TIMEOUT", "15"))

    # Cache TTL in seconds (default 10 min)
    NEWS_CACHE_TTL = int(os.environ.get("NEWS_CACHE_TTL", "600"))

    # Feature flags
    ENABLE_HISTORY_RANKING = os.environ.get("ENABLE_HISTORY_RANKING", "true").lower() == "true"
    HISTORY_MIN_INTERACTIONS = int(os.environ.get("HISTORY_MIN_INTERACTIONS", "5"))

    ENABLE_CLUSTERING = os.environ.get("ENABLE_CLUSTERING", "true").lower() == "true"
    CLUSTER_SIMILARITY_THRESHOLD = float(os.environ.get("CLUSTER_SIMILARITY_THRESHOLD", "0.5"))

    ENABLE_RELIABILITY = os.environ.get("ENABLE_RELIABILITY", "true").lower() == "true"

    ENABLE_TRENDING = os.environ.get("ENABLE_TRENDING", "true").lower() == "true"
    TRENDING_SPIKE_MULTIPLIER = float(os.environ.get("TRENDING_SPIKE_MULTIPLIER", "2.0"))
    TRENDING_WINDOW_HOURS = int(os.environ.get("TRENDING_WINDOW_HOURS", "6"))
    TRENDING_BASELINE_DAYS = int(os.environ.get("TRENDING_BASELINE_DAYS", "7"))

    # Debug flag
    FLASK_ENV = os.environ.get("FLASK_ENV", "production")
    DEBUG = FLASK_ENV == "development"
