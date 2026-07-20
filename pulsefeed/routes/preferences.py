from flask import render_template, request, redirect, url_for, flash, current_app
from flask_login import login_required, current_user

from .. import db
from ..models import UserPreference
from . import prefs_bp


@prefs_bp.route("/set_preferences", methods=["GET", "POST"])
@login_required
def set_preferences():
    if request.method == "POST":
        categories = request.form.getlist("categories")
        sources = request.form.getlist("sources")
        country = request.form.get("country")

        categories_str = ",".join(categories) if categories else ""
        sources_str = ",".join(sources) if sources else ""

        # Phase 6: newsletter opt-in
        newsletter_opt_in = request.form.get("newsletter_opt_in") == "on"
        digest_frequency = request.form.get("digest_frequency", "daily")

        existing_pref = UserPreference.query.filter_by(
            user_id=current_user.id
        ).first()
        if existing_pref:
            db.session.delete(existing_pref)
            db.session.commit()

        new_pref = UserPreference(
            user_id=current_user.id,
            categories=categories_str,
            sources=sources_str,
            countries=country,
            newsletter_opt_in=newsletter_opt_in,
            digest_frequency=digest_frequency,
        )
        db.session.add(new_pref)
        db.session.commit()

        flash("Preferences updated successfully!", "success")
        return redirect(url_for("news.index"))

    return render_template(
        "preferences.html",
        enable_newsletter=current_app.config.get("ENABLE_NEWSLETTER", False),
        enable_public_api=current_app.config.get("ENABLE_PUBLIC_API", False),
    )
