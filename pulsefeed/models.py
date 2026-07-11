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


class TrendingTopic(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    topic = db.Column(db.String(255), nullable=False, index=True)
    keyword = db.Column(db.String(255), nullable=False)
    article_count = db.Column(db.Integer, default=0)
    baseline_count = db.Column(db.Float, default=0.0)
    multiplier = db.Column(db.Float, default=1.0)
    articles_json = db.Column(db.Text)
    detected_at = db.Column(db.DateTime, default=datetime.utcnow)
