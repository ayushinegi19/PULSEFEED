import logging
from flask import render_template, jsonify, request, redirect, url_for
from flask_login import login_required, current_user

from ..services.news_service import fetch_personalized_news
from . import news_bp

logger = logging.getLogger(__name__)


@news_bp.route("/")
@login_required
def index():
    if not current_user.preferences:
        return redirect(url_for("preferences.set_preferences"))
    return render_template("index.html")


@news_bp.route("/get_news")
@login_required
def get_news():
    try:
        if not current_user.preferences:
            return jsonify({"error": "Set preferences first"})

        news = fetch_personalized_news(current_user.preferences)

        if not news:
            return jsonify(
                {"error": "No news articles found for selected preferences."}
            )

        return jsonify(news)

    except Exception as e:
        logger.error("Error fetching news: %s", str(e), exc_info=True)
        return jsonify(
            {"error": "Failed to fetch news. Please try again later."}
        ), 500


@news_bp.route("/search_news")
@login_required
def search_news():
    try:
        query = request.args.get("query", "")
        if not query:
            return jsonify({"error": "Search query is required"}), 400

        if not current_user.preferences:
            return jsonify({"error": "Set preferences first"})

        news = fetch_personalized_news(current_user.preferences)

        if not news:
            return jsonify(
                {"error": "No news articles found for your preferences."}
            )

        query = query.lower()
        filtered_news = [
            article
            for article in news
            if (
                query in article.get("title", "").lower()
                or query in (article.get("description", "") or "").lower()
                or query in article.get("source", "").lower()
            )
        ]

        return jsonify(filtered_news)

    except Exception as e:
        logger.error("Error searching news: %s", str(e), exc_info=True)
        return jsonify(
            {"error": "Failed to search news. Please try again later."}
        ), 500
