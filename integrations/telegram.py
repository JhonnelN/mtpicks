"""Telegram Bot API client for VIP channel/group alerts."""

from __future__ import annotations

import logging

import requests
from django.conf import settings

logger = logging.getLogger("integrations")


class TelegramClient:
    """Send messages to the configured VIP chat (channel or group)."""

    def __init__(self) -> None:
        self.token = getattr(settings, "TELEGRAM_BOT_TOKEN", "") or ""
        self.chat_id = getattr(settings, "TELEGRAM_VIP_CHAT_ID", "") or ""
        self.enabled = bool(getattr(settings, "TELEGRAM_ENABLED", False))

    @property
    def configured(self) -> bool:
        return bool(self.enabled and self.token and self.chat_id)

    def send_message(self, text: str, *, parse_mode: str = "HTML") -> bool:
        if not self.configured:
            logger.debug("Telegram disabled or not configured; skip send")
            return False
        url = f"https://api.telegram.org/bot{self.token}/sendMessage"
        try:
            response = requests.post(
                url,
                json={
                    "chat_id": self.chat_id,
                    "text": text,
                    "parse_mode": parse_mode,
                    "disable_web_page_preview": False,
                },
                timeout=15,
            )
            if response.status_code >= 400:
                logger.warning(
                    "Telegram send failed %s: %s",
                    response.status_code,
                    response.text[:300],
                )
                return False
            return True
        except requests.RequestException as exc:
            logger.warning("Telegram request error: %s", exc)
            return False


def format_event_message(event_type: str, payload: dict) -> str:
    """Build a short HTML message for the VIP channel."""
    track = payload.get("track_code", "?")
    race_number = payload.get("race_number", "?")
    race_date = payload.get("race_date", "")

    if event_type == "picks.morning_published":
        sels = " · ".join(str(s) for s in payload.get("selections", []))
        return (
            f"<b>Our Picks — Mañana</b>\n"
            f"{track} R{race_number} ({race_date})\n"
            f"Selecciones: <code>{sels}</code>"
        )
    if event_type == "picks.mtp5_published":
        sels = " · ".join(str(s) for s in payload.get("selections", []))
        return (
            f"<b>5 MTP Update</b>\n"
            f"{track} R{race_number}\n"
            f"Selecciones: <code>{sels}</code>"
        )
    if event_type == "odds.moved":
        lines = []
        for item in payload.get("movements", [])[:6]:
            lines.append(
                f"#{item.get('program_number')} "
                f"{item.get('morning_odds')} → {item.get('mtp5_odds')} "
                f"({item.get('direction')})"
            )
        body = "\n".join(lines) or "Sin detalle"
        return f"<b>Odds Movement</b>\n{track} R{race_number}\n{body}"
    if event_type == "race.official":
        top = payload.get("top_three") or []
        order = " · ".join(
            f"{f.get('position')}º #{f.get('program_number')}" for f in top
        )
        divs = payload.get("dividends") or {}
        w = (divs.get("W") or {}).get("amount", "—")
        exa = (divs.get("EXA") or {}).get("amount", "—")
        tri = (divs.get("TRI") or {}).get("amount", "—")
        return (
            f"<b>Official</b> {track} R{race_number}\n"
            f"Llegada: {order}\n"
            f"W ${w} · EXA ${exa} · TRI ${tri}"
        )
    if event_type == "replay.ready":
        url = payload.get("video_replay_url", "")
        return (
            f"<b>Video Replay</b>\n"
            f"{track} R{race_number}\n"
            f"<a href=\"{url}\">Ver replay</a>"
        )
    if event_type == "race.next":
        mtp = payload.get("minutes_to_post")
        return (
            f"<b>NEXT</b> {track} R{race_number}\n"
            f"MTP: {mtp if mtp is not None else '—'}"
        )
    return f"<b>{event_type}</b>\n{track} R{race_number}"
