from django.core.management.base import BaseCommand

from scraper.services import ScrapeService


class Command(BaseCommand):
    help = "Live refresh: today (+ yesterday) results and NEXT race status."

    def add_arguments(self, parser):
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
        tracks = (
            [t.strip().upper() for t in options["tracks"].split(",") if t.strip()]
            if options.get("tracks")
            else None
        )
        service = ScrapeService(source=options.get("source"))
        jobs = service.scrape_live(track_codes=tracks)
        for job in jobs:
            self.stdout.write(
                self.style.SUCCESS(
                    f"[{job.status}] live {job.target_date}: {job.races_upserted} races"
                )
            )
            if job.error_message:
                self.stderr.write(job.error_message)
