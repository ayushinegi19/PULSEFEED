import json
import hashlib
import logging
from datetime import datetime, timedelta
import requests
from flask import current_app

from ..models import CachedArticle
from .. import db

logger = logging.getLogger(__name__)


def _cache_key(categories, sources, country):
    raw = f"{categories}|{sources}|{country}"
    return hashlib.md5(raw.encode()).hexdigest()


def _normalize_article(raw):
    """Map NewsData.io fields to the shape the frontend expects."""
    return {
        "title": raw.get("title", ""),
        "description": raw.get("description", ""),
        "url": raw.get("link", ""),
        "urlToImage": raw.get("image_url", ""),
        "publishedAt": raw.get("pubDate", ""),
        "source": (raw.get("source_id") or raw.get("source") or "").upper(),
    }


def _fetch_from_newsdata(categories_list, sources_list, country):
    """Call NewsData.io and return a list of normalized article dicts."""
    base = current_app.config["NEWSDATA_BASE_URL"]
    api_key = current_app.config["NEWSDATA_API_KEY"]
    timeout = current_app.config["NEWSDATA_TIMEOUT"]

    all_articles = []

    if sources_list:
        params = {
            "apikey": api_key,
            "language": "en",
            "domain": ",".join(s.strip() for s in sources_list),
        }
        resp = requests.get(f"{base}/news", params=params, timeout=timeout)
        resp.raise_for_status()
        data = resp.json()
        articles = data.get("results", [])

        if categories_list:
            for a in articles:
                title = (a.get("title") or "").lower()
                desc = (a.get("description") or "").lower()
                if any(c.lower() in title or c.lower() in desc for c in categories_list):
                    all_articles.append(_normalize_article(a))
        else:
            all_articles.extend(_normalize_article(a) for a in articles)

    elif categories_list:
        for category in categories_list:
            params = {
                "apikey": api_key,
                "language": "en",
                "category": category.strip(),
                "country": country,
            }
            resp = requests.get(f"{base}/news", params=params, timeout=timeout)
            resp.raise_for_status()
            data = resp.json()
            articles = data.get("results", [])
            all_articles.extend(_normalize_article(a) for a in articles)

    return all_articles


def fetch_personalized_news(preferences):
    """Return articles for a user, using a DB cache with TTL."""
    categories = (
        preferences.categories.split(",") if preferences.categories else []
    )
    sources = preferences.sources.split(",") if preferences.sources else []
    country = preferences.countries if preferences.countries else "us"

    categories = [c.strip() for c in categories if c.strip()]
    sources = [s.strip() for s in sources if s.strip()]

    key = _cache_key(
        preferences.categories or "",
        preferences.sources or "",
        country,
    )
    ttl = current_app.config["NEWS_CACHE_TTL"]

    cached = CachedArticle.query.filter_by(cache_key=key).first()
    if cached and datetime.utcnow() - cached.fetched_at < timedelta(seconds=ttl):
        try:
            return json.loads(cached.articles_json)
        except (json.JSONDecodeError, TypeError):
            pass  # stale/corrupt cache, re-fetch

    try:
        articles = _fetch_from_newsdata(categories, sources, country)
    except requests.exceptions.Timeout:
        logger.error("NewsData.io request timed out")
        if cached:
            try:
                return json.loads(cached.articles_json)
            except (json.JSONDecodeError, TypeError):
                pass
        raise
    except requests.exceptions.RequestException as e:
        logger.error("NewsData.io request failed: %s", e)
        if cached:
            try:
                return json.loads(cached.articles_json)
            except (json.JSONDecodeError, TypeError):
                pass
        raise

    if cached:
        cached.articles_json = json.dumps(articles)
        cached.fetched_at = datetime.utcnow()
    else:
        cached = CachedArticle(
            cache_key=key,
            articles_json=json.dumps(articles),
            fetched_at=datetime.utcnow(),
        )
        db.session.add(cached)
    db.session.commit()

    return articles
