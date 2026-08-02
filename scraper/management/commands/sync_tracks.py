from django.core.management.base import BaseCommand

from scraper.services import ensure_tracks


class Command(BaseCommand):
    help = "Upsert the major US/Canada thoroughbred track catalog."

    def handle(self, *args, **options):
        created = ensure_tracks()
        self.stdout.write(self.style.SUCCESS(f"Tracks synced. Newly created: {created}"))
