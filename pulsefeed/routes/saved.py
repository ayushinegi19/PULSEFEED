import logging
from flask import render_template, jsonify, request, current_app
from flask_login import login_required, current_user
from sqlalchemy import or_

from .. import db
from ..models import SavedArticle
from . import saved_bp

logger = logging.getLogger(__name__)


@saved_bp.route("/saved")
@login_required
def saved():
    return render_template(
        "saved.html",
        enable_public_api=current_app.config.get("ENABLE_PUBLIC_API", False),
    )


@saved_bp.route("/save_article", methods=["POST"])
@login_required
def save_article():
    try:
        data = request.json

        required_fields = [
            "title", "description", "url", "urlToImage", "publishedAt", "source"
        ]
        if not all(field in data and data[field] for field in required_fields):
            missing = [
                field for field in required_fields
                if field not in data or not data[field]
            ]
            return jsonify(
                {"success": False, "message": f'Missing fields: {", ".join(missing)}'}
            ), 400

        existing = SavedArticle.query.filter_by(
            user_id=current_user.id, url=data.get("url")
        ).first()
        if existing:
            return jsonify(
                {"success": False, "message": "Article already saved"}
            ), 400

        article = SavedArticle(
            user_id=current_user.id,
            title=data.get("title"),
            description=data.get("description"),
            url=data.get("url"),
            urlToImage=data.get("urlToImage"),
            publishedAt=data.get("publishedAt"),
            source=data.get("source"),
        )

        db.session.add(article)
        db.session.commit()

        return jsonify({"success": True, "message": "Article saved successfully"})

    except Exception as e:
        db.session.rollback()
        logger.error("Error saving article: %s", str(e), exc_info=True)
        return jsonify({"success": False, "message": "Failed to save article"}), 500


@saved_bp.route("/get_saved_articles")
@login_required
def get_saved_articles():
    try:
        articles = (
            SavedArticle.query.filter_by(user_id=current_user.id)
            .order_by(SavedArticle.saved_at.desc())
            .all()
        )

        result = []
        for article in articles:
            result.append({
                "id": article.id,
                "title": article.title,
                "description": article.description,
                "url": article.url,
                "urlToImage": article.urlToImage,
                "publishedAt": article.publishedAt,
                "source": article.source,
                "saved_at": article.saved_at.strftime("%Y-%m-%d %H:%M:%S"),
            })

        return jsonify(result)

    except Exception as e:
        logger.error("Error fetching saved articles: %s", str(e), exc_info=True)
        return jsonify({"error": "Failed to retrieve saved articles"}), 500


@saved_bp.route("/delete_saved_article/<int:article_id>", methods=["DELETE"])
@login_required
def delete_saved_article(article_id):
    try:
        article = SavedArticle.query.filter_by(
            id=article_id, user_id=current_user.id
        ).first()

        if not article:
            return jsonify({"success": False, "message": "Article not found"}), 404

        db.session.delete(article)
        db.session.commit()

        return jsonify({"success": True, "message": "Article removed from saved"})

    except Exception as e:
        db.session.rollback()
        logger.error("Error deleting saved article: %s", str(e), exc_info=True)
        return jsonify({"success": False, "message": "Failed to delete article"}), 500


@saved_bp.route("/search_saved_articles")
@login_required
def search_saved_articles():
    try:
        query = request.args.get("query", "")
        if not query:
            return jsonify({"error": "Search query is required"}), 400

        search_filter = or_(
            SavedArticle.title.ilike(f"%{query}%"),
            SavedArticle.description.ilike(f"%{query}%"),
            SavedArticle.source.ilike(f"%{query}%"),
        )

        articles = (
            SavedArticle.query.filter(
                SavedArticle.user_id == current_user.id,
                search_filter,
            )
            .order_by(SavedArticle.saved_at.desc())
            .all()
        )

        result = []
        for article in articles:
            result.append({
                "id": article.id,
                "title": article.title,
                "description": article.description,
                "url": article.url,
                "urlToImage": article.urlToImage,
                "publishedAt": article.publishedAt,
                "source": article.source,
                "saved_at": article.saved_at.strftime("%Y-%m-%d %H:%M:%S"),
            })

        return jsonify(result)

    except Exception as e:
        logger.error("Error searching saved articles: %s", str(e), exc_info=True)
        return jsonify({"error": "Failed to search saved articles"}), 500
