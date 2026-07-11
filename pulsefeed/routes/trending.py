import logging
from flask import jsonify, current_app
from flask_login import login_required

from ..services.trending_service import get_current_trending, detect_spikes
from . import trending_bp

logger = logging.getLogger(__name__)


@trending_bp.route("/trending")
@login_required
def trending():
    if not current_app.config.get("ENABLE_TRENDING", False):
        return jsonify({"error": "Trending feature is disabled"}), 503

    try:
        topics = get_current_trending()
        return jsonify(topics)
    except Exception as e:
        logger.error("Error fetching trending topics: %s", str(e), exc_info=True)
        return jsonify({"error": "Failed to fetch trending topics"}), 500


@trending_bp.route("/trending/refresh", methods=["POST"])
@login_required
def refresh_trending():
    if not current_app.config.get("ENABLE_TRENDING", False):
        return jsonify({"error": "Trending feature is disabled"}), 503

    try:
        flagged = detect_spikes()
        return jsonify({"success": True, "flagged_count": len(flagged), "topics": flagged})
    except Exception as e:
        logger.error("Error refreshing trending topics: %s", str(e), exc_info=True)
        return jsonify({"error": "Failed to refresh trending topics"}), 500
