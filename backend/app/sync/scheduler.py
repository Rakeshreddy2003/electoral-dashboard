import logging
from datetime import datetime

from apscheduler.schedulers.background import BackgroundScheduler

from app.config import settings
from app.sync.odk_sync import sync_once

logger = logging.getLogger(__name__)
_scheduler: BackgroundScheduler | None = None


def _run_safely() -> None:
    try:
        sync_once()
    except Exception:
        logger.exception("Scheduled ODK sync run failed; will retry next interval")


def start_scheduler() -> BackgroundScheduler:
    global _scheduler
    if _scheduler is not None:
        return _scheduler
    _scheduler = BackgroundScheduler()
    # next_run_time=now, not None -- None (APScheduler's "wait a full
    # interval before the first run" behavior) meant every container
    # restart silently pushed the first sync ODK_SYNC_INTERVAL_MINUTES into
    # the future. A deploy, crash, or routine restart is not rare in a
    # Dockerized service, and each one reset this clock, so the dashboard
    # could sit stale for arbitrarily long (confirmed: 318 vs 699 real
    # submissions after a run of restarts this session). Sync picks up
    # incrementally from sync_state's watermark, so running it right away
    # on every startup is cheap when little has changed.
    _scheduler.add_job(
        _run_safely, "interval", minutes=settings.odk_sync_interval_minutes, id="odk_sync", next_run_time=datetime.now()
    )
    _scheduler.start()
    logger.info("ODK sync scheduler started: every %s minutes, first run immediately", settings.odk_sync_interval_minutes)
    return _scheduler
