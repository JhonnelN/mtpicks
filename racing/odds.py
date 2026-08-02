"""Odds parsing and morning → 5 MTP movement helpers."""

from __future__ import annotations

import re
from decimal import Decimal, InvalidOperation

from django.utils import timezone

from .models import OddsMovement, OddsSnapshot, Race, Runner, VipPick


def parse_odds_to_decimal(odds: str) -> Decimal | None:
    """Convert common US odds strings (5/2, 6-1, 3.5, EVEN) to decimal odds."""
    if not odds:
        return None
    text = odds.strip().upper().replace(" ", "")
    if text in {"EVEN", "EVENS", "1/1", "1-1"}:
        return Decimal("2.0")
    frac = re.match(r"^(\d+(?:\.\d+)?)/(\d+(?:\.\d+)?)$", text)
    if frac:
        num = Decimal(frac.group(1))
        den = Decimal(frac.group(2))
        if den == 0:
            return None
        return (num / den) + Decimal("1")
    dash = re.match(r"^(\d+(?:\.\d+)?)-(\d+(?:\.\d+)?)$", text)
    if dash:
        num = Decimal(dash.group(1))
        den = Decimal(dash.group(2))
        if den == 0:
            return None
        return (num / den) + Decimal("1")
    # Bare integer on US boards usually means X-1 (e.g. "2" → 2/1, "3" → 3/1)
    if re.match(r"^\d+$", text):
        return Decimal(text) + Decimal("1")
    try:
        value = Decimal(text)
        # Decimal odds already (e.g. 3.5); keep if > 1
        return value if value > 1 else value + Decimal("1")
    except InvalidOperation:
        return None


def capture_morning_line_snapshots(race: Race, *, source: str = "morning_line") -> int:
    """Store ML odds from runners as OddsSnapshot(mtp_minutes=None)."""
    created = 0
    for runner in race.runners.filter(scratched=False):
        if not runner.morning_line_odds:
            continue
        _, was_created = OddsSnapshot.objects.update_or_create(
            race=race,
            program_number=runner.program_number,
            mtp_minutes=None,
            defaults={
                "odds": runner.morning_line_odds,
                "odds_decimal": parse_odds_to_decimal(runner.morning_line_odds),
                "source": source,
                "captured_at": timezone.now(),
            },
        )
        if was_created:
            created += 1
    return created


def capture_mtp5_snapshots(
    race: Race,
    odds_by_number: dict[str, str],
    *,
    source: str = "live",
) -> int:
    """Store 5 MTP odds snapshots for the given program numbers."""
    created = 0
    for program_number, odds in odds_by_number.items():
        _, was_created = OddsSnapshot.objects.update_or_create(
            race=race,
            program_number=str(program_number),
            mtp_minutes=5,
            defaults={
                "odds": odds,
                "odds_decimal": parse_odds_to_decimal(odds),
                "source": source,
                "captured_at": timezone.now(),
            },
        )
        if was_created:
            created += 1
    return created


def synthetic_mtp5_odds(morning_odds: str, *, drift_factor: float = 0.85) -> str:
    """
    Demo helper: shorten favorites slightly for 5 MTP movement.
    Returns fractional-ish string when possible.
    """
    dec = parse_odds_to_decimal(morning_odds)
    if dec is None:
        return morning_odds
    # Shorten toward even money
    new_dec = Decimal("1") + (dec - Decimal("1")) * Decimal(str(drift_factor))
    if new_dec < Decimal("1.2"):
        new_dec = Decimal("1.2")
    # Represent as X/1 style when close to integer
    profit = new_dec - Decimal("1")
    if profit == profit.to_integral_value():
        return f"{int(profit)}/1"
    # Keep one decimal as decimal odds string
    return f"{new_dec:.2f}"


def compute_odds_movements(race: Race, program_numbers: list[str] | None = None) -> list[OddsMovement]:
    """Compare morning vs 5 MTP snapshots for VIP selections (or all provided)."""
    if program_numbers is None:
        morning_pick = race.vip_picks.filter(pick_window=VipPick.PickWindow.MORNING).first()
        program_numbers = list(morning_pick.selections) if morning_pick else [
            r.program_number for r in race.runners.all()
        ]

    morning_map = {
        s.program_number: s
        for s in race.odds_snapshots.filter(mtp_minutes__isnull=True)
    }
    mtp_map = {
        s.program_number: s for s in race.odds_snapshots.filter(mtp_minutes=5)
    }

    results: list[OddsMovement] = []
    for number in program_numbers:
        morning = morning_map.get(str(number))
        mtp = mtp_map.get(str(number))
        morning_odds = morning.odds if morning else ""
        mtp5_odds = mtp.odds if mtp else ""
        morning_dec = morning.odds_decimal if morning else parse_odds_to_decimal(morning_odds)
        mtp_dec = mtp.odds_decimal if mtp else parse_odds_to_decimal(mtp5_odds)

        direction = OddsMovement.Direction.UNCHANGED
        delta = None
        if morning_dec is not None and mtp_dec is not None:
            delta = mtp_dec - morning_dec
            if delta < Decimal("-0.05"):
                direction = OddsMovement.Direction.SHORTENED
            elif delta > Decimal("0.05"):
                direction = OddsMovement.Direction.DRIFTED

        movement, _ = OddsMovement.objects.update_or_create(
            race=race,
            program_number=str(number),
            defaults={
                "morning_odds": morning_odds,
                "mtp5_odds": mtp5_odds,
                "morning_decimal": morning_dec,
                "mtp5_decimal": mtp_dec,
                "delta": delta,
                "direction": direction,
            },
        )
        results.append(movement)
    return results


def ensure_runner_ml_from_snapshots(race: Race) -> None:
    """Backfill runner morning_line_odds from snapshots if missing."""
    for snap in race.odds_snapshots.filter(mtp_minutes__isnull=True):
        Runner.objects.filter(
            race=race, program_number=snap.program_number, morning_line_odds=""
        ).update(morning_line_odds=snap.odds)


def favorites_board(race: Race, *, limit: int = 4) -> list[dict]:
    """
    Top favorites from the odds board (shortest current odds first).

    Prefers latest 5 MTP snapshots; falls back to morning line / runner ML.
    Matches BetAmerica pizarra 'O' column ordering.
    """
    snaps = list(race.odds_snapshots.filter(mtp_minutes=5))
    if not snaps:
        snaps = list(race.odds_snapshots.filter(mtp_minutes__isnull=True))

    board: list[dict] = []
    if snaps:
        for snap in snaps:
            dec = snap.odds_decimal or parse_odds_to_decimal(snap.odds)
            if dec is None:
                continue
            board.append(
                {
                    "program_number": snap.program_number,
                    "odds": snap.odds,
                    "odds_decimal": dec,
                    "source": snap.source,
                }
            )
    else:
        for runner in race.runners.filter(scratched=False):
            odds = runner.morning_line_odds
            dec = parse_odds_to_decimal(odds)
            if not odds or dec is None:
                continue
            board.append(
                {
                    "program_number": runner.program_number,
                    "odds": odds,
                    "odds_decimal": dec,
                    "source": "morning_line",
                }
            )

    board.sort(key=lambda row: row["odds_decimal"])
    ranked = []
    for idx, row in enumerate(board[:limit], start=1):
        ranked.append(
            {
                "rank": idx,
                "program_number": row["program_number"],
                "odds": row["odds"],
                "odds_decimal": str(row["odds_decimal"]),
                "source": row["source"],
            }
        )
    return ranked
