from datetime import date

from django.core.management.base import BaseCommand
from django.utils import timezone

from scraper.services import ScrapeService


class Command(BaseCommand):
    help = "Scrape official results, finishers and mutuel payouts."

    def add_arguments(self, parser):
        parser.add_argument("--date", type=str, help="YYYY-MM-DD (default: today ET)")
        parser.add_argument(
            "--tracks",
            type=str,
            help="Comma-separated track codes, e.g. GP,CD,SAR",
        )
        parser.add_argument(
            "--source",
            type=str,
            help="Override SCRAPER_SOURCE (single or chain: equibase,racing_api,demo)",
        )

    def handle(self, *args, **options):
        race_date = (
            date.fromisoformat(options["date"])
            if options.get("date")
            else timezone.localdate()
        )
        tracks = (
            [t.strip().upper() for t in options["tracks"].split(",") if t.strip()]
            if options.get("tracks")
            else None
        )
        service = ScrapeService(source=options.get("source"))
        job = service.scrape_results(race_date=race_date, track_codes=tracks)
        self.stdout.write(
            self.style.SUCCESS(
                f"[{job.status}] results {race_date}: {job.races_upserted} races "
                f"(source={job.source})"
            )
        )
        if job.error_message:
            self.stderr.write(job.error_message)
