import logging
from flask import current_app
from flask_mail import Mail, Message

logger = logging.getLogger(__name__)

mail = Mail()


def init_mail(app):
    """Initialize Flask-Mail. Called from app factory only when newsletter is enabled."""
    mail.init_app(app)


def send_digest_email(recipient, subject, html_body):
    """
    Send a digest email and return (True, None) on success or (False, error_msg) on failure.
    Never raises — callers can safely loop over multiple users.
    """
    try:
        msg = Message(
            subject=subject,
            recipients=[recipient],
            html=html_body,
            sender=current_app.config["MAIL_DEFAULT_SENDER"],
        )
        mail.send(msg)
        logger.info("Digest email sent to %s", recipient)
        return True, None
    except Exception as e:
        logger.error("Failed to send digest to %s: %s", recipient, e)
        return False, str(e)
