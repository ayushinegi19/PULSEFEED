from datetime import datetime
from flask_login import UserMixin
from . import db


class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    preferences = db.relationship(
        "UserPreference", backref="user", uselist=False
    )
    saved_articles = db.relationship(
        "SavedArticle", backref="user", lazy=True
    )


class UserPreference(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"))
    categories = db.Column(db.String(255))
    sources = db.Column(db.String(255))
    countries = db.Column(db.String(100))

    # Phase 6: Newsletter / email digest
    newsletter_opt_in = db.Column(db.Boolean, default=False, nullable=False)
    digest_frequency = db.Column(db.String(20), default="daily")


class SavedArticle(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"))
    title = db.Column(db.String(255))
    description = db.Column(db.Text)
    url = db.Column(db.String(255))
    urlToImage = db.Column(db.String(255))
    publishedAt = db.Column(db.String(100))
    source = db.Column(db.String(100))
    saved_at = db.Column(db.DateTime, default=datetime.utcnow)


class CachedArticle(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    cache_key = db.Column(db.String(255), index=True)
    articles_json = db.Column(db.Text)
    fetched_at = db.Column(db.DateTime, default=datetime.utcnow)


class ArticleInteraction(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    url_hash = db.Column(db.String(64), nullable=False, index=True)
    interaction_type = db.Column(db.String(20), nullable=False)
    title = db.Column(db.Text)
    description = db.Column(db.Text)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship("User", backref="interactions")


# ── Phase 5: Trending Topics ──────────────────────────────────────────────

class TrendingTopic(db.Model):
    """A topic flagged as trending (Phase 5)."""
    id = db.Column(db.Integer, primary_key=True)
    topic = db.Column(db.String(255), nullable=False, index=True)
    article_count = db.Column(db.Integer, default=0)
    score = db.Column(db.Float, default=0.0)
    is_flagged = db.Column(db.Boolean, default=False, nullable=False, index=True)
    detected_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


# ── Phase 6: Newsletter / Email Digest ────────────────────────────────────

class NewsletterLog(db.Model):
    """Tracks which articles have been emailed to which user (avoid duplicate sends)."""
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False, index=True)
    article_url = db.Column(db.String(512), nullable=False, index=True)
    article_title = db.Column(db.String(512))
    sent_at = db.Column(db.DateTime, default=datetime.utcnow)
    status = db.Column(db.String(20), default="success")  # success | failed
    error_message = db.Column(db.Text)

    user = db.relationship("User", backref="newsletter_logs")


# ── Phase 7: Public API with Rate-Limited API Keys ──────────────────────────

class ApiKey(db.Model):
    """API key for public API access. Key is stored hashed, never plaintext."""
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False, index=True)
    key_hash = db.Column(db.String(128), nullable=False, unique=True, index=True)
    name = db.Column(db.String(100))
    rate_limit_tier = db.Column(db.String(20), default="free", nullable=False)
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship("User", backref="api_keys")


class ApiKeyUsage(db.Model):
    """Simple usage log for API key requests."""
    id = db.Column(db.Integer, primary_key=True)
    api_key_id = db.Column(db.Integer, db.ForeignKey("api_key.id"), nullable=False, index=True)
    endpoint = db.Column(db.String(255))
    method = db.Column(db.String(10))
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

    api_key = db.relationship("ApiKey", backref="usage_logs")
