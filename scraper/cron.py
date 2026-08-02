"""
Callable entrypoints for django-crontab.

Cron schedule (America/New_York) is defined in settings.CRONJOBS.
"""

from __future__ import annotations

import logging
from datetime import timedelta

from django.utils import timezone

from .services import ScrapeService, ensure_tracks

logger = logging.getLogger("scraper")


def scrape_entries_job() -> None:
    service = ScrapeService()
    today = timezone.localdate()
    for day in (today, today + timedelta(days=1)):
        job = service.scrape_entries(race_date=day)
        logger.info(
            "entries job %s date=%s races=%s status=%s",
            job.id,
            day,
            job.races_upserted,
            job.status,
        )


def scrape_results_job() -> None:
    service = ScrapeService()
    job = service.scrape_results(race_date=timezone.localdate())
    logger.info(
        "results job %s races=%s status=%s",
        job.id,
        job.races_upserted,
        job.status,
    )


def scrape_live_job() -> None:
    service = ScrapeService()
    jobs = service.scrape_live()
    for job in jobs:
        logger.info(
            "live job %s date=%s races=%s status=%s",
            job.id,
            job.target_date,
            job.races_upserted,
            job.status,
        )


def scrape_near_post_job() -> None:
    service = ScrapeService()
    job = service.scrape_near_post()
    logger.info(
        "near-post job %s races=%s status=%s",
        job.id,
        job.races_upserted,
        job.status,
    )


def sync_tracks_job() -> None:
    count = ensure_tracks()
    logger.info("track sync complete, new tracks=%s", count)
