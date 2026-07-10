import logging
from flask import jsonify
from . import health_bp
from .. import db

logger = logging.getLogger(__name__)


@health_bp.route("/health")
def health():
    try:
        db.session.execute(db.text("SELECT 1"))
        return jsonify({"status": "ok", "database": "connected"}), 200
    except Exception as e:
        logger.error("Health check DB failure: %s", str(e))
        return jsonify({"status": "error", "database": "unreachable"}), 503
