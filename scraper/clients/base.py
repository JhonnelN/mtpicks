"""Shared HTTP utilities for racing data clients."""

from __future__ import annotations

import logging
import time
from typing import Any

import requests
from django.conf import settings

logger = logging.getLogger("scraper")


class HttpClient:
    """Thin requests wrapper with polite delays and browser-like headers."""

    def __init__(self) -> None:
        self.session = requests.Session()
        self.session.headers.update(
            {
                "User-Agent": settings.SCRAPER_USER_AGENT,
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                "Accept-Language": "en-US,en;q=0.9",
                "Cache-Control": "no-cache",
            }
        )
        self.delay = settings.SCRAPER_REQUEST_DELAY_SECONDS
        self.timeout = settings.SCRAPER_TIMEOUT_SECONDS
        self._last_request_at = 0.0

    def _throttle(self) -> None:
        elapsed = time.monotonic() - self._last_request_at
        if elapsed < self.delay:
            time.sleep(self.delay - elapsed)

    def get(
        self,
        url: str,
        *,
        params: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
        auth: Any = None,
    ) -> requests.Response:
        self._throttle()
        logger.info("GET %s params=%s", url, params)
        response = self.session.get(
            url,
            params=params,
            headers=headers,
            auth=auth,
            timeout=self.timeout,
        )
        self._last_request_at = time.monotonic()
        return response
