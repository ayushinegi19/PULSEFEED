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

    # Feature flags — Phase 2 (ranking)
    ENABLE_HISTORY_RANKING = os.environ.get("ENABLE_HISTORY_RANKING", "true").lower() == "true"
    HISTORY_MIN_INTERACTIONS = int(os.environ.get("HISTORY_MIN_INTERACTIONS", "5"))

<<<<<<< HEAD
    # Feature flags — Phase 5 (trending)
    ENABLE_TRENDING = os.environ.get("ENABLE_TRENDING", "false").lower() == "true"

    # Feature flags — Phase 6 (newsletter / email digest)
    ENABLE_NEWSLETTER = os.environ.get("ENABLE_NEWSLETTER", "false").lower() == "true"
    DIGEST_FREQUENCY = os.environ.get("DIGEST_FREQUENCY", "daily")  # daily | weekly
    DIGEST_MAX_ARTICLES = int(os.environ.get("DIGEST_MAX_ARTICLES", "10"))

    # Flask-Mail — Resend SMTP (https://resend.com)
    # Create a free account at resend.com, get your API key, and set these in .env:
    #   MAIL_USERNAME=resend          (literal string "resend")
    #   MAIL_PASSWORD=re_xxxxx         (your Resend API key)
    #   MAIL_DEFAULT_SENDER=PulseFeed <noreply@yourdomain.com>
    #   (or onboarding@resend.dev for the free sandbox domain)
    MAIL_SERVER = os.environ.get("MAIL_SERVER", "smtp.resend.com")
    MAIL_PORT = int(os.environ.get("MAIL_PORT", "587"))
    MAIL_USE_TLS = os.environ.get("MAIL_USE_TLS", "true").lower() == "true"
    MAIL_USE_SSL = os.environ.get("MAIL_USE_SSL", "false").lower() == "true"
    MAIL_USERNAME = os.environ.get("MAIL_USERNAME", "")
    MAIL_PASSWORD = os.environ.get("MAIL_PASSWORD", "")
    MAIL_DEFAULT_SENDER = os.environ.get("MAIL_DEFAULT_SENDER", "PulseFeed <onboarding@resend.dev>")

    # APScheduler
    SCHEDULER_ENABLED = os.environ.get("SCHEDULER_ENABLED", "true").lower() == "true"

    # Feature flags — Phase 7 (public API)
    ENABLE_PUBLIC_API = os.environ.get("ENABLE_PUBLIC_API", "false").lower() == "true"
    API_RATE_LIMIT_FREE = os.environ.get("API_RATE_LIMIT_FREE", "100 per day")
    API_RATE_LIMIT_PRO = os.environ.get("API_RATE_LIMIT_PRO", "1000 per day")
    API_RATE_LIMIT_ENTERPRISE = os.environ.get("API_RATE_LIMIT_ENTERPRISE", "10000 per day")
    RATELIMIT_STORAGE_URI = os.environ.get("RATELIMIT_STORAGE_URI", "memory://")

=======
>>>>>>> 6f65201d4a2a05204f650ff3813aadaedb7a5197
    # Debug flag
    FLASK_ENV = os.environ.get("FLASK_ENV", "production")
    DEBUG = FLASK_ENV == "development"
