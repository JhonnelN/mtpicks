"""
Seed Colonial Downs race matching the BetAmerica CONSEJOS + odds board example.

Green tips (first of each → morning Our Picks = 5,1,5,6):
  SELECCIONES     5-3-4
  VELOCIDAD MAX   1-2-5
  PRIMERA CLASE   5-2-6
  RITMO MAXIMO    6-3-7

Red favorites board (O column):
  #5 5/2 · #4 2 · #3 3 · #2 9/2
"""

from datetime import timedelta
from decimal import Decimal
from zoneinfo import ZoneInfo

from django.conf import settings
from django.core.management.base import BaseCommand
from django.utils import timezone

from racing.models import (
    OddsSnapshot,
    Race,
    RaceDay,
    RaceTipSheet,
    Runner,
    Track,
    VipPick,
)
from racing.odds import compute_odds_movements, parse_odds_to_decimal
from scraper.services import ensure_tracks


class Command(BaseCommand):
    help = "Seed Colonial Downs (CNL) BetAmerica-style tips + favorites board."

    def handle(self, *args, **options):
        ensure_tracks()
        track, _ = Track.objects.update_or_create(
            code="CNL",
            defaults={
                "name": "Colonial Downs",
                "state": "VA",
                "country": "USA",
                "timezone": "America/New_York",
                "is_active": True,
            },
        )
        tz = ZoneInfo(settings.TIME_ZONE)
        today = timezone.localdate()
        post_time = timezone.now().astimezone(tz) + timedelta(minutes=8)

        race_day, _ = RaceDay.objects.update_or_create(
            track=track,
            race_date=today,
            defaults={
                "first_post_time": post_time,
                "source": "betamerica_demo",
                "scraped_at": timezone.now(),
            },
        )

        race, _ = Race.objects.update_or_create(
            race_day=race_day,
            race_number=1,
            defaults={
                "race_name": "Colonial Downs Race 1",
                "race_type": "MCL",
                "distance": "5 1/2F T",
                "distance_furlongs": Decimal("5.5"),
                "surface": Race.Surface.TURF,
                "purse": Decimal("40000"),
                "post_time": post_time,
                "status": Race.Status.NEXT,
                "conditions": "$16,000 MCL | $40,000 | 3yo+ F&M | 5 1/2F Turf Firm",
            },
        )

        # Runners with board odds from the screenshot (O column)
        board_odds = {
            "1": "8/1",
            "2": "9/2",
            "3": "3",
            "4": "2",
            "5": "5/2",
            "6": "6/1",
            "7": "10/1",
            "8": "12/1",
        }
        race.runners.all().delete()
        Runner.objects.bulk_create(
            [
                Runner(
                    race=race,
                    program_number=num,
                    horse_name=f"CNL Horse {num}",
                    jockey=f"Jockey {num}",
                    trainer=f"Trainer {num}",
                    morning_line_odds=odds,
                    post_position=int(num),
                )
                for num, odds in board_odds.items()
            ]
        )

        # Tip sheet = green CONSEJOS boxes
        tip_sheet, _ = RaceTipSheet.objects.update_or_create(
            race=race,
            defaults={
                "selections": ["5", "3", "4"],
                "max_speed": ["1", "2", "5"],
                "first_class": ["5", "2", "6"],
                "max_pace": ["6", "3", "7"],
                "source": "betamerica",
                "published_at": timezone.now(),
            },
        )
        morning = tip_sheet.morning_tops()  # ["5","1","5","6"]

        VipPick.objects.update_or_create(
            race=race,
            pick_window=VipPick.PickWindow.MORNING,
            defaults={"selections": morning, "notes": "betamerica-tips-tops"},
        )
        VipPick.objects.update_or_create(
            race=race,
            pick_window=VipPick.PickWindow.MTP5,
            defaults={
                "selections": ["5", "4", "3", "2"],
                "notes": "betamerica-favorites-order",
            },
        )
        VipPick.objects.update_or_create(
            race=race,
            pick_window=VipPick.PickWindow.LAST_HOUR,
            defaults={
                "selections": ["5", "4", "3", "2"],
                "notes": "betamerica-favorites-alias",
            },
        )

        # Morning + live (5 MTP) odds snapshots for favorites / movement
        race.odds_snapshots.all().delete()
        for num, odds in board_odds.items():
            OddsSnapshot.objects.create(
                race=race,
                program_number=num,
                odds=odds,
                odds_decimal=parse_odds_to_decimal(odds),
                mtp_minutes=None,
                source="betamerica",
            )
            # Slight shorten for live board (same display values from screenshot)
            OddsSnapshot.objects.create(
                race=race,
                program_number=num,
                odds=odds,
                odds_decimal=parse_odds_to_decimal(odds),
                mtp_minutes=5,
                source="betamerica",
            )

        # Movement on tip tops + board favorites
        compute_odds_movements(race, ["5", "1", "5", "6", "4", "3", "2"])

        self.stdout.write(
            self.style.SUCCESS(
                f"CNL seeded. morning(Our Picks)={morning} "
                f"tips={tip_sheet.as_tips_payload()} "
                f"GET /api/our-picks/?track=CNL"
            )
        )
