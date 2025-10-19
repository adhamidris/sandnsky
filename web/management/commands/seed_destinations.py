from django.core.management.base import BaseCommand
from django.db import transaction
from web.models import Destination, DestinationName


DESCRIPTIONS = {
    DestinationName.SIWA: (
        "Quiet desert oasis with salt lakes and palm groves. "
        "Highlights: Shali Fortress, Cleopatra Spring, Great Sand Sea."
    ),
    DestinationName.WHITE_BLACK: (
        "Striking white rock formations and black basalt hills. "
        "Highlights: Aqabat Valley, Crystal Mountain, Black Desert."
    ),
    DestinationName.FARAFRA: (
        "Relaxed oasis near the White Desert with hot springs and local art. "
        "Highlights: Badr Museum, Bir Sitta hot spring, White Desert."
    ),
    DestinationName.DAKHLA: (
        "Historic villages, wide dunes, and date farms. "
        "Highlights: Al-Qasr old town, Deir el-Hagar temple, Mut hot springs."
    ),
    DestinationName.KHARGA: (
        "Open sands with major ancient sites. "
        "Highlights: Temple of Hibis, Bagawat Necropolis, Qasr Dush."
    ),
    # NOTE: Fayoum intentionally omitted per your instruction.
}

# Order matters for featured positions:
ORDER = [
    DestinationName.SIWA,
    DestinationName.WHITE_BLACK,
    DestinationName.FARAFRA,
    DestinationName.DAKHLA,
    DestinationName.KHARGA,
]


class Command(BaseCommand):
    help = "Seed/update Destination descriptions and featured ordering (starting at 2)."

    def add_arguments(self, parser):
        parser.add_argument(
            "--start-pos",
            type=int,
            default=2,
            help="Starting featured position (default: 2)",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Print changes without saving to DB",
        )

    @transaction.atomic
    def handle(self, *args, **opts):
        start_pos = opts["start_pos"]
        dry_run = opts["dry_run"]

        self.stdout.write(self.style.MIGRATE_HEADING(
            f"Seeding destinations (start_pos={start_pos}, dry_run={dry_run})"
        ))

        for idx, dest_name in enumerate(ORDER, start=start_pos):
            desc = DESCRIPTIONS.get(dest_name, "").strip()
            if not desc:
                self.stdout.write(self.style.WARNING(f"Skipping {dest_name}: no description provided"))
                continue

            # Use the predefined choice value (no free text).
            defaults = {
                "description": desc,
                "is_featured": True,
                "featured_position": idx,
                # Leave 'tagline' and 'card_image' untouched.
            }

            try:
                obj, created = Destination.objects.get_or_create(name=dest_name)
                before = {
                    "description": obj.description,
                    "is_featured": obj.is_featured,
                    "featured_position": obj.featured_position,
                }

                # Apply updates
                obj.description = desc
                obj.is_featured = True
                obj.featured_position = idx

                if dry_run:
                    action = "CREATE" if created else "UPDATE"
                    self.stdout.write(f"{action} {dest_name}: {before} -> {defaults}")
                else:
                    obj.save()
                    self.stdout.write(self.style.SUCCESS(
                        f"{'Created' if created else 'Updated'} {dest_name} "
                        f"(featured_position={idx})"
                    ))

            except Exception as e:
                self.stderr.write(self.style.ERROR(f"Error processing {dest_name}: {e}"))
                if not dry_run:
                    raise

        if dry_run:
            self.stdout.write(self.style.WARNING("Dry-run complete. No changes were saved."))
        else:
            self.stdout.write(self.style.SUCCESS("Seeding complete."))
