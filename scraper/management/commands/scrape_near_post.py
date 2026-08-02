from django.core.management.base import BaseCommand

from scraper.services import ScrapeService


class Command(BaseCommand):
    help = "Near-post scrape: refresh cards and capture 5 MTP odds / VIP picks."

    def add_arguments(self, parser):
        parser.add_argument(
            "--tracks",
            type=str,
            help="Comma-separated track codes, e.g. GP,CD,SAR",
        )
        parser.add_argument(
            "--source",
            type=str,
            help="Override SCRAPER_SOURCE (single or chain)",
        )

    def handle(self, *args, **options):
        tracks = (
            [t.strip().upper() for t in options["tracks"].split(",") if t.strip()]
            if options.get("tracks")
            else None
        )
        service = ScrapeService(source=options.get("source"))
        job = service.scrape_near_post(track_codes=tracks)
        self.stdout.write(
            self.style.SUCCESS(
                f"[{job.status}] near-post: {job.races_upserted} races processed"
            )
        )
        if job.error_message:
            self.stderr.write(job.error_message)
