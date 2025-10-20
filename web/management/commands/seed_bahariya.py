from django.core.management.base import BaseCommand
from django.db import transaction
from web.models import Destination, DestinationName

# ---- Content & media ----

DEST_LABEL = "Bahareya Oasis"  # display label/captions
DESCRIPTION = (
    "A desert escape known for palm groves, golden dunes, and natural springs. "
    "Highlights: Black Desert, Crystal Mountain, English Mountain, Bawiti village, "
    "and nearby White Desert tours."
)

HERO_SUBTITLE = (
    "Bahariya offers an easy desert escape from Cairo with palm groves, warm springs, "
    "and a relaxed pace. It’s a practical base for exploring nearby highlights like the "
    "Black Desert’s volcanic hills, Crystal Mountain’s quartz ridge, and the dunes around "
    "Aqabat Valley. Many visitors pair Bahariya with camping in the White Desert, where "
    "chalk formations light up at sunrise and sunset. In town, simple lodges, local meals, "
    "and friendly guides make logistics straightforward. If you want a classic Western "
    "Desert experience without long transfers, Bahariya is a smart starting point."
)

# store paths relative to your MEDIA_ROOT (works fine by assigning .name)
CARD_IMAGE_PATH = "destinations/5926689bcd.jpg"
HERO_IMAGE_PATH = "destinations/hero/16057f7033.jpg"

# (image_path, position, caption)
GALLERY_ITEMS = [
    ("destinations/gallery/38c7bf4755.jpg", 1, f"{DEST_LABEL}"),
    ("destinations/gallery/8857f34b6c.jpg", 2, f"{DEST_LABEL}"),
    ("destinations/gallery/16057f7033.jpg", 3, f"{DEST_LABEL}"),
    ("destinations/gallery/5926689bcd.jpg", 4, f"{DEST_LABEL}"),
]

FEATURED = True
FEATURED_POSITION = 1  # as requested


class Command(BaseCommand):
    help = "Seed/Update Bahariya/Bahareya Oasis destination, hero content, media, and gallery."

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Print the changes without saving to the DB",
        )
        parser.add_argument(
            "--overwrite-images",
            action="store_true",
            help="Replace existing card/hero images if already set",
        )

    def _resolve_enum(self):
        # Accept either spelling in your enum: BAHAREYA or BAHARIYA
        target = getattr(DestinationName, "BAHAREYA", None)
        if target is None:
            target = getattr(DestinationName, "BAHARIYA", None)
        return target

    @transaction.atomic
    def handle(self, *args, **opts):
        dry_run = opts["dry_run"]
        overwrite_images = opts["overwrite_images"]

        dest_enum = self._resolve_enum()
        if dest_enum is None:
            self.stderr.write(
                self.style.ERROR(
                    "DestinationName enum has no BAHAREYA/BAHARIYA member. "
                    "Please add it to DestinationName before running this command."
                )
            )
            return

        self.stdout.write(self.style.MIGRATE_HEADING(
            f"Seeding {DEST_LABEL} (dry_run={dry_run}, overwrite_images={overwrite_images})"
        ))

        # --- Upsert Destination ---
        try:
            obj, created = Destination.objects.get_or_create(name=dest_enum)
        except Exception as e:
            self.stderr.write(self.style.ERROR(f"Failed to get_or_create Destination: {e}"))
            if not dry_run:
                raise
            return

        before = {
            "description": getattr(obj, "description", None),
            "is_featured": getattr(obj, "is_featured", None),
            "featured_position": getattr(obj, "featured_position", None),
            "tagline": getattr(obj, "tagline", None),
            "card_image": getattr(obj, "card_image", None).name if getattr(obj, "card_image", None) else None,
            "hero_image": getattr(obj, "hero_image", None).name if getattr(obj, "hero_image", None) else None,
            "hero_subtitle": getattr(obj, "hero_subtitle", None),
        }

        # Apply textual fields
        obj.description = DESCRIPTION
        obj.is_featured = FEATURED
        obj.featured_position = FEATURED_POSITION

        # Optional: keep tagline untouched unless you want to seed it explicitly:
        # obj.tagline = "HistoryView on site"  # (left blank by your brief; uncomment if needed)

        # Hero content (set if the model has the fields)
        if hasattr(obj, "hero_subtitle"):
            obj.hero_subtitle = HERO_SUBTITLE

        # Card image (assign path name if empty or overwrite requested)
        if hasattr(obj, "card_image"):
            if overwrite_images or not getattr(obj.card_image, "name", ""):
                obj.card_image.name = CARD_IMAGE_PATH

        # Hero image
        if hasattr(obj, "hero_image"):
            if overwrite_images or not getattr(obj.hero_image, "name", ""):
                obj.hero_image.name = HERO_IMAGE_PATH

        if dry_run:
            action = "CREATE" if not before["description"] and created else "UPDATE"
            self.stdout.write(self.style.WARNING(f"{action} Destination preview:"))
            self.stdout.write(f"  before={before}")
            self.stdout.write(
                "  after="
                f"{{'description': '{DESCRIPTION[:60]}...', 'is_featured': {FEATURED}, "
                f"'featured_position': {FEATURED_POSITION}, "
                f"'card_image': '{CARD_IMAGE_PATH}', 'hero_image': '{HERO_IMAGE_PATH}', "
                f"'hero_subtitle': '{HERO_SUBTITLE[:60]}...'}}"
            )
        else:
            obj.save()
            self.stdout.write(self.style.SUCCESS(
                f"{'Created' if created else 'Updated'} {DEST_LABEL} "
                f"(featured_position={FEATURED_POSITION})"
            ))

        # --- Gallery seeding (DestinationGalleryImage) ---
        # Only attempt if model exists and relation named as expected
        GalleryModel = None
        try:
            from web.models import DestinationGalleryImage  # your migrations show this model exists
            GalleryModel = DestinationGalleryImage
        except Exception:
            self.stdout.write(self.style.WARNING(
                "DestinationGalleryImage model not found; skipping gallery seeding."
            ))

        if GalleryModel:
            for img_path, position, caption in GALLERY_ITEMS:
                try:
                    gi, gi_created = GalleryModel.objects.get_or_create(
                        destination=obj,
                        position=position,
                        defaults={"caption": caption},
                    )
                    before_img = gi.image.name if getattr(gi, "image", None) else None

                    # Assign image path if missing or if overwriting is requested
                    if overwrite_images or not getattr(gi.image, "name", ""):
                        if not dry_run:
                            gi.image.name = img_path
                            # keep/update caption
                            if caption and hasattr(gi, "caption"):
                                gi.caption = caption
                            gi.save()

                        self.stdout.write(self.style.SUCCESS(
                            f"{'Created' if gi_created else 'Updated'} gallery item "
                            f"(pos={position}) -> {img_path}"
                        ))
                    else:
                        self.stdout.write(
                            f"Gallery item pos={position} already has image "
                            f"({before_img}); skip (use --overwrite-images to replace)."
                        )
                except Exception as e:
                    self.stderr.write(self.style.ERROR(
                        f"Error seeding gallery pos={position}: {e}"
                    ))
                    if not dry_run:
                        raise

        if dry_run:
            self.stdout.write(self.style.WARNING("Dry-run complete. No changes were saved."))
        else:
            self.stdout.write(self.style.SUCCESS("Bahariya/Bahareya seeding complete."))
