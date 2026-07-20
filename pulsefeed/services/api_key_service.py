import os
import secrets
import hashlib
import logging
from datetime import datetime

from .. import db
from ..models import ApiKey, ApiKeyUsage

logger = logging.getLogger(__name__)

# Rate limit tiers mapped to Flask-Limiter limit strings
TIER_LIMITS = {
    "free": "100 per day",
    "pro": "1000 per day",
    "enterprise": "10000 per day",
}


def _hash_key(plaintext_key):
    """Hash an API key with SHA-256 for secure storage."""
    return hashlib.sha256(plaintext_key.encode()).hexdigest()


def generate_api_key(user_id, name="Default", tier="free"):
    """
    Generate a new API key for a user.
    Returns the plaintext key (shown exactly once) and the stored ApiKey object.
    """
    raw_key = secrets.token_urlsafe(32)
    prefix = "pf_"
    plaintext = prefix + raw_key
    key_hash = _hash_key(plaintext)

    api_key = ApiKey(
        user_id=user_id,
        key_hash=key_hash,
        name=name,
        rate_limit_tier=tier,
        is_active=True,
    )
    db.session.add(api_key)
    db.session.commit()

    return plaintext, api_key


def validate_api_key(plaintext_key):
    """
    Validate an API key from the request header.
    Returns the ApiKey object if valid and active, None otherwise.
    """
    if not plaintext_key:
        return None

    key_hash = _hash_key(plaintext_key)
    api_key = ApiKey.query.filter_by(key_hash=key_hash, is_active=True).first()
    return api_key


def log_usage(api_key_id, endpoint, method):
    """Log an API key usage event."""
    try:
        usage = ApiKeyUsage(
            api_key_id=api_key_id,
            endpoint=endpoint,
            method=method,
        )
        db.session.add(usage)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        logger.error("Failed to log API usage: %s", e)


def revoke_api_key(api_key_id, user_id):
    """Deactivate an API key (soft delete)."""
    api_key = ApiKey.query.filter_by(id=api_key_id, user_id=user_id).first()
    if not api_key:
        return False
    api_key.is_active = False
    db.session.commit()
    return True


def get_user_keys(user_id):
    """Return all API keys for a user (without the hash)."""
    return ApiKey.query.filter_by(user_id=user_id).all()


def get_tier_limit(tier):
    """Return the Flask-Limiter limit string for a tier, from config."""
    from flask import current_app
    config_key = f"API_RATE_LIMIT_{tier.upper()}"
    return current_app.config.get(config_key, TIER_LIMITS.get(tier, TIER_LIMITS["free"]))
