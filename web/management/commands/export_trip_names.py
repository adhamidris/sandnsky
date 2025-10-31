from pathlib import Path

from django.core.management.base import BaseCommand

from web.models import Trip


class Command(BaseCommand):
    help = "Export all trip titles to a plain-text file."

    def add_arguments(self, parser):
        parser.add_argument(
            "--output",
            default="trip_names.txt",
            help="Destination path for the generated text file (default: trip_names.txt).",
        )

    def handle(self, *args, **options):
        output_path = Path(options["output"]).expanduser().resolve()
        output_path.parent.mkdir(parents=True, exist_ok=True)

        trips = Trip.objects.order_by("title").only("title")
        lines = [f"Trip object [{trip.title}]" for trip in trips]

        output_path.write_text("\n".join(lines) + ("\n" if lines else ""), encoding="utf-8")

        self.stdout.write(
            self.style.SUCCESS(f"Wrote {len(lines)} trip name(s) to {output_path}")
        )
