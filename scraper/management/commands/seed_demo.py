from datetime import date, timedelta

from django.core.management.base import BaseCommand
from django.utils import timezone

from scraper.demo_data import seed_vip_picks_for_track
from scraper.services import ScrapeService, ensure_tracks


class Command(BaseCommand):
    help = "Seed demo tracks/cards/VIP picks so the JSON API works offline."

    def add_arguments(self, parser):
        parser.add_argument(
            "--tracks",
            type=str,
            default="GP,CD,SAR",
            help="Comma-separated track codes (default: GP,CD,SAR)",
        )
        parser.add_argument(
            "--days",
            type=int,
            default=1,
            help="How many days from today to seed (default: 1)",
        )

    def handle(self, *args, **options):
        ensure_tracks()
        tracks = [t.strip().upper() for t in options["tracks"].split(",") if t.strip()]
        days = max(1, options["days"])
        service = ScrapeService(source="demo")
        today = timezone.localdate()

        total_races = 0
        total_picks = 0
        for offset in range(days):
            day: date = today + timedelta(days=offset)
            job = service.scrape_results(race_date=day, track_codes=tracks)
            total_races += job.races_upserted
            for code in tracks:
                total_picks += seed_vip_picks_for_track(code, day)

        self.stdout.write(
            self.style.SUCCESS(
                f"Demo seed complete: {total_races} races, {total_picks} VIP pick rows"
            )
        )
