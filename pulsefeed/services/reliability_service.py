"""
Source reliability tiers based on domain.

Reliability tiers:
  - high:     Established, well-known news organizations with strong
              editorial standards (e.g., BBC, Reuters, AP, NYT).
  - medium:   Recognized news sources with moderate editorial oversight.
  - low:      Sources with minimal editorial oversight or known bias.
  - unrated:  Default for any source not in the lookup table.

The initial seed list below is derived from publicly available media
reliability assessments. It is NOT our own judgment — it reflects
commonly referenced open-source media bias / reliability resources
such as:
  - Ad Fontes Media Bias Chart (https://www.adfontesmedia.com/)
  - AllSides Media Bias Ratings (https://www.allsides.com/unbiased-balanced-news)

Users should treat the "unrated" badge as "no assessment available,"
not as an implication of unreliability.
"""

RELIABILITY_TIERS = {
    "high": {"label": "High", "color": "#2e7d32"},
    "medium": {"label": "Medium", "color": "#f9a825"},
    "low": {"label": "Low", "color": "#c62828"},
    "unrated": {"label": "Unrated", "color": "#757575"},
}

# Domain -> tier mapping
DOMAIN_RELIABILITY = {
    # High reliability
    "bbc.com": "high",
    "bbc.co.uk": "high",
    "reuters.com": "high",
    "apnews.com": "high",
    "nytimes.com": "high",
    "washingtonpost.com": "high",
    "theguardian.com": "high",
    "npr.org": "high",
    "pbs.org": "high",
    "bloomberg.com": "high",
    "economist.com": "high",
    "wsj.com": "high",
    "ft.com": "high",
    "nature.com": "high",
    "scientificamerican.com": "high",
    "nationalgeographic.com": "high",

    # Medium reliability
    "cnn.com": "medium",
    "msnbc.com": "medium",
    "foxnews.com": "medium",
    "abcnews.go.com": "medium",
    "nbcnews.com": "medium",
    "cbsnews.com": "medium",
    "usatoday.com": "medium",
    "newsweek.com": "medium",
    "time.com": "medium",
    "forbes.com": "medium",
    "businessinsider.com": "medium",
    "techcrunch.com": "medium",
    "theverge.com": "medium",
    "arstechnica.com": "medium",
    "wired.com": "medium",
    "espn.com": "medium",

    # Low reliability
    "breitbart.com": "low",
    "infowars.com": "low",
    "dailymail.co.uk": "low",
    "thesun.co.uk": "low",
    "nypost.com": "low",
    "rt.com": "low",
    "sputniknews.com": "low",
}


def _extract_domain(url):
    """Extract the registered domain from a URL."""
    if not url:
        return ""
    try:
        from urllib.parse import urlparse
        netloc = urlparse(url).netloc.lower()
        # Strip 'www.' prefix
        if netloc.startswith("www."):
            netloc = netloc[4:]
        return netloc
    except Exception:
        return ""


def get_reliability(article):
    """
    Look up the reliability tier for an article based on its URL domain.

    Returns a dict: {"tier": "high", "label": "High", "color": "#2e7d32"}
    Falls back to "unrated" for any source not in the lookup table.
    """
    url = article.get("url", "")
    domain = _extract_domain(url)

    tier = DOMAIN_RELIABILITY.get(domain, "unrated")
    tier_info = RELIABILITY_TIERS[tier]

    return {
        "tier": tier,
        "label": tier_info["label"],
        "color": tier_info["color"],
        "domain": domain,
    }


def annotate_articles(articles):
    """Add a 'reliability' key to each article in the list."""
    for article in articles:
        article["reliability"] = get_reliability(article)
    return articles
