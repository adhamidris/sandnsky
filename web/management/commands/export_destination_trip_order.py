from pathlib import Path
from typing import List

from django.core.management.base import BaseCommand
from django.db.models import Prefetch

from web.models import Destination, Trip


class Command(BaseCommand):
    help = (
        "Export destinations with their trips, primary/additional relations, "
        "and per-destination ordering into a human-readable text file."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--output",
            default="destination_trip_order.txt",
            help="Destination path for the generated text file (default: destination_trip_order.txt).",
        )

    def handle(self, *args, **options):
        output_path = Path(options["output"]).expanduser().resolve()
        output_path.parent.mkdir(parents=True, exist_ok=True)

        destinations = (
            Destination.objects.order_by("name")
            .prefetch_related(
                Prefetch(
                    "trips",
                    queryset=Trip.objects.select_related("destination")
                    .prefetch_related("additional_destinations")
                ),
                Prefetch(
                    "additional_trips",
                    queryset=Trip.objects.select_related("destination")
                    .prefetch_related("additional_destinations"),
                ),
            )
        )

        sections: List[str] = []
        for destination in destinations:
            sections.append(f"Destination: {destination.name} (slug: {destination.slug})")

            primary_trips = sorted(
                destination.trips.all(),
                key=lambda trip: (
                    trip.destination_order is None,
                    trip.destination_order or 0,
                    trip.title.lower(),
                ),
            )
            additional_trips = sorted(
                destination.additional_trips.all(),
                key=lambda trip: (trip.destination.name.lower(), trip.title.lower()),
            )

            if primary_trips:
                sections.append("  Primary trips:")
                for trip in primary_trips:
                    sections.extend(self._trip_lines(trip, indent="    "))
            else:
                sections.append("  Primary trips: none")

            if additional_trips:
                sections.append("  Appears as additional destination in:")
                for trip in additional_trips:
                    sections.extend(self._trip_lines(trip, indent="    "))
            else:
                sections.append("  Appears as additional destination in: none")

            sections.append("")  # blank line between destinations

        content = "\n".join(sections).rstrip() + "\n"
        output_path.write_text(content, encoding="utf-8")

        self.stdout.write(
            self.style.SUCCESS(
                f"Wrote destination/trip ordering report with {len(destinations)} destination(s) to {output_path}"
            )
        )

    def _trip_lines(self, trip: Trip, indent: str) -> List[str]:
        additional_names = sorted(
            {destination.name for destination in trip.additional_destinations.all()}
        )
        additional_display = ", ".join(additional_names) if additional_names else "None"
        order_display = trip.destination_order if trip.destination_order is not None else "None"

        lines = [
            f"{indent}- {trip.title} (slug: {trip.slug})",
            f"{indent}  Primary destination: {trip.destination.name}",
            f"{indent}  Destination order: {order_display}",
            f"{indent}  Additional destinations: {additional_display}",
        ]
        return lines
