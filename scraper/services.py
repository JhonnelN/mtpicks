"""
Orchestration layer: choose source, scrape cards, upsert into Django models,
capture odds, enrich replays, and emit outbound integration events.
"""

from __future__ import annotations

import logging
from datetime import date, timedelta
from typing import Iterable

from django.conf import settings
from django.db import transaction
from django.utils import timezone

from integrations.dispatcher import emit
from racing.models import (
    Finisher,
    Payout,
    Race,
    RaceDay,
    RaceResult,
    Runner,
    ScrapeJob,
    Track,
    VipPick,
)
from racing.odds import (
    capture_morning_line_snapshots,
    capture_mtp5_snapshots,
    compute_odds_movements,
    synthetic_mtp5_odds,
)

from .clients.equibase import (
    MAJOR_TRACKS,
    EquibaseBlockedError,
    EquibaseClient,
    ParsedCard,
)
from .clients.racing_api import RacingApiClient

logger = logging.getLogger("scraper")


def ensure_tracks(track_defs: Iterable[dict] | None = None) -> int:
    """Upsert major track catalog. Returns created+updated count."""
    created_or_updated = 0
    for item in track_defs or MAJOR_TRACKS:
        _, created = Track.objects.update_or_create(
            code=item["code"].upper(),
            defaults={
                "name": item["name"],
                "state": item.get("state", ""),
                "country": item.get("country", "USA"),
                "timezone": item.get("timezone", "America/New_York"),
                "is_active": True,
            },
        )
        created_or_updated += 1 if created else 0
    return created_or_updated


def resolve_track_codes(track_codes: list[str] | None = None) -> list[str]:
    if track_codes:
        return [c.upper() for c in track_codes]
    return [c.upper() for c in settings.DEFAULT_TRACK_CODES]


def _race_payload_base(race: Race) -> dict:
    return {
        "race_id": race.id,
        "track_code": race.track_code,
        "race_number": race.race_number,
        "race_date": race.race_day.race_date.isoformat(),
        "status": race.status,
        "minutes_to_post": race.minutes_to_post,
        "distance": race.distance,
        "surface": race.surface,
    }


def _dividends_map(race: Race) -> dict:
    mapping = {}
    for payout in race.payouts.all():
        mapping[payout.bet_type] = {
            "amount": float(payout.amount),
            "combination": payout.combination,
            "base_wager": float(payout.base_wager),
        }
    return mapping


