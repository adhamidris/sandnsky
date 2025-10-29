# your_app/management/commands/seed_destination_images.py
from pathlib import Path
from django.core.files import File
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.conf import settings
from django.utils.text import slugify

from web.models import Destination, DestinationName

# Map folder names under media/mains → DestinationName values
FOLDER_TO_DESTINATION = {
    "siwa": DestinationName.SIWA,
    "fayoum": DestinationName.FAYOUM,
    "black-desert": DestinationName.WHITE_BLACK,        # folder: "black desert"
    "farafra": DestinationName.FARAFRA,
    "dakhla": DestinationName.DAKHLA,
    "kharga": DestinationName.KHARGA,
    "wahat-bahareya": DestinationName.BAHAREYA,         # folder: "wahat bahareya"
    "giza": DestinationName.GIZA,
    "cairo": DestinationName.CAIRO,
    "alexandria": DestinationName.ALEXANDRIA,
    "ain-sokhna": DestinationName.AIN_EL_SOKHNA,        # folder: "ain-sokhna"
    "sinai": DestinationName.SINAI,
    "luxor": DestinationName.LUXOR,
    "aswan": DestinationName.ASWAN,
}

SUPPORTED_EXTS = {".jpg", ".jpeg", ".png", ".webp"}


def find_one(globbed):
    """Return the first existing path from a list (or None)."""
    for p in globbed:
        if p.exists() and p.is_file():
            return p
    return None


def normalize_key(name: str) -> str:
    # Turns "Wahat Bahareya" → "wahat-bahareya", "black desert" → "black-desert"
    return slugify(name)


class Command(BaseCommand):
    help = "Seed Destination.card_image and Destination.hero_image from media/mains/*/*-card.* and *-hero.*"

    def add_arguments(self, parser):
        parser.add_argument(
            "--root",
            default="media/mains",
            help="Root directory (relative to project root) containing destination folders. Default: media/mains",
        )
        parser.add_argument(
            "--overwrite",
            action="store_true",
            help="Replace existing images if already set.",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Scan and show what would change without writing files.",
        )

    @transaction.atomic
    def handle(self, *args, **opts):
        project_root = Path(settings.BASE_DIR)
        root_dir = (project_root / opts["root"]).resolve()
        overwrite = opts["overwrite"]
        dry_run = opts["dry_run"]

        if not root_dir.exists():
            raise CommandError(f"Root dir not found: {root_dir}")

        self.stdout.write(self.style.MIGRATE_HEADING(f"Scanning {root_dir}"))
        total_seen = total_updated = 0

        for sub in sorted(p for p in root_dir.iterdir() if p.is_dir()):
            key = normalize_key(sub.name)  # folder name normalized
            if key not in FOLDER_TO_DESTINATION:
                self.stdout.write(self.style.WARNING(f"Skip folder '{sub.name}' (no mapping)"))
                continue

            dest_name = FOLDER_TO_DESTINATION[key]
            try:
                dest = Destination.objects.get(name=dest_name.value)
            except Destination.DoesNotExist:
                self.stdout.write(self.style.WARNING(
                    f"Destination record missing for '{dest_name.value}'. Creating…"
                ))
                dest = Destination.objects.create(name=dest_name.value)

            # Find card / hero images in this folder
            card_path = find_one([*sub.glob("*-card.*")])
            hero_path = find_one([*sub.glob("*-hero.*")])

            # Guard extensions
            if card_path and card_path.suffix.lower() not in SUPPORTED_EXTS:
                self.stdout.write(self.style.WARNING(f"Unsupported ext for card: {card_path.name}; skipping card."))
                card_path = None
            if hero_path and hero_path.suffix.lower() not in SUPPORTED_EXTS:
                self.stdout.write(self.style.WARNING(f"Unsupported ext for hero: {hero_path.name}; skipping hero."))
                hero_path = None

            total_seen += 1
            changed = False

            # Assign card image
            if card_path:
                if overwrite or not dest.card_image:
                    filename = f"{dest.slug or slugify(dest.name)}-card{card_path.suffix.lower()}"
                    if dry_run:
                        self.stdout.write(f"[dry-run] {dest.name}: set card_image ← {card_path}")
                    else:
                        with card_path.open("rb") as fh:
                            # ImageField.upload_to handles placing under 'destinations/'
                            dest.card_image.save(filename, File(fh), save=False)
                    changed = True
                else:
                    self.stdout.write(f"{dest.name}: card_image exists (use --overwrite to replace)")
            else:
                self.stdout.write(self.style.WARNING(f"{dest.name}: no *-card.* in '{sub.name}'"))

            # Assign hero image
            if hero_path:
                if overwrite or not dest.hero_image:
                    filename = f"{dest.slug or slugify(dest.name)}-hero{hero_path.suffix.lower()}"
                    if dry_run:
                        self.stdout.write(f"[dry-run] {dest.name}: set hero_image ← {hero_path}")
                    else:
                        with hero_path.open("rb") as fh:
                            # ImageField.upload_to handles placing under 'destinations/hero/'
                            dest.hero_image.save(filename, File(fh), save=False)
                    changed = True
                else:
                    self.stdout.write(f"{dest.name}: hero_image exists (use --overwrite to replace)")
            else:
                self.stdout.write(self.style.WARNING(f"{dest.name}: no *-hero.* in '{sub.name}'"))

            if changed and not dry_run:
                # Ensure slug exists before filename generation next time
                if not dest.slug:
                    dest.slug = slugify(dest.name)
                dest.save()
                total_updated += 1

        self.stdout.write(self.style.SUCCESS(f"Done. Folders scanned: {total_seen}. Destinations updated: {total_updated}."))
