import json
import hashlib
import logging
from datetime import datetime, timedelta
import requests
from flask import current_app

from ..models import CachedArticle
from .. import db

logger = logging.getLogger(__name__)

<<<<<<< HEAD
# Map friendly source names to actual domains recognized by NewsData.io
SOURCE_DOMAIN_MAP = {
    "bbc-news": "bbc.com",
    "cnn": "edition.cnn.com",
    "techcrunch": "techcrunch.com",
    "business-insider": "businessinsider.com",
    "espn": "espn.com",
    "national-geographic": "nationalgeographic.com",
}

# Categories recognized by NewsData.io (not all news APIs share the same set)
VALID_CATEGORIES = {
    "business", "technology", "sports", "entertainment",
    "science", "health", "politics", "food", "travel", "world",
    "top", "environment",
}

=======
>>>>>>> 6f65201d4a2a05204f650ff3813aadaedb7a5197

def _cache_key(categories, sources, country):
    raw = f"{categories}|{sources}|{country}"
    return hashlib.md5(raw.encode()).hexdigest()


def _normalize_article(raw):
    """Map NewsData.io fields to the shape the frontend expects."""
    return {
        "title": raw.get("title", ""),
        "description": raw.get("description", "") or "",
        "url": raw.get("link", ""),
        "urlToImage": raw.get("image_url", "") or "",
        "publishedAt": raw.get("pubDate", "") or "",
        "source": (raw.get("source_id") or raw.get("source") or "").upper(),
    }


def _log_response_error(resp, context):
    """Log the actual response body from NewsData.io before raising."""
    try:
        body = resp.json()
        logger.error(
            "NewsData.io %s failed: %s — response body: %s",
            context, resp.status_code, json.dumps(body),
        )
    except (ValueError, json.JSONDecodeError):
        logger.error(
            "NewsData.io %s failed: %s — response text: %s",
            context, resp.status_code, resp.text[:500],
        )


def _safe_request(url, params, timeout, context):
    """Make a GET request, log the response body on error, return parsed JSON or raise."""
    resp = requests.get(url, params=params, timeout=timeout)

    if not resp.ok:
        _log_response_error(resp, context)
        resp.raise_for_status()

    data = resp.json()
    if data.get("status") == "error":
        logger.error(
            "NewsData.io %s returned error status: %s",
            context, json.dumps(data.get("results", data)),
        )
        return None

    return data


def _fetch_from_newsdata(categories_list, sources_list, country):
    """Call NewsData.io and return a list of normalized article dicts.

    Fallback chain:
      1. domainurl (if sources provided) — filter by domain
      2. category + country (if categories provided) — filter by category
      3. country only — broadest fallback
      4. language only — last resort
    """
    base = current_app.config["NEWSDATA_BASE_URL"]
    api_key = current_app.config["NEWSDATA_API_KEY"]
    timeout = current_app.config["NEWSDATA_TIMEOUT"]

    all_articles = []

    # Filter to valid categories only
    valid_cats = [c for c in categories_list if c in VALID_CATEGORIES]

    # --- Tier 1: domainurl ---
    if sources_list:
<<<<<<< HEAD
        domains = [SOURCE_DOMAIN_MAP.get(s.strip(), s.strip()) for s in sources_list]
        params = {
            "apikey": api_key,
            "language": "en",
            "domainurl": ",".join(domains),
=======
        params = {
            "apikey": api_key,
            "language": "en",
            "domain": ",".join(s.strip() for s in sources_list),
>>>>>>> 6f65201d4a2a05204f650ff3813aadaedb7a5197
        }
        logger.info("Fetching news via domainurl: %s", domains)
        try:
            data = _safe_request(f"{base}/news", params, timeout, "domainurl request")
            if data:
                articles = data.get("results", [])
                all_articles.extend(_normalize_article(a) for a in articles)
                logger.info("domainurl returned %d articles", len(all_articles))
        except requests.exceptions.HTTPError:
            pass  # Fall through to category tier

    # --- Tier 2: category + country ---
    if not all_articles and valid_cats:
        for category in valid_cats:
            params = {
                "apikey": api_key,
                "language": "en",
                "category": category.strip(),
                "country": country,
            }
            logger.info("Fetching news via category=%s, country=%s", category, country)
            try:
                data = _safe_request(f"{base}/news", params, timeout, "category request")
                if data:
                    articles = data.get("results", [])
                    all_articles.extend(_normalize_article(a) for a in articles)
                    logger.info("category=%s returned %d articles", category, len(articles))
            except requests.exceptions.HTTPError:
                continue  # Try next category

    # --- Tier 3: country only ---
    if not all_articles and country:
        params = {
            "apikey": api_key,
            "language": "en",
            "country": country,
        }
        logger.info("Fetching news via country=%s only", country)
        try:
            data = _safe_request(f"{base}/news", params, timeout, "country request")
            if data:
                articles = data.get("results", [])
                all_articles.extend(_normalize_article(a) for a in articles)
                logger.info("country=%s returned %d articles", country, len(all_articles))
        except requests.exceptions.HTTPError:
            pass

    # --- Tier 4: language only (last resort) ---
    if not all_articles:
        params = {
            "apikey": api_key,
            "language": "en",
        }
        logger.info("Fetching news via language=en only (last resort)")
        try:
            data = _safe_request(f"{base}/news", params, timeout, "language-only request")
            if data:
                articles = data.get("results", [])
                all_articles.extend(_normalize_article(a) for a in articles)
                logger.info("language-only returned %d articles", len(all_articles))
        except requests.exceptions.HTTPError:
            pass

    if not all_articles:
        logger.warning("All fetch tiers exhausted — no articles returned")

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
