import re
import logging
from collections import defaultdict

logger = logging.getLogger(__name__)

_WORD_RE = re.compile(r"[a-z]{2,}")


def _normalize_title(title):
    """Lowercase, tokenize, remove short words for comparison."""
    if not title:
        return []
    return [w for w in _WORD_RE.findall(title.lower()) if len(w) > 2]


def _token_overlap(title_a, title_b):
    """Jaccard similarity of normalized title token sets."""
    set_a = set(_normalize_title(title_a))
    set_b = set(_normalize_title(title_b))
    if not set_a or not set_b:
        return 0.0
    intersection = set_a & set_b
    union = set_a | set_b
    return len(intersection) / len(union)


def cluster_articles(articles, threshold=0.5):
    """
    Group articles with similar titles into clusters.

    Returns a list of cluster dicts:
      {
        "representative": <article dict>,
        "also_covered_by": ["SOURCE_A", "SOURCE_B", ...],
        "cluster_size": 3
      }

    Articles below the similarity threshold remain as single-article clusters.
    """
    if not articles:
        return []

    # Union-find for clustering
    parent = list(range(len(articles)))

    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    def union(x, y):
        rx, ry = find(x), find(y)
        if rx != ry:
            parent[rx] = ry

    # Compare all pairs
    for i in range(len(articles)):
        for j in range(i + 1, len(articles)):
            sim = _token_overlap(
                articles[i].get("title", ""),
                articles[j].get("title", ""),
            )
            if sim >= threshold:
                union(i, j)

    # Group indices by cluster root
    clusters = defaultdict(list)
    for idx in range(len(articles)):
        clusters[find(idx)].append(idx)

    result = []
    for indices in clusters.values():
        cluster_articles_list = [articles[i] for i in indices]

        # Pick representative: earliest published, or most complete description
        def sort_key(a):
            pub = a.get("publishedAt") or ""
            desc_len = len(a.get("description") or "")
            return (pub, desc_len)

        sorted_cluster = sorted(cluster_articles_list, key=sort_key)
        representative = sorted_cluster[0]

        # Collect other sources
        also_covered = []
        seen_sources = {representative.get("source", "")}
        for a in sorted_cluster[1:]:
            src = a.get("source", "")
            if src and src not in seen_sources:
                also_covered.append(src)
                seen_sources.add(src)

        cluster = {
            "representative": representative,
            "also_covered_by": also_covered,
            "cluster_size": len(cluster_articles_list),
        }

        if len(cluster_articles_list) > 1:
            logger.info(
                "Cluster of %d articles: '%s' — also covered by %s",
                len(cluster_articles_list),
                representative.get("title", "")[:60],
                also_covered,
            )

        result.append(cluster)

    logger.info(
        "Clustered %d articles into %d clusters (threshold=%.2f)",
        len(articles), len(result), threshold,
    )
    return result
