from django.core.management.base import BaseCommand
from django.db import transaction

from web.models import Trip, get_package_trip_category


class Command(BaseCommand):
    help = (
        "Recalculate which trips qualify as 'Package Trip' based on destination combinations "
        "and update their category tags accordingly."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Show what would change without modifying the database.",
        )

    def handle(self, *args, dry_run=False, **options):
        category = get_package_trip_category()
        trip_qs = (
            Trip.objects.select_related("destination")
            .prefetch_related("additional_destinations", "category_tags")
            .order_by("title")
        )

        to_add = []
        to_remove = []
        for trip in trip_qs:
            should_tag = trip.total_destination_count() > 2
            is_tagged = any(cat.pk == category.pk for cat in trip.category_tags.all())
            if should_tag and not is_tagged:
                to_add.append(trip)
            elif not should_tag and is_tagged:
                to_remove.append(trip)

        if not to_add and not to_remove:
            self.stdout.write(self.style.SUCCESS("All trips are already in sync."))
            return

        if dry_run:
            if to_add:
                self.stdout.write("Would add 'Package Trip' tag to:")
                for trip in to_add:
                    self.stdout.write(f"  - {trip.title}")
            if to_remove:
                self.stdout.write("Would remove 'Package Trip' tag from:")
                for trip in to_remove:
                    self.stdout.write(f"  - {trip.title}")
            self.stdout.write(self.style.WARNING("Dry run complete; no changes applied."))
            return

        with transaction.atomic():
            for trip in to_add:
                trip.category_tags.add(category)
            for trip in to_remove:
                trip.category_tags.remove(category)

        self.stdout.write(
            self.style.SUCCESS(
                f"Updated package classification: added {len(to_add)}, removed {len(to_remove)}."
            )
        )
