"""Fan-out event bus: signed webhooks + Telegram VIP channel."""

from __future__ import annotations

import hashlib
import hmac
import json
import logging
from datetime import timedelta
from typing import Any

import requests
from django.conf import settings
from django.utils import timezone

from .models import WebhookDelivery, WebhookEndpoint
from .telegram import TelegramClient, format_event_message

logger = logging.getLogger("integrations")


def sign_payload(secret: str, body: bytes) -> str:
    """HMAC-SHA256 hex digest for X-Signature header."""
    return hmac.new(secret.encode("utf-8"), body, hashlib.sha256).hexdigest()


def emit(event_type: str, payload: dict[str, Any]) -> dict[str, Any]:
    """
    Dispatch an outbound event to subscribed webhooks and Telegram.

    Returns a small summary for logging/tests.
    """
    envelope = {
        "event": event_type,
        "occurred_at": timezone.now().isoformat(),
        "data": payload,
    }
    body = json.dumps(envelope, default=str, separators=(",", ":")).encode("utf-8")

    webhook_results = _deliver_webhooks(event_type, envelope, body)
    telegram_ok = False
    if getattr(settings, "TELEGRAM_ENABLED", False):
        telegram_ok = TelegramClient().send_message(
            format_event_message(event_type, payload)
        )

    summary = {
        "event": event_type,
        "webhooks": webhook_results,
        "telegram": telegram_ok,
    }
    logger.info("emit %s webhooks=%s telegram=%s", event_type, webhook_results, telegram_ok)
    return summary


def _deliver_webhooks(
    event_type: str, envelope: dict, body: bytes
) -> list[dict[str, Any]]:
    results: list[dict[str, Any]] = []
    endpoints = WebhookEndpoint.objects.filter(is_active=True)
    timeout = getattr(settings, "WEBHOOK_TIMEOUT_SECONDS", 10)
    max_attempts = getattr(settings, "WEBHOOK_MAX_ATTEMPTS", 3)

    for endpoint in endpoints:
        if not endpoint.subscribes_to(event_type):
            continue
        delivery = WebhookDelivery.objects.create(
            endpoint=endpoint,
            event_type=event_type,
            payload=envelope,
            status=WebhookDelivery.Status.PENDING,
        )
        signature = sign_payload(endpoint.secret, body)
        headers = {
            "Content-Type": "application/json",
            "X-Signature": signature,
            "X-Event-Type": event_type,
            "User-Agent": "AHRVIPPicker-Webhooks/1.0",
        }
        try:
            response = requests.post(
                endpoint.url, data=body, headers=headers, timeout=timeout
            )
            delivery.attempts = 1
            delivery.status_code = response.status_code
            delivery.response_body = (response.text or "")[:2000]
            if 200 <= response.status_code < 300:
                delivery.status = WebhookDelivery.Status.SUCCESS
                delivery.delivered_at = timezone.now()
            else:
                delivery.status = WebhookDelivery.Status.FAILED
                delivery.error_message = f"HTTP {response.status_code}"
                if delivery.attempts < max_attempts:
                    delivery.next_retry_at = timezone.now() + timedelta(minutes=5)
            delivery.save()
            results.append(
                {
                    "endpoint_id": endpoint.id,
                    "status": delivery.status,
                    "status_code": delivery.status_code,
                }
            )
        except requests.RequestException as exc:
            delivery.attempts = 1
            delivery.status = WebhookDelivery.Status.FAILED
            delivery.error_message = str(exc)[:500]
            delivery.next_retry_at = timezone.now() + timedelta(minutes=5)
            delivery.save()
            results.append(
                {
                    "endpoint_id": endpoint.id,
                    "status": delivery.status,
                    "error": str(exc),
                }
            )
    return results
