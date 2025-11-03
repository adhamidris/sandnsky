from django.core.management.base import BaseCommand
from django.db import transaction

from web.models import TripCategory


class Command(BaseCommand):
    help = "Remove the 'luxury' category tag from every trip currently using it."

    def handle(self, *args, **options):
        try:
            luxury_category = TripCategory.objects.get(slug="luxury")
        except TripCategory.DoesNotExist:
            self.stdout.write(
                self.style.WARNING("TripCategory with slug 'luxury' does not exist.")
            )
            return

        tagged_count = luxury_category.trips.count()
        if tagged_count == 0:
            self.stdout.write("No trips are currently tagged as 'luxury'.")
            return

        with transaction.atomic():
            luxury_category.trips.clear()

        self.stdout.write(
            self.style.SUCCESS(
                f"Removed 'luxury' tag from {tagged_count} trip"
                f"{'' if tagged_count == 1 else 's'}."
            )
        )
