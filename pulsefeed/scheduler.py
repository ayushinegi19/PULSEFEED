import logging
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger

logger = logging.getLogger(__name__)

_scheduler = None


def init_scheduler(app):
    """Start APScheduler in-process alongside the Flask app."""
    global _scheduler

    if not app.config.get("SCHEDULER_ENABLED", True):
        logger.info("Scheduler disabled by config")
        return

    if _scheduler is not None:
        return

    _scheduler = BackgroundScheduler(daemon=True)

    # Newsletter digest job
    if app.config.get("ENABLE_NEWSLETTER", False):
        from .services.digest_service import run_digest_job

        frequency = app.config.get("DIGEST_FREQUENCY", "daily")
        if frequency == "weekly":
            trigger = CronTrigger(day_of_week="mon", hour=8, minute=0)
        else:
            trigger = CronTrigger(hour=8, minute=0)

        _scheduler.add_job(
            func=run_digest_job,
            trigger=trigger,
            args=[app],
            id="digest_job",
            name="Newsletter digest job",
            replace_existing=True,
        )
        logger.info("Scheduled digest job (%s)", frequency)

    _scheduler.start()
    logger.info("APScheduler started")

    # Shut down scheduler when app context ends
    import atexit
    atexit.register(lambda: _scheduler.shutdown(wait=False) if _scheduler else None)


def get_scheduler():
    return _scheduler
