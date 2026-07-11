import json
import re
import logging
from collections import Counter
from datetime import datetime, timedelta

import requests
from flask import current_app

from .. import db
from ..models import TrendingTopic

logger = logging.getLogger(__name__)

_WORD_RE = re.compile(r"[a-z]{3,}")
STOPWORDS = frozenset(
    """
    the and for that with from this that have will been more than they
    also said says according reports about into were was are not but
    its their his her our your his him them who whom whose which what
    when where while after before during between among across over
    could would should might must shall can may will just only very
    some any all none most many much such being been have has had
    did does done doing made make makes making said says saying
    new one two three first last next still even out off over
    """.split()
)


def _extract_keywords(text, top_n=5):
    if not text:
        return []
    words = [w for w in _WORD_RE.findall(text.lower()) if w not in STOPWORDS]
    return [w for w, _ in Counter(words).most_common(top_n)]


def _fetch_broad_news():
    """Fetch broad category coverage for spike detection (not per-user)."""
    base = current_app.config["NEWSDATA_BASE_URL"]
    api_key = current_app.config["NEWSDATA_API_KEY"]
    timeout = current_app.config["NEWSDATA_TIMEOUT"]

    categories = ["politics", "business", "technology", "sports", "world"]
    all_articles = []

    for category in categories:
        params = {
            "apikey": api_key,
            "language": "en",
            "category": category,
        }
        try:
            resp = requests.get(f"{base}/news", params=params, timeout=timeout)
            resp.raise_for_status()
            data = resp.json()
            for a in data.get("results", []):
                all_articles.append({
                    "title": a.get("title", ""),
                    "description": a.get("description", ""),
                    "url": a.get("link", ""),
                    "urlToImage": a.get("image_url", ""),
                    "publishedAt": a.get("pubDate", ""),
                    "source": (a.get("source_id") or "").upper(),
                    "category": category,
                })
        except requests.exceptions.RequestException as e:
            logger.error("Trending fetch failed for category %s: %s", category, e)
            continue

    return all_articles


def detect_spikes():
    """
    Fetch broad news, count article volume per topic/keyword cluster,
    compare to a rolling baseline, and flag topics exceeding the spike
    multiplier.

    Stores flagged topics in the TrendingTopic table. Returns the list
    of flagged topics.
    """
    window_hours = current_app.config["TRENDING_WINDOW_HOURS"]
    multiplier_threshold = current_app.config["TRENDING_SPIKE_MULTIPLIER"]

    articles = _fetch_broad_news()
    if not articles:
        logger.warning("No articles fetched for spike detection")
        return []

    # Count keyword frequency across current batch
    keyword_counts = Counter()
    keyword_articles = {}

    for article in articles:
        text = (article.get("title") or "") + " " + (article.get("description") or "")
        keywords = _extract_keywords(text, top_n=3)
        for kw in keywords:
            keyword_counts[kw] += 1
            if kw not in keyword_articles:
                keyword_articles[kw] = []
            keyword_articles[kw].append(article)

    # Get baseline: average count per keyword over past N days
    baseline_days = current_app.config["TRENDING_BASELINE_DAYS"]
    since = datetime.utcnow() - timedelta(days=baseline_days)

    existing = TrendingTopic.query.filter(
        TrendingTopic.detected_at >= since
    ).all()

    baseline_map = {}
    for t in existing:
        if t.keyword not in baseline_map:
            baseline_map[t.keyword] = []
        baseline_map[t.keyword].append(t.article_count)

    flagged = []
    for keyword, count in keyword_counts.most_common(20):
        baseline_counts = baseline_map.get(keyword, [])
        if baseline_counts:
            baseline_avg = sum(baseline_counts) / len(baseline_counts)
        else:
            baseline_avg = 0.0

        if baseline_avg > 0:
            spike_multiplier = count / baseline_avg
        else:
            spike_multiplier = float(count) if count > 0 else 0.0

        if count >= 3 and spike_multiplier >= multiplier_threshold:
            cluster_articles = keyword_articles[keyword]

            trending = TrendingTopic(
                topic=keyword,
                keyword=keyword,
                article_count=count,
                baseline_count=baseline_avg,
                multiplier=spike_multiplier,
                articles_json=json.dumps(cluster_articles[:10]),
                detected_at=datetime.utcnow(),
            )
            db.session.add(trending)
            flagged.append({
                "topic": keyword,
                "article_count": count,
                "baseline_count": baseline_avg,
                "multiplier": round(spike_multiplier, 2),
                "articles": cluster_articles[:10],
            })

            logger.info(
                "Trending spike detected: '%s' — %d articles (baseline: %.1f, multiplier: %.2f)",
                keyword, count, baseline_avg, spike_multiplier,
            )

    db.session.commit()
    logger.info("Spike detection complete: %d topics flagged", len(flagged))
    return flagged


def get_current_trending():
    """Return currently flagged trending topics from the DB."""
    window_hours = current_app.config.get("TRENDING_WINDOW_HOURS", 6)
    since = datetime.utcnow() - timedelta(hours=window_hours)

    topics = (
        TrendingTopic.query
        .filter(TrendingTopic.detected_at >= since)
        .order_by(TrendingTopic.multiplier.desc())
        .all()
    )

    result = []
    for t in topics:
        try:
            articles = json.loads(t.articles_json) if t.articles_json else []
        except (json.JSONDecodeError, TypeError):
            articles = []

        result.append({
            "topic": t.topic,
            "keyword": t.keyword,
            "article_count": t.article_count,
            "baseline_count": t.baseline_count,
            "multiplier": round(t.multiplier, 2),
            "detected_at": t.detected_at.isoformat(),
            "articles": articles,
        })

    return result
