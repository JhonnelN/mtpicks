"""
Optional licensed client for The Racing API (North America add-on).

Docs: https://api.theracingapi.com/documentation
Requires RACING_API_USERNAME / RACING_API_PASSWORD and the North America add-on.
"""

from __future__ import annotations

import logging
from datetime import date, datetime
from decimal import Decimal, InvalidOperation
from typing import Any
from zoneinfo import ZoneInfo

from django.conf import settings
from requests.auth import HTTPBasicAuth

from .base import HttpClient
from .equibase import ParsedCard, ParsedFinisher, ParsedPayout, ParsedRace, ParsedRunner

logger = logging.getLogger("scraper")


class RacingApiClient:
    """Fetch North American meets/results from The Racing API."""

    def __init__(self, http: HttpClient | None = None) -> None:
        self.http = http or HttpClient()
        self.base = settings.RACING_API_BASE_URL.rstrip("/")
        self.auth = HTTPBasicAuth(
            settings.RACING_API_USERNAME,
            settings.RACING_API_PASSWORD,
        )

    @property
    def configured(self) -> bool:
        return bool(settings.RACING_API_USERNAME and settings.RACING_API_PASSWORD)

    def _get_json(self, path: str, params: dict[str, Any] | None = None) -> Any:
        if not self.configured:
            raise RuntimeError(
                "Racing API credentials missing. Set RACING_API_USERNAME and "
                "RACING_API_PASSWORD in your .env file."
            )
        url = f"{self.base}{path}"
        response = self.http.get(url, params=params, auth=self.auth)
        response.raise_for_status()
        return response.json()

    def list_meets(self, start: date, end: date | None = None) -> list[dict]:
        end = end or start
        payload = self._get_json(
            "/v1/north-america/meets",
            params={
                "start_date": start.isoformat(),
                "end_date": end.isoformat(),
            },
        )
        if isinstance(payload, dict):
            return payload.get("meets") or payload.get("results") or []
        return payload if isinstance(payload, list) else []

    def meet_entries(self, meet_id: str) -> dict:
        return self._get_json(f"/v1/north-america/meets/{meet_id}/entries")

    def meet_results(self, meet_id: str) -> dict:
        return self._get_json(f"/v1/north-america/meets/{meet_id}/results")

    def fetch_card(
        self, track_code: str, race_date: date, *, include_results: bool = True
    ) -> ParsedCard:
        meets = self.list_meets(race_date)
        meet = next(
            (
                m
                for m in meets
                if str(m.get("course_code") or m.get("track_code") or "").upper()
                == track_code.upper()
            ),
            None,
        )
        if not meet:
            return ParsedCard(track_code=track_code.upper(), race_date=race_date, races=[])

        meet_id = str(meet.get("meet_id") or meet.get("id"))
        entries = self.meet_entries(meet_id)
        results = self.meet_results(meet_id) if include_results else {}
        return self._normalize_meet(track_code, race_date, entries, results)

    def _normalize_meet(
        self,
        track_code: str,
        race_date: date,
        entries: dict,
        results: dict,
    ) -> ParsedCard:
        races_payload = entries.get("races") or entries.get("results") or []
        results_by_number = {
            int(r.get("race_number") or r.get("number") or 0): r
            for r in (results.get("races") or results.get("results") or [])
            if r.get("race_number") or r.get("number")
        }

        races: list[ParsedRace] = []
        for item in races_payload:
            race_number = int(item.get("race_number") or item.get("number") or 0)
            if not race_number:
                continue

            runners = []
            for runner in item.get("runners") or item.get("entries") or []:
                runners.append(
                    ParsedRunner(
                        program_number=str(
                            runner.get("number")
                            or runner.get("program_number")
                            or runner.get("saddle_cloth")
                            or ""
                        ),
                        horse_name=str(runner.get("horse") or runner.get("horse_name") or ""),
                        jockey=str(runner.get("jockey") or ""),
                        trainer=str(runner.get("trainer") or ""),
                        morning_line_odds=str(
                            runner.get("odds") or runner.get("morning_line") or ""
                        ),
                        scratched=bool(runner.get("scratched")),
                        post_position=self._safe_int(runner.get("draw") or runner.get("post")),
                    )
                )

            finishers: list[ParsedFinisher] = []
            payouts: list[ParsedPayout] = []
            status = "scheduled"
            winning_time = ""
            result_item = results_by_number.get(race_number)
            if result_item:
                status = "official"
                winning_time = str(result_item.get("winning_time") or "")
                for fin in result_item.get("finishers") or result_item.get("runners") or []:
                    pos = self._safe_int(fin.get("position") or fin.get("pos"))
                    if not pos:
                        continue
                    finishers.append(
                        ParsedFinisher(
                            position=pos,
                            program_number=str(fin.get("number") or fin.get("program_number") or ""),
                            horse_name=str(fin.get("horse") or fin.get("horse_name") or ""),
                            jockey=str(fin.get("jockey") or ""),
                            trainer=str(fin.get("trainer") or ""),
                        )
                    )
                for payoff in result_item.get("payoffs") or result_item.get("payouts") or []:
                    bet = str(payoff.get("type") or payoff.get("bet_type") or "").upper()
                    amount = self._safe_decimal(payoff.get("amount") or payoff.get("dividend"))
                    if bet and amount is not None:
                        payouts.append(
                            ParsedPayout(
                                bet_type=self._map_bet_type(bet),
                                amount=amount,
                                combination=str(payoff.get("combination") or ""),
                            )
                        )

            races.append(
                ParsedRace(
                    race_number=race_number,
                    race_name=str(item.get("race_name") or item.get("title") or ""),
                    race_type=str(item.get("race_type") or item.get("type") or ""),
                    distance=str(item.get("distance") or ""),
                    surface=self._map_surface(str(item.get("surface") or "")),
                    purse=self._safe_decimal(item.get("purse")),
                    post_time=self._parse_dt(item.get("off_time") or item.get("post_time")),
                    status=status,
                    runners=runners,
                    finishers=finishers,
                    payouts=payouts,
                    winning_time=winning_time,
                    raw=item,
                )
            )

        return ParsedCard(
            track_code=track_code.upper(),
            race_date=race_date,
            races=sorted(races, key=lambda r: r.race_number),
            source="racing_api",
        )

    @staticmethod
    def _map_surface(value: str) -> str:
        lowered = value.lower()
        if "turf" in lowered:
            return "T"
        if "dirt" in lowered:
            return "D"
        if "synth" in lowered or "all weather" in lowered:
            return "S"
        return "U"

    @staticmethod
    def _map_bet_type(value: str) -> str:
        mapping = {
            "WIN": "W",
            "W": "W",
            "PLACE": "P",
            "P": "P",
            "SHOW": "S",
            "S": "S",
            "EXACTA": "EXA",
            "EXA": "EXA",
            "TRIFECTA": "TRI",
            "TRI": "TRI",
            "SUPERFECTA": "SUPER",
            "SUPER": "SUPER",
        }
        return mapping.get(value.upper(), value.upper()[:10])

    @staticmethod
    def _safe_int(value: Any) -> int | None:
        try:
            return int(value) if value is not None and value != "" else None
        except (TypeError, ValueError):
            return None

    @staticmethod
    def _safe_decimal(value: Any) -> Decimal | None:
        if value is None or value == "":
            return None
        try:
            return Decimal(str(value).replace(",", "").replace("$", ""))
        except (InvalidOperation, ValueError):
            return None

    @staticmethod
    def _parse_dt(value: Any) -> datetime | None:
        if not value:
            return None
        if isinstance(value, datetime):
            return value
        text = str(value).replace("Z", "+00:00")
        try:
            return datetime.fromisoformat(text)
        except ValueError:
            return None