class ScrapeService:
    """High-level scrape operations used by management commands and cron."""

    def __init__(self, source: str | None = None) -> None:
        raw = source or settings.SCRAPER_SOURCE
        self.sources = [
            s.strip().lower() for s in str(raw).split(",") if s.strip()
        ] or list(settings.SCRAPER_SOURCES)
        self.source = ",".join(self.sources)
        self.equibase = EquibaseClient()
        self.racing_api = RacingApiClient()

    def fetch_card(
        self, track_code: str, race_date: date, *, want_results: bool
    ) -> ParsedCard:
        errors: list[str] = []
        for source_name in self.sources:
            try:
                card = self._fetch_from_source(
                    source_name, track_code, race_date, want_results=want_results
                )
                if card.races:
                    logger.info(
                        "Source %s OK for %s %s (%s races)",
                        source_name,
                        track_code,
                        race_date,
                        len(card.races),
                    )
                    return card
                errors.append(f"{source_name}: empty card")
            except EquibaseBlockedError as exc:
                logger.warning("Source %s blocked: %s", source_name, exc)
                errors.append(f"{source_name}: blocked")
            except Exception as exc:  # noqa: BLE001
                logger.warning("Source %s failed: %s", source_name, exc)
                errors.append(f"{source_name}: {exc}")

        from .demo_data import build_demo_card

        logger.warning(
            "All sources failed for %s %s (%s). Falling back to demo.",
            track_code,
            race_date,
            "; ".join(errors) or "no races",
        )
        return build_demo_card(track_code, race_date, with_results=want_results)

    def _fetch_from_source(
        self,
        source_name: str,
        track_code: str,
        race_date: date,
        *,
        want_results: bool,
    ) -> ParsedCard:
        if source_name == "demo":
            from .demo_data import build_demo_card

            return build_demo_card(track_code, race_date, with_results=want_results)

        if source_name == "racing_api":
            return self.racing_api.fetch_card(
                track_code, race_date, include_results=want_results
            )

        if source_name == "equibase":
            if want_results:
                return self.equibase.fetch_results(track_code, race_date)
            return self.equibase.fetch_entries(track_code, race_date)

        raise ValueError(
            f"Unknown scraper source '{source_name}'. "
            "Supported: equibase, racing_api, demo"
        )

    @transaction.atomic
    def upsert_card(self, card: ParsedCard) -> int:
        track, _ = Track.objects.get_or_create(
            code=card.track_code,
            defaults={
                "name": card.track_code,
                "timezone": "America/New_York",
            },
        )
        race_day, _ = RaceDay.objects.update_or_create(
            track=track,
            race_date=card.race_date,
            defaults={
                "source": card.source,
                "scraped_at": timezone.now(),
                "first_post_time": next(
                    (r.post_time for r in card.races if r.post_time), None
                ),
            },
        )

        count = 0
        event_queue: list[tuple[str, dict]] = []

        for parsed in card.races:
            previous = Race.objects.filter(
                race_day=race_day, race_number=parsed.race_number
            ).first()
            was_official = previous.status == Race.Status.OFFICIAL if previous else False
            prev_replay = previous.video_replay_url if previous else ""

            race, _ = Race.objects.update_or_create(
                race_day=race_day,
                race_number=parsed.race_number,
                defaults={
                    "race_name": parsed.race_name,
                    "race_type": parsed.race_type,
                    "distance": parsed.distance,
                    "distance_furlongs": parsed.distance_furlongs,
                    "surface": parsed.surface,
                    "purse": parsed.purse,
                    "post_time": parsed.post_time,
                    "status": parsed.status,
                    "conditions": parsed.conditions,
                    "video_replay_url": parsed.video_replay_url or (prev_replay or ""),
                    "raw_payload": parsed.raw,
                },
            )
            count += 1

            if parsed.runners:
                race.runners.all().delete()
                Runner.objects.bulk_create(
                    [
                        Runner(
                            race=race,
                            program_number=r.program_number,
                            horse_name=r.horse_name,
                            jockey=r.jockey,
                            trainer=r.trainer,
                            morning_line_odds=r.morning_line_odds,
                            weight=r.weight,
                            scratched=r.scratched,
                            post_position=r.post_position,
                        )
                        for r in parsed.runners
                        if r.program_number
                    ]
                )
                capture_morning_line_snapshots(race, source=card.source)

            became_official = False
            if parsed.finishers:
                result, _ = RaceResult.objects.update_or_create(
                    race=race,
                    defaults={
                        "winning_time": parsed.winning_time,
                        "official_at": timezone.now(),
                        "source": card.source,
                    },
                )
                result.finishers.all().delete()
                Finisher.objects.bulk_create(
                    [
                        Finisher(
                            result=result,
                            position=f.position,
                            program_number=f.program_number,
                            horse_name=f.horse_name,
                            jockey=f.jockey,
                            trainer=f.trainer,
                            win_payoff=f.win_payoff,
                            place_payoff=f.place_payoff,
                            show_payoff=f.show_payoff,
                        )
                        for f in parsed.finishers
                    ]
                )
                race.status = Race.Status.OFFICIAL
                race.save(update_fields=["status", "updated_at"])
                became_official = not was_official

            if parsed.payouts:
                for payout in parsed.payouts:
                    Payout.objects.update_or_create(
                        race=race,
                        bet_type=payout.bet_type,
                        combination=payout.combination,
                        defaults={
                            "amount": payout.amount,
                            "base_wager": payout.base_wager,
                        },
                    )

            # Replay enricher for official races missing a URL
            if race.status == Race.Status.OFFICIAL and not race.video_replay_url:
                guessed = self.equibase._guess_replay_url(
                    race.track_code, race.race_day.race_date, race.race_number
                )
                if guessed:
                    race.video_replay_url = guessed
                    race.save(update_fields=["video_replay_url", "updated_at"])

            if became_official:
                race.refresh_from_db()
                top = []
                if hasattr(race, "result"):
                    top = [
                        {
                            "position": f.position,
                            "program_number": f.program_number,
                            "horse_name": f.horse_name,
                        }
                        for f in race.result.finishers.all()[:3]
                    ]
                event_queue.append(
                    (
                        "race.official",
                        {
                            **_race_payload_base(race),
                            "top_three": top,
                            "dividends": _dividends_map(race),
                            "winning_time": getattr(race.result, "winning_time", ""),
                        },
                    )
                )

            if race.video_replay_url and race.video_replay_url != prev_replay:
                event_queue.append(
                    (
                        "replay.ready",
                        {
                            **_race_payload_base(race),
                            "video_replay_url": race.video_replay_url,
                        },
                    )
                )

        previous_next_id = (
            race_day.races.filter(status=Race.Status.NEXT)
            .values_list("id", flat=True)
            .first()
        )
        self._refresh_next_status(race_day)
        new_next = race_day.races.filter(status=Race.Status.NEXT).first()
        if new_next and new_next.id != previous_next_id:
            event_queue.append(("race.next", _race_payload_base(new_next)))

        # Emit after successful commit of this atomic block via on_commit
        for event_type, payload in event_queue:
            transaction.on_commit(lambda et=event_type, p=payload: emit(et, p))

        return count

    def _refresh_next_status(self, race_day: RaceDay) -> None:
        now = timezone.now()
        upcoming = (
            race_day.races.exclude(status=Race.Status.OFFICIAL)
            .exclude(status=Race.Status.CANCELLED)
            .order_by("post_time", "race_number")
        )
        Race.objects.filter(race_day=race_day, status=Race.Status.NEXT).update(
            status=Race.Status.SCHEDULED
        )
        next_race = None
        for race in upcoming:
            if race.post_time and race.post_time >= now:
                next_race = race
                break
        if not next_race and upcoming.exists():
            next_race = upcoming.first()
        if next_race:
            next_race.status = Race.Status.NEXT
            next_race.save(update_fields=["status", "updated_at"])

    def process_near_post_odds(self, track_codes: list[str] | None = None) -> int:
        """
        For races with MTP <= threshold, capture 5 MTP odds, upsert mtp5 picks,
        compute movements and emit events.
        """
        threshold = getattr(settings, "NEAR_POST_MTP_THRESHOLD", 15)
        codes = resolve_track_codes(track_codes)
        today = timezone.localdate()
        races = (
            Race.objects.filter(
                race_day__race_date=today,
                race_day__track__code__in=codes,
            )
            .exclude(status__in=[Race.Status.OFFICIAL, Race.Status.CANCELLED])
            .select_related("race_day__track")
            .prefetch_related("runners", "vip_picks", "odds_snapshots")
        )

        processed = 0
        for race in races:
            mtp = race.minutes_to_post
            if mtp is None or mtp > threshold or mtp < 0:
                continue
            # Capture when inside the 5 MTP window (or first time under threshold)
            if mtp > 5 and race.odds_snapshots.filter(mtp_minutes=5).exists():
                continue

            morning_pick = race.vip_picks.filter(
                pick_window=VipPick.PickWindow.MORNING
            ).first()
            selections = list(morning_pick.selections) if morning_pick else [
                r.program_number for r in race.runners.filter(scratched=False)[:4]
            ]

            odds_map: dict[str, str] = {}
            for runner in race.runners.filter(scratched=False):
                ml = runner.morning_line_odds or "5/1"
                # Prefer synthetic drift for demo/live-without-odds-feed
                odds_map[runner.program_number] = synthetic_mtp5_odds(ml)

            capture_mtp5_snapshots(race, odds_map, source=self.source or "live")

            mtp5_selections = selections[:]
            if mtp <= 5 and len(mtp5_selections) >= 4:
                # Simulate late money reshuffle on board order
                mtp5_selections = [
                    mtp5_selections[1],
                    mtp5_selections[0],
                    mtp5_selections[3],
                    mtp5_selections[2],
                ] + mtp5_selections[4:]

            pick, created = VipPick.objects.update_or_create(
                race=race,
                pick_window=VipPick.PickWindow.MTP5,
                defaults={
                    "selections": mtp5_selections,
                    "notes": "auto-5mtp",
                    "published_at": timezone.now(),
                },
            )
            # Keep legacy alias in sync
            VipPick.objects.update_or_create(
                race=race,
                pick_window=VipPick.PickWindow.LAST_HOUR,
                defaults={
                    "selections": mtp5_selections,
                    "notes": "auto-5mtp-alias",
                    "published_at": timezone.now(),
                },
            )

            movements = compute_odds_movements(race, selections)
            moved = [m for m in movements if m.direction != "unchanged"]

            base = _race_payload_base(race)
            if created or mtp <= 5:
                emit(
                    "picks.mtp5_published",
                    {**base, "selections": mtp5_selections},
                )
            if moved:
                emit(
                    "odds.moved",
                    {
                        **base,
                        "movements": [
                            {
                                "program_number": m.program_number,
                                "morning_odds": m.morning_odds,
                                "mtp5_odds": m.mtp5_odds,
                                "delta": float(m.delta) if m.delta is not None else None,
                                "direction": m.direction,
                            }
                            for m in moved
                        ],
                    },
                )
            processed += 1
        return processed

    def run_job(
        self,
        job_type: str,
        race_date: date,
        track_codes: list[str] | None = None,
        *,
        want_results: bool,
    ) -> ScrapeJob:
        codes = resolve_track_codes(track_codes)
        job = ScrapeJob.objects.create(
            job_type=job_type,
            source=self.source,
            target_date=race_date,
            track_codes=codes,
            status=ScrapeJob.Status.RUNNING,
        )
        total = 0
        errors: list[str] = []

        for code in codes:
            try:
                card = self.fetch_card(code, race_date, want_results=want_results)
                if not card.races:
                    logger.info("No races for %s on %s", code, race_date)
                    continue
                total += self.upsert_card(card)
            except Exception as exc:  # noqa: BLE001
                logger.exception("Failed scrape %s %s", code, race_date)
                errors.append(f"{code}: {exc}")

        job.races_upserted = total
        job.finished_at = timezone.now()
        if errors and total:
            job.status = ScrapeJob.Status.PARTIAL
            job.error_message = "\n".join(errors)
        elif errors:
            job.status = ScrapeJob.Status.FAILED
            job.error_message = "\n".join(errors)
        else:
            job.status = ScrapeJob.Status.SUCCESS
        job.save()
        return job

    def scrape_entries(
        self, race_date: date | None = None, track_codes: list[str] | None = None
    ) -> ScrapeJob:
        target = race_date or timezone.localdate()
        return self.run_job(
            ScrapeJob.JobType.ENTRIES,
            target,
            track_codes,
            want_results=False,
        )

    def scrape_results(
        self, race_date: date | None = None, track_codes: list[str] | None = None
    ) -> ScrapeJob:
        target = race_date or timezone.localdate()
        return self.run_job(
            ScrapeJob.JobType.RESULTS,
            target,
            track_codes,
            want_results=True,
        )

    def scrape_live(self, track_codes: list[str] | None = None) -> list[ScrapeJob]:
        today = timezone.localdate()
        jobs = [
            self.run_job(
                ScrapeJob.JobType.LIVE,
                today,
                track_codes,
                want_results=True,
            )
        ]
        jobs.append(
            self.run_job(
                ScrapeJob.JobType.LIVE,
                today - timedelta(days=1),
                track_codes,
                want_results=True,
            )
        )
        return jobs

    def scrape_near_post(self, track_codes: list[str] | None = None) -> ScrapeJob:
        codes = resolve_track_codes(track_codes)
        job = ScrapeJob.objects.create(
            job_type=ScrapeJob.JobType.NEAR_POST,
            source=self.source,
            target_date=timezone.localdate(),
            track_codes=codes,
            status=ScrapeJob.Status.RUNNING,
        )
        try:
            # Refresh live card first, then odds window
            self.scrape_live(track_codes=codes)
            processed = self.process_near_post_odds(track_codes=codes)
            job.races_upserted = processed
            job.status = ScrapeJob.Status.SUCCESS
        except Exception as exc:  # noqa: BLE001
            logger.exception("near-post scrape failed")
            job.status = ScrapeJob.Status.FAILED
            job.error_message = str(exc)
        job.finished_at = timezone.now()
        job.save()
        return job
