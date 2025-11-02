from dataclasses import dataclass
from typing import Iterable, List

from django.core.management.base import BaseCommand
from django.db import transaction
from django.db.models import Prefetch

from web.models import Destination, Trip


@dataclass
class ReorderResult:
    destination: Destination
    primary_count: int
    secondary_count: int
    updated_trips: List[Trip]


class Command(BaseCommand):
    help = (
        "Normalize trip ordering per destination so that primary trips appear first, "
        "followed by trips where the destination is listed as an additional stop."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--destination",
            help="Restrict ordering to a single destination by slug.",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Show the changes without saving them.",
        )

    def handle(self, *args, **options):
        destination_slug = options.get("destination")
        dry_run = options.get("dry_run", False)

        destinations = self._destination_queryset(destination_slug)
        if destination_slug and not destinations:
            self.stderr.write(self.style.ERROR(f"No destination found for slug '{destination_slug}'"))
            return

        results: List[ReorderResult] = []

        with transaction.atomic():
            for destination in destinations:
                result = self._reorder_for_destination(destination, dry_run=dry_run)
                results.append(result)

            if dry_run:
                transaction.set_rollback(True)

        total_updated = sum(len(result.updated_trips) for result in results)
        for result in results:
            self.stdout.write(
                f"{result.destination.name}: {result.primary_count} primary, "
                f"{result.secondary_count} secondary; "
                f"{len(result.updated_trips)} trip(s) would be updated."
                if dry_run
                else
                f"{result.destination.name}: reordered {result.primary_count} primary and "
                f"{result.secondary_count} secondary trip(s); "
                f"{len(result.updated_trips)} updated."
            )

        summary_template = (
            "Dry run complete. {count} trip(s) would be updated."
            if dry_run
            else "Ordering complete. {count} trip(s) updated."
        )
        self.stdout.write(self.style.SUCCESS(summary_template.format(count=total_updated)))

    def _destination_queryset(self, destination_slug: str | None) -> Iterable[Destination]:
        queryset = Destination.objects.order_by("name")
        if destination_slug:
            queryset = queryset.filter(slug=destination_slug)
        return queryset.prefetch_related(
            Prefetch(
                "trips",
                queryset=Trip.objects.select_related("destination").prefetch_related("additional_destinations"),
            ),
            Prefetch(
                "additional_trips",
                queryset=Trip.objects.select_related("destination").prefetch_related("additional_destinations"),
            ),
        )

    def _reorder_for_destination(self, destination: Destination, dry_run: bool) -> ReorderResult:
        primary_trips = list(destination.trips.all())
        secondary_trips = [
            trip for trip in destination.additional_trips.all() if trip.destination_id != destination.id
        ]

        primary_sorted = self._sorted_trips(primary_trips, prioritize_existing=True)
        secondary_sorted = self._sorted_trips(secondary_trips, prioritize_existing=True)

        updated: List[Trip] = []

        order = 1
        for trip in primary_sorted:
            if trip.destination_order != order:
                trip.destination_order = order
                updated.append(trip)
            order += 1
        if updated and not dry_run:
            Trip.objects.bulk_update(updated, ["destination_order"])

        return ReorderResult(
            destination=destination,
            primary_count=len(primary_sorted),
            secondary_count=len(secondary_sorted),
            updated_trips=updated,
        )

    def _sorted_trips(self, trips: Iterable[Trip], prioritize_existing: bool) -> List[Trip]:
        if prioritize_existing:
            return sorted(
                trips,
                key=lambda trip: (
                    trip.destination_order is None,
                    trip.destination_order or 0,
                    trip.title.lower(),
                    trip.pk,
                ),
            )
        return sorted(trips, key=lambda trip: (trip.title.lower(), trip.pk))
