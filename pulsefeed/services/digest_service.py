import logging
from datetime import datetime, timedelta

from flask import current_app
from .. import db
from ..models import (
    User, UserPreference, NewsletterLog, TrendingTopic, ArticleInteraction,
)
from .email_service import send_digest_email

logger = logging.getLogger(__name__)


def _get_trending_articles():
    """Pull currently-flagged trending topics (Phase 5) and return their top articles."""
    if not current_app.config.get("ENABLE_TRENDING", False):
        return []

    trending = TrendingTopic.query.filter_by(is_flagged=True).all()
    articles = []
    for t in trending:
        # Use the most recent interactions matching this topic as a proxy
        recent = (
            ArticleInteraction.query
            .filter(ArticleInteraction.title.ilike(f"%{t.topic}%"))
            .order_by(ArticleInteraction.timestamp.desc())
            .limit(5)
            .all()
        )
        for r in recent:
            articles.append({
                "title": r.title,
                "description": r.description,
                "url": f"https://www.google.com/search?q={t.topic.replace(' ', '+')}",
                "source": "Trending",
                "publishedAt": r.timestamp.strftime("%Y-%m-%d") if r.timestamp else "",
            })
    return articles


def _get_ranked_articles_for_user(user_id, max_articles=10):
    """Pull recent high-similarity matches for a user (Phase 2's ranking)."""
    from .news_service import fetch_personalized_news
    from .ranking_service import rank_articles

    user = User.query.get(user_id)
    if not user or not user.preferences:
        return []

    try:
        articles = fetch_personalized_news(user.preferences)
        if not articles:
            return []
        ranked = rank_articles(user_id, articles, min_interactions=3)
        return ranked[:max_articles]
    except Exception as e:
        logger.error("Failed to get ranked articles for user %d: %s", user_id, e)
        return []


def _filter_already_sent(user_id, articles):
    """Remove articles already in NewsletterLog for this user."""
    sent_urls = set(
        r.article_url
        for r in NewsletterLog.query.filter_by(user_id=user_id).all()
    )
    return [a for a in articles if a.get("url") not in sent_urls]


def _build_html_digest(user, articles):
    """Build a simple HTML email template for the digest."""
    from flask import render_template

    try:
        return render_template(
            "email/digest.html",
            username=user.username,
            articles=articles,
        )
    except Exception:
        # Fallback inline HTML if template not found
        rows = ""
        for a in articles:
            title = a.get("title", "Untitled")
            url = a.get("url", "#")
            desc = a.get("description", "")
            source = a.get("source", "")
            rows += f"""
                <tr>
                    <td style="padding:16px 0;border-bottom:1px solid #eee;">
                        <a href="{url}" style="font-size:16px;font-weight:600;color:#1a56db;text-decoration:none;">{title}</a>
                        <p style="color:#666;font-size:14px;margin:4px 0;">{desc}</p>
                        <span style="color:#999;font-size:12px;">{source}</span>
                    </td>
                </tr>
            """
        return f"""
        <html><body style="font-family:Arial,sans-serif;max-width:600px;margin:0 auto;padding:20px;">
            <h2 style="color:#1a56db;">PulseFeed Digest</h2>
            <p>Hi {user.username},</p>
            <p>Here are your latest personalized news picks:</p>
            <table style="width:100%;border-collapse:collapse;">{rows}</table>
            <p style="color:#999;font-size:12px;margin-top:20px;">
                You're receiving this because you opted into PulseFeed digests.
                Visit your preferences to change frequency or opt out.
            </p>
        </body></html>
        """


def run_digest_job(app):
    """
    Scheduled job: send a digest email to each opted-in user.
    Pulls trending topics (Phase 5) and/or ranked articles (Phase 2),
    filters out already-sent articles, and sends an email.
    Logs every send attempt; a failed send doesn't crash the job or block other users.
    """
    with app.app_context():
        if not app.config.get("ENABLE_NEWSLETTER", False):
            logger.debug("Newsletter feature disabled — skipping digest job")
            return

        frequency = app.config.get("DIGEST_FREQUENCY", "daily")
        max_articles = app.config.get("DIGEST_MAX_ARTICLES", 10)

        opted_in_users = (
            User.query
            .join(UserPreference, UserPreference.user_id == User.id)
            .filter(UserPreference.newsletter_opt_in == True)
            .all()
        )
        logger.info("Digest job: %d opted-in users", len(opted_in_users))

        trending_articles = _get_trending_articles()

        for user in opted_in_users:
            try:
                # Skip if frequency doesn't match (weekly vs daily)
                if user.preferences.digest_frequency != frequency:
                    continue

                # Gather articles from ranking (Phase 2) + trending (Phase 5)
                ranked = _get_ranked_articles_for_user(user.id, max_articles)
                combined = ranked + trending_articles

                # Deduplicate by URL
                seen = set()
                deduped = []
                for a in combined:
                    url = a.get("url", "")
                    if url and url not in seen:
                        seen.add(url)
                        deduped.append(a)

                # Filter out already-sent articles
                new_articles = _filter_already_sent(user.id, deduped)

                if not new_articles:
                    logger.debug("No new articles for user %d — skipping", user.id)
                    continue

                # Limit to max
                new_articles = new_articles[:max_articles]

                # Build and send email
                html = _build_html_digest(user, new_articles)
                subject = f"PulseFeed Digest — {datetime.utcnow().strftime('%b %d, %Y')}"
                success, error = send_digest_email(user.username, subject, html)

                # Log every send attempt
                for article in new_articles:
                    log_entry = NewsletterLog(
                        user_id=user.id,
                        article_url=article.get("url", ""),
                        article_title=article.get("title", ""),
                        status="success" if success else "failed",
                        error_message=error if not success else None,
                    )
                    db.session.add(log_entry)

                db.session.commit()

            except Exception as e:
                db.session.rollback()
                logger.error(
                    "Digest job error for user %d: %s — continuing to next user",
                    user.id, e,
                )
                continue

        logger.info("Digest job complete")
