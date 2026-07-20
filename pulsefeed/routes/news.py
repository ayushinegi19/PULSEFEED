import logging
from flask import render_template, jsonify, request, redirect, url_for, current_app
from flask_login import login_required, current_user

from ..services.news_service import fetch_personalized_news
from ..services.ranking_service import rank_articles, log_interaction
from . import news_bp

logger = logging.getLogger(__name__)


@news_bp.route("/")
@login_required
def index():
    if not current_user.preferences:
        return redirect(url_for("preferences.set_preferences"))
    return render_template(
        "index.html",
        enable_public_api=current_app.config.get("ENABLE_PUBLIC_API", False),
    )


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

        if current_app.config.get("ENABLE_HISTORY_RANKING", False):
            min_inter = current_app.config.get("HISTORY_MIN_INTERACTIONS", 5)
            news = rank_articles(current_user.id, news, min_interactions=min_inter)

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


@news_bp.route("/log_interaction", methods=["POST"])
@login_required
def log_interaction_route():
    try:
        data = request.json
        if not data or "url" not in data:
            return jsonify({"error": "Article data with url is required"}), 400

        interaction_type = data.get("interaction_type", "viewed")
        if interaction_type not in ("viewed", "saved", "clicked"):
            return jsonify({"error": "Invalid interaction_type"}), 400

        success = log_interaction(current_user.id, data, interaction_type)
        if success:
            return jsonify({"success": True})
        return jsonify({"error": "Failed to log interaction"}), 500

    except Exception as e:
        logger.error("Error logging interaction: %s", str(e), exc_info=True)
        return jsonify({"error": "Failed to log interaction"}), 500
