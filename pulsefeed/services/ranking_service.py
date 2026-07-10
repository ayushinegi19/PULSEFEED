import hashlib
import math
import re
import logging
from collections import Counter
from datetime import datetime, timedelta

from .. import db
from ..models import ArticleInteraction

logger = logging.getLogger(__name__)

STOPWORDS = frozenset(
    """
    a an the and or but in on at to for of is are was were be been being have
    has had do does did will would could should may might must shall can need
    this that these those i you he she it we they them his her its their our
    your my me him us as from by with about into through during before after
    above below up down out off over under again further then once here there
    all any both each few more most other some such no nor not only own same
    so than too very s t can just don should now
    """.split()
)

_WORD_RE = re.compile(r"[a-z]{2,}")


def _tokenize(text):
    if not text:
        return []
    return [
        w for w in _WORD_RE.findall(text.lower())
        if w not in STOPWORDS and len(w) > 2
    ]


def url_hash(url):
    return hashlib.sha256(url.encode()).hexdigest()


def log_interaction(user_id, article, interaction_type):
    try:
        url = article.get("url", "")
        if not url:
            return False

        interaction = ArticleInteraction(
            user_id=user_id,
            url_hash=url_hash(url),
            interaction_type=interaction_type,
            title=article.get("title", ""),
            description=article.get("description", ""),
        )
        db.session.add(interaction)
        db.session.commit()
        return True
    except Exception as e:
        db.session.rollback()
        logger.error("Failed to log interaction: %s", e)
        return False


def get_interaction_count(user_id):
    return ArticleInteraction.query.filter_by(user_id=user_id).count()


def _compute_tfidf(tokens, idf_map):
    counts = Counter(tokens)
    total = sum(counts.values())
    if total == 0:
        return {}
    vec = {}
    for term, count in counts.items():
        tf = count / total
        idf = idf_map.get(term, 0.0)
        vec[term] = tf * idf
    return vec


def _build_idf_map(docs_tokens):
    num_docs = len(docs_tokens)
    if num_docs == 0:
        return {}
    df = Counter()
    for tokens in docs_tokens:
        for term in set(tokens):
            df[term] += 1
    return {term: math.log((num_docs + 1) / (count + 1)) + 1 for term, count in df.items()}


def _cosine_similarity(vec_a, vec_b):
    if not vec_a or not vec_b:
        return 0.0
    dot = sum(vec_a.get(t, 0.0) * v for t, v in vec_b.items())
    mag_a = math.sqrt(sum(v * v for v in vec_a.values()))
    mag_b = math.sqrt(sum(v * v for v in vec_b.values()))
    if mag_a == 0 or mag_b == 0:
        return 0.0
    return dot / (mag_a * mag_b)


def rank_articles(user_id, articles, min_interactions=5):
    """
    Re-rank articles by TF-IDF cosine similarity to the user's recent
    interaction history. Returns articles sorted by relevance score (desc).

    If the user has fewer than min_interactions, returns articles unchanged
    (cold-start fallback).
    """
    if not articles:
        return articles

    count = get_interaction_count(user_id)
    if count < min_interactions:
        logger.debug(
            "User %d has %d interactions (< %d), skipping ranking",
            user_id, count, min_interactions,
        )
        return articles

    # Fetch recent interactions (last 50)
    interactions = (
        ArticleInteraction.query
        .filter_by(user_id=user_id)
        .order_by(ArticleInteraction.timestamp.desc())
        .limit(50)
        .all()
    )

    # Build corpus: interaction docs + candidate article docs
    interaction_tokens = [
        _tokenize((i.title or "") + " " + (i.description or ""))
        for i in interactions
    ]
    article_tokens = [
        _tokenize((a.get("title") or "") + " " + (a.get("description") or ""))
        for a in articles
    ]

    all_docs = interaction_tokens + article_tokens
    idf_map = _build_idf_map(all_docs)

    # Build user profile vector: average of interaction TF-IDF vectors
    interaction_vecs = [
        _compute_tfidf(tokens, idf_map) for tokens in interaction_tokens
    ]
    if not interaction_vecs:
        return articles

    user_profile = {}
    for vec in interaction_vecs:
        for term, weight in vec.items():
            user_profile[term] = user_profile.get(term, 0.0) + weight
    num_interactions = len(interaction_vecs)
    user_profile = {t: w / num_interactions for t, w in user_profile.items()}

    # Score each article by cosine similarity to user profile
    scored = []
    for idx, article in enumerate(articles):
        article_vec = _compute_tfidf(article_tokens[idx], idf_map)
        score = _cosine_similarity(user_profile, article_vec)
        scored.append((score, article))

    scored.sort(key=lambda x: x[0], reverse=True)
    return [article for _, article in scored]
