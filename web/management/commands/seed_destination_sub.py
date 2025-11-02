from django.core.management.base import BaseCommand
from django.db import transaction
from web.models import Destination, DestinationName  # adjust import path if needed

SUBTITLES = {
    DestinationName.SIWA.value: (
        "Golden dunes, salt lakes and starry nights.\n"
        "An oasis of Amazigh culture and quiet."
    ),
    DestinationName.FAYOUM.value: (
        "Desert meets water at Wadi El Rayan.\n"
        "Lakes, waterfalls, and gentle palm villages."
    ),
    DestinationName.WHITE_BLACK.value: (
        "Alien chalk sculptures and ebony dunes.\n"
        "Camp under a sky bright with constellations."
    ),
    DestinationName.FARAFRA.value: (
        "Slow oasis life and white desert gateways.\n"
        "Hot springs, palms, and wide open silence."
    ),
    DestinationName.DAKHLA.value: (
        "Ancient villages and fertile fields in sand seas.\n"
        "Mud-brick lanes, date groves, desert horizons."
    ),
    DestinationName.KHARGA.value: (
        "Temples on old caravan routes of the Sahara.\n"
        "Wide valleys, palm oases, and warm springs."
    ),
    DestinationName.BAHAREYA.value: (
        "Gateway to the Black & White Desert.\n"
        "Golden dunes, crystal hills, oasis charm."
    ),
    DestinationName.GIZA.value: (
        "The Great Pyramids and the timeless Sphinx.\n"
        "Sunsets over stone and desert edges."
    ),
    DestinationName.CAIRO.value: (
        "Fast, layered, alive — Egypt’s heartbeat.\n"
        "Museums, markets, Nile views."
    ),
    DestinationName.ALEXANDRIA.value: (
        "Sea breeze, libraries, and Mediterranean light.\n"
        "Corniche cafés and Greco-Roman whispers."
    ),
    DestinationName.AIN_EL_SOKHNA.value: (
        "Closest Red Sea escape from Cairo.\n"
        "Clear water, soft beaches, year-round sun."
    ),
    DestinationName.SINAI.value: (
        "Red Sea reefs and rugged granite mountains.\n"
        "Bedouin nights, starry camps, sunrise hikes."
    ),
    DestinationName.LUXOR.value: (
        "The world’s greatest open-air museum.\n"
        "Nile sunsets, temples, West Bank tombs."
    ),
    DestinationName.ASWAN.value: (
        "Granite islands and Nubian colors.\n"
        "Calm Nile, feluccas, warm winter sun."
    ),
}

class Command(BaseCommand):
    help = "Seed human-sounding 2–3 line hero_subtitles for Destinations."

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Show what would change without saving."
        )
        parser.add_argument(
            "--reset",
            action="store_true",
            help="Overwrite existing hero_subtitle values."
        )
        parser.add_argument(
            "--only",
            type=str,
            help="Comma-separated list of destination names to limit (e.g. 'Cairo,Giza,Luxor')."
        )

    def handle(self, *args, **options):
        dry_run = options["dry_run"]
        reset = options["reset"]
        only = options.get("only")

        targets = set(n.strip() for n in only.split(",")) if only else None

        # Validate 'only' values early
        if targets:
            unknown = [t for t in targets if t not in SUBTITLES]
            if unknown:
                self.stdout.write(self.style.WARNING(
                    f"Unknown destinations in --only: {', '.join(unknown)}"
                ))
                # continue but they just won't match anything

        planned = []
        skipped = []
        missing = []

        # Work through all mapped subtitles; we don't create Destination rows here.
        for name, subtitle in SUBTITLES.items():
            if targets and name not in targets:
                continue

            try:
                dest = Destination.objects.get(name=name)
            except Destination.DoesNotExist:
                missing.append(name)
                continue

            if dest.hero_subtitle and not reset:
                skipped.append((name, "exists"))
                continue

            planned.append((dest, subtitle))

        if not planned and not missing:
            self.stdout.write(self.style.SUCCESS("Nothing to do."))
            return

        if missing:
            self.stdout.write(self.style.WARNING(
                "Missing Destination rows (not created): " + ", ".join(missing)
            ))

        if skipped:
            self.stdout.write(self.style.WARNING(
                f"Skipped (already had hero_subtitle; use --reset to overwrite): "
                + ", ".join(n for n, _ in skipped)
            ))

        self.stdout.write(self.style.NOTICE("Planned updates:"))
        for dest, _ in planned:
            self.stdout.write(f" - {dest.name}")

        if dry_run:
            self.stdout.write(self.style.SUCCESS("Dry-run complete. No changes made."))
            return

        with transaction.atomic():
            for dest, subtitle in planned:
                dest.hero_subtitle = subtitle
                dest.save(update_fields=["hero_subtitle"])

        self.stdout.write(self.style.SUCCESS(
            f"Updated {len(planned)} destination subtitle(s)."
        ))
