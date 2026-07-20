import logging
from flask import (
    render_template, request, redirect, url_for, flash, jsonify,
    current_app,
)
from flask_login import login_required, current_user

from .. import db
from ..models import ApiKey
from ..services.api_key_service import generate_api_key, revoke_api_key, get_user_keys
from . import api_keys_bp

logger = logging.getLogger(__name__)


@api_keys_bp.route("/api_keys")
@login_required
def manage_keys():
    if not current_app.config.get("ENABLE_PUBLIC_API", False):
        flash("Public API feature is not enabled.", "error")
        return redirect(url_for("news.index"))

    keys = get_user_keys(current_user.id)
    return render_template("api_keys.html", keys=keys)


@api_keys_bp.route("/api_keys/generate", methods=["POST"])
@login_required
def generate_key():
    if not current_app.config.get("ENABLE_PUBLIC_API", False):
        return jsonify({"error": "Public API feature is not enabled"}), 403

    name = request.form.get("key_name", "Default")
    tier = request.form.get("tier", "free")

    try:
        plaintext, api_key = generate_api_key(current_user.id, name=name, tier=tier)
        flash("API key created. Copy it now — you won't see it again.", "success")
        return render_template(
            "api_keys.html",
            keys=get_user_keys(current_user.id),
            new_key=plaintext,
            new_key_id=api_key.id,
        )
    except Exception as e:
        logger.error("Failed to generate API key: %s", e)
        flash("Failed to generate API key.", "error")
        return redirect(url_for("api_keys.manage_keys"))


@api_keys_bp.route("/api_keys/<int:key_id>/revoke", methods=["POST"])
@login_required
def revoke_key(key_id):
    if not current_app.config.get("ENABLE_PUBLIC_API", False):
        return jsonify({"error": "Public API feature is not enabled"}), 403

    success = revoke_api_key(key_id, current_user.id)
    if success:
        flash("API key revoked.", "success")
    else:
        flash("API key not found.", "error")
    return redirect(url_for("api_keys.manage_keys"))
