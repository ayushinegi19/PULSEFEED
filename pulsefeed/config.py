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

    # Debug flag
    FLASK_ENV = os.environ.get("FLASK_ENV", "production")
    DEBUG = FLASK_ENV == "development"
