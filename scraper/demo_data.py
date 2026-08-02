"""
Deterministic demo cards used when Equibase is blocked / no API key is set.
"""

from __future__ import annotations

from datetime import date, datetime, timedelta
from decimal import Decimal
from zoneinfo import ZoneInfo

from django.conf import settings
from django.utils import timezone

from integrations.dispatcher import emit
from racing.models import VipPick
from racing.odds import (
    capture_morning_line_snapshots,
    capture_mtp5_snapshots,
    compute_odds_movements,
    synthetic_mtp5_odds,
)

from .clients.equibase import (
    ParsedCard,
    ParsedFinisher,
    ParsedPayout,
    ParsedRace,
    ParsedRunner,
)


def build_demo_card(
    track_code: str, race_date: date, *, with_results: bool = True
) -> ParsedCard:
    tz = ZoneInfo(settings.TIME_ZONE)
    now = timezone.now().astimezone(tz)
    anchor = now - timedelta(hours=3)
    if anchor.date() != race_date:
        anchor = datetime.combine(race_date, datetime.min.time(), tzinfo=tz).replace(
            hour=11, minute=0
        )
    base_post = anchor.replace(second=0, microsecond=0)

    races: list[ParsedRace] = []
    sample_fields = [
        ("1 1/16M T", "T", Decimal("8.5")),
        ("6F D", "D", Decimal("6")),
        ("1M T", "T", Decimal("8")),
        ("7F D", "D", Decimal("7")),
        ("1 1/16M D", "D", Decimal("8.5")),
        ("5F T", "T", Decimal("5")),
        ("1 1/8M D", "D", Decimal("9")),
        ("1M D", "D", Decimal("8")),
    ]

    for idx, (distance, surface, furlongs) in enumerate(sample_fields, start=1):
        post_time = base_post + timedelta(minutes=30 * (idx - 1))
        runners = [
            ParsedRunner(
                program_number=str(n),
                horse_name=f"Demo Horse {track_code}-{idx}-{n}",
                jockey=f"Jockey {n}",
                trainer=f"Trainer {n}",
                morning_line_odds=f"{n + 1}/1",
                post_position=n,
            )
            for n in range(1, 11)
        ]

        finishers: list[ParsedFinisher] = []
        payouts: list[ParsedPayout] = []
        status = "scheduled"
        video = ""

        if with_results and post_time < now:
            status = "official"
            winner = "9" if idx == 6 else "4"
            finishers = [
                ParsedFinisher(position=1, program_number=winner, horse_name="Winner"),
                ParsedFinisher(position=2, program_number="2", horse_name="Place"),
                ParsedFinisher(position=3, program_number="7", horse_name="Show"),
            ]
            payouts = [
                ParsedPayout(bet_type="W", amount=Decimal("8.40"), combination=winner),
                ParsedPayout(bet_type="P", amount=Decimal("4.20"), combination=winner),
                ParsedPayout(bet_type="S", amount=Decimal("3.00"), combination=winner),
                ParsedPayout(
                    bet_type="EXA",
                    amount=Decimal("42.60"),
                    combination=f"{winner}-2",
                ),
                ParsedPayout(
                    bet_type="TRI",
                    amount=Decimal("158.80"),
                    combination=f"{winner}-2-7",
                ),
            ]
            video = f"https://example.com/replay/{track_code}/{race_date}/R{idx}"
        else:
            status = "scheduled"

        races.append(
            ParsedRace(
                race_number=idx,
                race_name=f"{track_code} Race {idx}",
                race_type="Allowance" if idx % 2 else "Maiden Special Weight",
                distance=distance,
                distance_furlongs=furlongs,
                surface=surface,
                purse=Decimal("45000") + Decimal(idx * 5000),
                post_time=post_time,
                status=status,
                runners=runners,
                finishers=finishers,
                payouts=payouts,
                winning_time="1:42.35" if finishers else "",
                video_replay_url=video,
            )
        )

    return ParsedCard(
        track_code=track_code.upper(),
        race_date=race_date,
        races=races,
        source="demo",
    )


def seed_vip_picks_for_track(track_code: str, race_date: date) -> int:
    """Create morning / 5 MTP VIP boards, odds snapshots and movements."""
    from racing.models import Race

    races = Race.objects.filter(
        race_day__track__code=track_code.upper(),
        race_day__race_date=race_date,
    ).prefetch_related("runners")
    created = 0
    patterns = [
        ["4", "2", "9", "7"],
        ["1", "5", "3", "8"],
        ["6", "2", "4", "1"],
        ["3", "7", "5", "9"],
        ["2", "8", "1", "4"],
        ["9", "2", "7", "3"],
        ["5", "1", "6", "2"],
        ["8", "4", "3", "7"],
    ]
    for race in races:
        morning = patterns[(race.race_number - 1) % len(patterns)]
        mtp5 = morning[:]
        if race.status == Race.Status.NEXT or (
            race.minutes_to_post is not None and race.minutes_to_post <= 15
        ):
            mtp5 = [morning[1], morning[0], morning[3], morning[2]]

        for window, selections in (
            (VipPick.PickWindow.MORNING, morning),
            (VipPick.PickWindow.MTP5, mtp5),
            (VipPick.PickWindow.LAST_HOUR, mtp5),
        ):
            _, was_created = VipPick.objects.update_or_create(
                race=race,
                pick_window=window,
                defaults={"selections": selections, "notes": "demo"},
            )
            if was_created:
                created += 1

        capture_morning_line_snapshots(race, source="demo")
        odds_map = {
            r.program_number: synthetic_mtp5_odds(r.morning_line_odds or "5/1")
            for r in race.runners.all()
        }
        capture_mtp5_snapshots(race, odds_map, source="demo")
        movements = compute_odds_movements(race, morning)

        emit(
            "picks.morning_published",
            {
                "race_id": race.id,
                "track_code": race.track_code,
                "race_number": race.race_number,
                "race_date": race_date.isoformat(),
                "selections": morning,
            },
        )
        emit(
            "picks.mtp5_published",
            {
                "race_id": race.id,
                "track_code": race.track_code,
                "race_number": race.race_number,
                "race_date": race_date.isoformat(),
                "selections": mtp5,
            },
        )
        moved = [m for m in movements if m.direction != "unchanged"]
        if moved:
            emit(
                "odds.moved",
                {
                    "race_id": race.id,
                    "track_code": race.track_code,
                    "race_number": race.race_number,
                    "race_date": race_date.isoformat(),
                    "movements": [
                        {
                            "program_number": m.program_number,
                            "morning_odds": m.morning_odds,
                            "mtp5_odds": m.mtp5_odds,
                            "direction": m.direction,
                        }
                        for m in moved
                    ],
                },
            )
    return created
