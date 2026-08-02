"""
Equibase client for US thoroughbred entries and results.

Equibase is the industry charting source. Their site uses bot protection
(Imperva), so this client:
  1) Attempts public HTML endpoints with polite throttling
  2) Falls back to structured parsing when HTML is available
  3) Raises EquibaseBlockedError when challenged so callers can switch source

URL patterns (public):
  Entries index:  https://www.equibase.com/static/entry/index.html
  Entries card:   https://www.equibase.com/static/entry/{TRACK}{MMDDYY}USA-EQB.html
  Chart summary:  https://www.equibase.com/static/chart/summary/{TRACK}{MMDDYY}USA-EQB.html
  Embedded chart: https://www.equibase.com/premium/chartEmb.cfm?track=GP&raceDate=MM/DD/YYYY&cy=USA&rn=1
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field
from datetime import date, datetime
from decimal import Decimal, InvalidOperation
from typing import Any
from zoneinfo import ZoneInfo

from bs4 import BeautifulSoup
from django.conf import settings

from .base import HttpClient

logger = logging.getLogger("scraper")

EQUIBASE_BASE = "https://www.equibase.com"
BLOCK_MARKERS = (
    "pardon our interruption",
    "something about your browser made us think you were a bot",
    "incapsula",
    "_incap_ses",
)


class EquibaseBlockedError(RuntimeError):
    """Raised when Equibase returns a bot-challenge page."""


@dataclass
class ParsedRunner:
    program_number: str
    horse_name: str
    jockey: str = ""
    trainer: str = ""
    morning_line_odds: str = ""
    weight: int | None = None
    scratched: bool = False
    post_position: int | None = None


@dataclass
class ParsedFinisher:
    position: int
    program_number: str
    horse_name: str = ""
    jockey: str = ""
    trainer: str = ""
    win_payoff: Decimal | None = None
    place_payoff: Decimal | None = None
    show_payoff: Decimal | None = None


@dataclass
class ParsedPayout:
    bet_type: str
    amount: Decimal
    combination: str = ""
    base_wager: Decimal = Decimal("2.00")


@dataclass
class ParsedRace:
    race_number: int
    race_name: str = ""
    race_type: str = ""
    distance: str = ""
    distance_furlongs: Decimal | None = None
    surface: str = "U"
    purse: Decimal | None = None
    post_time: datetime | None = None
    status: str = "scheduled"
    conditions: str = ""
    video_replay_url: str = ""
    runners: list[ParsedRunner] = field(default_factory=list)
    finishers: list[ParsedFinisher] = field(default_factory=list)
    payouts: list[ParsedPayout] = field(default_factory=list)
    winning_time: str = ""
    raw: dict[str, Any] = field(default_factory=dict)


@dataclass
class ParsedCard:
    track_code: str
    race_date: date
    races: list[ParsedRace] = field(default_factory=list)
    source: str = "equibase"


class EquibaseClient:
    """Fetch and parse Equibase entry/result HTML pages."""

    def __init__(self, http: HttpClient | None = None) -> None:
        self.http = http or HttpClient()

    @staticmethod
    def _date_token(race_date: date) -> str:
        return race_date.strftime("%m%d%y")

    @staticmethod
    def _is_blocked(html: str) -> bool:
        lowered = html.lower()
        return any(marker in lowered for marker in BLOCK_MARKERS)

    def _get_html(self, url: str, params: dict | None = None) -> str:
        response = self.http.get(url, params=params)
        text = response.text or ""
        if response.status_code == 403 or self._is_blocked(text):
            raise EquibaseBlockedError(
                f"Equibase blocked request ({response.status_code}): {url}"
            )
        response.raise_for_status()
        return text

    def entries_url(self, track_code: str, race_date: date) -> str:
        token = self._date_token(race_date)
        return f"{EQUIBASE_BASE}/static/entry/{track_code.upper()}{token}USA-EQB.html"

    def results_summary_url(self, track_code: str, race_date: date) -> str:
        token = self._date_token(race_date)
        return (
            f"{EQUIBASE_BASE}/static/chart/summary/"
            f"{track_code.upper()}{token}USA-EQB.html"
        )

    def chart_url(self, track_code: str, race_date: date, race_number: int) -> str:
        return (
            f"{EQUIBASE_BASE}/premium/chartEmb.cfm"
            f"?track={track_code.upper()}"
            f"&raceDate={race_date.strftime('%m/%d/%Y')}"
            f"&cy=USA&rn={race_number}"
        )

    def fetch_entries(self, track_code: str, race_date: date) -> ParsedCard:
        url = self.entries_url(track_code, race_date)
        html = self._get_html(url)
        return self.parse_entries_html(html, track_code, race_date)

    def fetch_results(self, track_code: str, race_date: date) -> ParsedCard:
        url = self.results_summary_url(track_code, race_date)
        html = self._get_html(url)
        return self.parse_results_html(html, track_code, race_date)

    def parse_entries_html(
        self, html: str, track_code: str, race_date: date
    ) -> ParsedCard:
        soup = BeautifulSoup(html, "lxml")
        races: list[ParsedRace] = []

        # Equibase entry pages typically group races in tables or race headers.
        race_headers = soup.find_all(
            ["h2", "h3", "b", "strong"],
            string=re.compile(r"Race\s+\d+", re.I),
        )
        if not race_headers:
            # Fallback: look for "Race N" text nodes anywhere
            race_headers = soup.find_all(string=re.compile(r"^\s*Race\s+\d+", re.I))

        for header in race_headers:
            header_text = header.get_text(" ", strip=True) if hasattr(header, "get_text") else str(header)
            match = re.search(r"Race\s+(\d+)", header_text, re.I)
            if not match:
                continue
            race_number = int(match.group(1))
            section = header.find_parent(["div", "table", "section", "tr"]) or header
            block_text = section.get_text(" ", strip=True) if hasattr(section, "get_text") else header_text

            distance, surface = self._parse_distance_surface(block_text)
            post_time = self._parse_post_time(block_text, race_date)
            purse = self._parse_purse(block_text)

            runners = self._parse_runners_near(section)
            races.append(
                ParsedRace(
                    race_number=race_number,
                    race_name=header_text[:255],
                    distance=distance,
                    distance_furlongs=self._distance_to_furlongs(distance),
                    surface=surface,
                    purse=purse,
                    post_time=post_time,
                    status="scheduled",
                    runners=runners,
                    raw={"header": header_text},
                )
            )

        # Deduplicate by race number (keep richest parse)
        by_number: dict[int, ParsedRace] = {}
        for race in races:
            existing = by_number.get(race.race_number)
            if not existing or len(race.runners) > len(existing.runners):
                by_number[race.race_number] = race

        return ParsedCard(
            track_code=track_code.upper(),
            race_date=race_date,
            races=sorted(by_number.values(), key=lambda r: r.race_number),
        )

    def parse_results_html(
        self, html: str, track_code: str, race_date: date
    ) -> ParsedCard:
        soup = BeautifulSoup(html, "lxml")
        races: list[ParsedRace] = []
        text = soup.get_text("\n", strip=True)

        # Split by race markers commonly found in summary charts
        chunks = re.split(r"(?=Race\s+\d+\b)", text, flags=re.I)
        for chunk in chunks:
            match = re.match(r"Race\s+(\d+)", chunk, re.I)
            if not match:
                continue
            race_number = int(match.group(1))
            distance, surface = self._parse_distance_surface(chunk)
            finishers = self._parse_finishers(chunk)
            payouts = self._parse_payouts(chunk)
            winning_time = self._parse_winning_time(chunk)

            races.append(
                ParsedRace(
                    race_number=race_number,
                    distance=distance,
                    distance_furlongs=self._distance_to_furlongs(distance),
                    surface=surface,
                    status="official" if finishers else "scheduled",
                    finishers=finishers,
                    payouts=payouts,
                    winning_time=winning_time,
                    video_replay_url=self._guess_replay_url(track_code, race_date, race_number),
                    raw={"snippet": chunk[:500]},
                )
            )

        return ParsedCard(
            track_code=track_code.upper(),
            race_date=race_date,
            races=races,
        )

    def _parse_runners_near(self, section) -> list[ParsedRunner]:
        runners: list[ParsedRunner] = []
        table = None
        if hasattr(section, "find"):
            table = section.find("table")
            if not table and section.parent:
                table = section.parent.find("table")
        if not table:
            return runners

        for row in table.find_all("tr"):
            cells = [c.get_text(" ", strip=True) for c in row.find_all(["td", "th"])]
            if len(cells) < 2:
                continue
            prog = cells[0]
            if not re.match(r"^\d+[A-Z]?$", prog):
                continue
            horse = cells[1]
            jockey = cells[2] if len(cells) > 2 else ""
            trainer = cells[3] if len(cells) > 3 else ""
            ml = ""
            for cell in cells:
                if re.match(r"^\d+/\d+$|^\d+\.\d+$|^EVEN$", cell, re.I):
                    ml = cell
                    break
            scratched = any("scratch" in c.lower() for c in cells)
            runners.append(
                ParsedRunner(
                    program_number=prog,
                    horse_name=horse,
                    jockey=jockey,
                    trainer=trainer,
                    morning_line_odds=ml,
                    scratched=scratched,
                    post_position=int(re.sub(r"\D", "", prog) or 0) or None,
                )
            )
        return runners

    def _parse_finishers(self, text: str) -> list[ParsedFinisher]:
        finishers: list[ParsedFinisher] = []
        # Prefer ordinals (1st/2nd/...) to avoid matching distances like "1 1/16M".
        patterns = [
            r"\b1st\s+#?(\d+[A-Z]?)",
            r"\b2nd\s+#?(\d+[A-Z]?)",
            r"\b3rd\s+#?(\d+[A-Z]?)",
            r"\b4th\s+#?(\d+[A-Z]?)",
        ]
        for idx, pattern in enumerate(patterns, start=1):
            match = re.search(pattern, text, re.I)
            if match:
                finishers.append(
                    ParsedFinisher(position=idx, program_number=match.group(1))
                )
        if finishers:
            return finishers

        # Fallback: "1. 9 Horse" style rows
        for idx in range(1, 5):
            match = re.search(rf"(?m)^\s*{idx}\.\s+#?(\d+[A-Z]?)\b", text)
            if match:
                finishers.append(
                    ParsedFinisher(position=idx, program_number=match.group(1))
                )
        return finishers

    def _parse_payouts(self, text: str) -> list[ParsedPayout]:
        payouts: list[ParsedPayout] = []
        mapping = {
            r"\bWin\b|\bWPS?\b|\bGanador\b": "W",
            r"\bPlace\b|\bPlac[eé]\b": "P",
            r"\bShow\b": "S",
            r"\bExacta\b|\bEXA\b": "EXA",
            r"\bTrifecta\b|\bTRI\b": "TRI",
            r"\bSuperfecta\b|\bSUPER\b": "SUPER",
        }
        money = r"\$?\s*([\d,]+\.\d{2})"
        for pattern, bet_type in mapping.items():
            # Wrap alternations so the trailing money capture always applies.
            match = re.search(rf"(?:{pattern})[^\d$]{{0,40}}{money}", text, re.I)
            if match:
                try:
                    amount = Decimal(match.group(1).replace(",", ""))
                except (InvalidOperation, AttributeError):
                    continue
                payouts.append(ParsedPayout(bet_type=bet_type, amount=amount))
        return payouts

    def _parse_winning_time(self, text: str) -> str:
        match = re.search(r"(?:Final Time|Time)[:\s]+(\d+:\d{2}\.\d{2})", text, re.I)
        return match.group(1) if match else ""

    def _parse_distance_surface(self, text: str) -> tuple[str, str]:
        # e.g. "1 1/16M T", "6 Furlongs Dirt", "One Mile Turf"
        dist_match = re.search(
            r"((\d+\s+\d/\d+|\d+/\d+|\d+)\s*(?:M|Mile|Miles|F|Furlongs?))",
            text,
            re.I,
        )
        distance = dist_match.group(0).strip() if dist_match else ""
        surface = "U"
        if re.search(r"\bTurf\b|\b\bT\b", text, re.I):
            surface = "T"
        elif re.search(r"\bDirt\b|\bD\b", text, re.I):
            surface = "D"
        elif re.search(r"\bSynthetic\b|\bAll Weather\b|\bS\b", text, re.I):
            surface = "S"
        # Compact app-friendly form like "1 1/16M T"
        if distance and surface in {"T", "D", "S"}:
            compact = re.sub(r"(?i)furlongs?", "F", distance)
            compact = re.sub(r"(?i)miles?", "M", compact)
            compact = re.sub(r"(?i)\bmile\b", "M", compact)
            return f"{compact} {surface}".strip(), surface
        return distance, surface

    def _parse_purse(self, text: str) -> Decimal | None:
        match = re.search(r"Purse[:\s]+\$?([\d,]+)", text, re.I)
        if not match:
            return None
        try:
            return Decimal(match.group(1).replace(",", ""))
        except InvalidOperation:
            return None

    def _parse_post_time(self, text: str, race_date: date) -> datetime | None:
        match = re.search(
            r"(?:Post(?:\s*Time)?|PT)[:\s]*(\d{1,2}:\d{2}\s*[AP]M)",
            text,
            re.I,
        )
        if not match:
            return None
        try:
            parsed = datetime.strptime(match.group(1).upper().replace(" ", ""), "%I:%M%p")
            tz = ZoneInfo(settings.TIME_ZONE)
            return datetime.combine(race_date, parsed.time(), tzinfo=tz)
        except ValueError:
            return None

    def _distance_to_furlongs(self, distance: str) -> Decimal | None:
        if not distance:
            return None
        # Miles
        mile_match = re.search(r"((\d+)\s+)?(\d+)/(\d+)\s*M\b", distance, re.I)
        if mile_match:
            whole = int(mile_match.group(2) or 0)
            num = int(mile_match.group(3))
            den = int(mile_match.group(4))
            miles = Decimal(whole) + (Decimal(num) / Decimal(den))
            return miles * Decimal("8")
        simple_mile = re.search(r"(\d+)\s*M\b", distance, re.I)
        if simple_mile:
            return Decimal(simple_mile.group(1)) * Decimal("8")
        furlong = re.search(r"(\d+(?:\.\d+)?)\s*F\b", distance, re.I)
        if furlong:
            return Decimal(furlong.group(1))
        return None

    def _guess_replay_url(
        self, track_code: str, race_date: date, race_number: int
    ) -> str:
        # Equibase replay landing; concrete stream URLs vary by meet.
        return (
            f"{EQUIBASE_BASE}/premium/eqbPDFChartPlus.cfm"
            f"?RACE={race_number}&TID={track_code.upper()}"
            f"&CTRY=USA&DT={race_date.strftime('%m/%d/%Y')}&DAY=D&STYLE=EQB"
        )


# Catalog of major US (and key Canadian) tracks for seeding / cron targeting
MAJOR_TRACKS: list[dict[str, str]] = [
    {"code": "GP", "name": "Gulfstream Park", "state": "FL", "timezone": "America/New_York"},
    {"code": "CD", "name": "Churchill Downs", "state": "KY", "timezone": "America/New_York"},
    {"code": "SAR", "name": "Saratoga", "state": "NY", "timezone": "America/New_York"},
    {"code": "BAQ", "name": "Belmont at the Big A", "state": "NY", "timezone": "America/New_York"},
    {"code": "AQU", "name": "Aqueduct", "state": "NY", "timezone": "America/New_York"},
    {"code": "BEL", "name": "Belmont Park", "state": "NY", "timezone": "America/New_York"},
    {"code": "SA", "name": "Santa Anita Park", "state": "CA", "timezone": "America/Los_Angeles"},
    {"code": "DMR", "name": "Del Mar", "state": "CA", "timezone": "America/Los_Angeles"},
    {"code": "KEE", "name": "Keeneland", "state": "KY", "timezone": "America/New_York"},
    {"code": "OP", "name": "Oaklawn Park", "state": "AR", "timezone": "America/Chicago"},
    {"code": "PIM", "name": "Pimlico", "state": "MD", "timezone": "America/New_York"},
    {"code": "LRL", "name": "Laurel Park", "state": "MD", "timezone": "America/New_York"},
    {"code": "IND", "name": "Horseshoe Indianapolis", "state": "IN", "timezone": "America/Indiana/Indianapolis"},
    {"code": "ELP", "name": "Ellis Park", "state": "KY", "timezone": "America/Chicago"},
    {"code": "FG", "name": "Fair Grounds", "state": "LA", "timezone": "America/Chicago"},
    {"code": "TAM", "name": "Tampa Bay Downs", "state": "FL", "timezone": "America/New_York"},
    {"code": "TP", "name": "Turfway Park", "state": "KY", "timezone": "America/New_York"},
    {"code": "WO", "name": "Woodbine", "state": "ON", "timezone": "America/Toronto", "country": "CAN"},
    {"code": "PRX", "name": "Parx Racing", "state": "PA", "timezone": "America/New_York"},
    {"code": "MTH", "name": "Monmouth Park", "state": "NJ", "timezone": "America/New_York"},
    {"code": "CNL", "name": "Colonial Downs", "state": "VA", "timezone": "America/New_York"},
]
