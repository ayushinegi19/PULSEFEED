import logging
from functools import wraps
from flask import (
    request, jsonify, g, current_app, make_response,
)
from datetime import datetime, timedelta

from .. import db
from ..models import ApiKey, ApiKeyUsage, TrendingTopic, ArticleInteraction, User
from ..services.api_key_service import validate_api_key, log_usage, get_tier_limit
from ..services.news_service import fetch_personalized_news
from ..services.ranking_service import rank_articles
from . import api_v1_bp

logger = logging.getLogger(__name__)


def require_api_key(f):
    """Decorator: authenticate via X-API-Key header, log usage, enforce rate limits per tier."""
    @wraps(f)
    def decorated(*args, **kwargs):
        if not current_app.config.get("ENABLE_PUBLIC_API", False):
            return jsonify({"error": "Public API is not enabled"}), 503

        auth_header = request.headers.get("Authorization", "")
        api_key_value = None

        # Accept either "Authorization: Bearer <key>" or "X-API-Key: <key>"
        if auth_header.startswith("Bearer "):
            api_key_value = auth_header[7:]
        else:
            api_key_value = request.headers.get("X-API-Key", "")

        if not api_key_value:
            return jsonify({"error": "Missing API key"}), 401

        api_key = validate_api_key(api_key_value)
        if not api_key:
            return jsonify({"error": "Invalid or inactive API key"}), 401

        g.api_key = api_key

        # Rate limiting per tier
        tier = api_key.rate_limit_tier
        limit_str = get_tier_limit(tier)
        limit_count, _, period = limit_str.partition(" per ")
        limit_count = int(limit_count)
        period = period.strip() if period else "day"

        if period == "day":
            since = datetime.utcnow() - timedelta(days=1)
        elif period == "hour":
            since = datetime.utcnow() - timedelta(hours=1)
        else:
            since = datetime.utcnow() - timedelta(days=1)

        usage_count = (
            ApiKeyUsage.query
            .filter(ApiKeyUsage.api_key_id == api_key.id, ApiKeyUsage.timestamp >= since)
            .count()
        )

        if usage_count >= limit_count:
            resp = jsonify({
                "error": "Rate limit exceeded",
                "limit": limit_str,
                "tier": tier,
            })
            resp.status_code = 429
            resp.headers["Retry-After"] = "3600" if period == "hour" else "86400"
            return resp

        # Log usage
        log_usage(api_key.id, request.path, request.method)

        return f(*args, **kwargs)
    return decorated


@api_v1_bp.route("/articles")
@require_api_key
def get_articles():
    """Get personalized news articles for the API key owner."""
    try:
        user = User.query.get(g.api_key.user_id)
        if not user or not user.preferences:
            return jsonify({"error": "No preferences set for this user"}), 400

        articles = fetch_personalized_news(user.preferences)
        if not articles:
            return jsonify({"results": [], "count": 0})

        if current_app.config.get("ENABLE_HISTORY_RANKING", False):
            min_inter = current_app.config.get("HISTORY_MIN_INTERACTIONS", 5)
            articles = rank_articles(user.id, articles, min_interactions=min_inter)

        return jsonify({
            "results": articles,
            "count": len(articles),
        })
    except Exception as e:
        logger.error("API /articles error: %s", e)
        return jsonify({"error": "Failed to fetch articles"}), 500


@api_v1_bp.route("/trending")
@require_api_key
def get_trending():
    """Get currently-flagged trending topics."""
    try:
        if not current_app.config.get("ENABLE_TRENDING", False):
            return jsonify({"error": "Trending feature is not enabled"}), 503

        trending = TrendingTopic.query.filter_by(is_flagged=True).all()
        results = [
            {
                "topic": t.topic,
                "article_count": t.article_count,
                "score": t.score,
                "detected_at": t.detected_at.isoformat() if t.detected_at else None,
            }
            for t in trending
        ]
        return jsonify({"results": results, "count": len(results)})
    except Exception as e:
        logger.error("API /trending error: %s", e)
        return jsonify({"error": "Failed to fetch trending topics"}), 500


@api_v1_bp.route("/search")
@require_api_key
def search_articles():
    """Search articles by keyword."""
    try:
        query = request.args.get("q", "")
        if not query:
            return jsonify({"error": "Query parameter 'q' is required"}), 400

        user = User.query.get(g.api_key.user_id)
        if not user or not user.preferences:
            return jsonify({"error": "No preferences set for this user"}), 400

        articles = fetch_personalized_news(user.preferences)
        if not articles:
            return jsonify({"results": [], "count": 0})

        query_lower = query.lower()
        filtered = [
            a for a in articles
            if query_lower in (a.get("title") or "").lower()
            or query_lower in (a.get("description") or "").lower()
            or query_lower in (a.get("source") or "").lower()
        ]

        return jsonify({"results": filtered, "count": len(filtered)})
    except Exception as e:
        logger.error("API /search error: %s", e)
        return jsonify({"error": "Failed to search articles"}), 500


@api_v1_bp.route("/key/info")
@require_api_key
def key_info():
    """Return info about the current API key."""
    return jsonify({
        "key_id": g.api_key.id,
        "name": g.api_key.name,
        "tier": g.api_key.rate_limit_tier,
        "is_active": g.api_key.is_active,
        "created_at": g.api_key.created_at.isoformat() if g.api_key.created_at else None,
    })
