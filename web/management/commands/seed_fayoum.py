from django.core.management.base import BaseCommand
from django.db import transaction
from web.models import Destination, DestinationName

# ---- Content & media ----

DEST_LABEL = "Fayoum"  # display label/captions

DESCRIPTION = (
    "A breathtaking escape where golden dunes meet shimmering lakes. Discover "
    "Wadi El Rayan’s waterfalls, the tranquil Magic Lake, and Wadi El-Hitan "
    "(Valley of the Whales)."
)

HERO_SUBTITLE = (
    "Fayoum is an easy escape from Cairo—an oasis of lakes, dunes, and quiet villages. "
    "Spend time by Lake Qarun, see the Wadi El-Rayan Waterfalls and shimmering Magic Lake, "
    "then head to Wadi El-Hitan (Valley of the Whales) for a UNESCO-listed fossil trail. "
    "Birdlife, desert picnics, and soft sunsets set the pace, while Tunis Village adds pottery "
    "studios and slow travel charm. Short drives connect highlights, making Fayoum ideal for "
    "nature, light adventure, and a reset from city life."
)

# store paths relative to your MEDIA_ROOT (assign via .name)
CARD_IMAGE_PATH = "destinations/3d235ad7c0.jpg"
HERO_IMAGE_PATH = "destinations/hero/4217eec125.jpg"

# (image_path, position, caption)
GALLERY_ITEMS = [
    ("destinations/gallery/3d235ad7c0_WcUNzvj.jpg", 1, DEST_LABEL),
    ("destinations/gallery/12b69d0cbc_Rdteky0.jpg", 2, DEST_LABEL),
    ("destinations/gallery/4217eec125_OUmw5BV.jpg", 3, DEST_LABEL),
    ("destinations/gallery/2017149ceb_d7j7uTD.jpg", 4, DEST_LABEL),
    ("destinations/gallery/c03430637b_s0zvzLL.jpg", 5, DEST_LABEL),
]

FEATURED = True
FEATURED_POSITION = 0  # as requested


class Command(BaseCommand):
    help = "Seed/Update Fayoum destination, hero content, media, and gallery."

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Print the changes without saving to the DB",
        )
        parser.add_argument(
            "--overwrite-images",
            action="store_true",
            help="Replace existing card/hero/gallery images if already set",
        )

    def _resolve_enum(self):
        # Expect DestinationName.FAYOUM (fallbacks if you used an alt spelling)
        for candidate in ("FAYOUM", "FAYUM", "AL_FAYYOUM", "AL_FAYOUM"):
            val = getattr(DestinationName, candidate, None)
            if val is not None:
                return val
        return None

    @transaction.atomic
    def handle(self, *args, **opts):
        dry_run = opts["dry_run"]
        overwrite_images = opts["overwrite_images"]

        dest_enum = self._resolve_enum()
        if dest_enum is None:
            self.stderr.write(
                self.style.ERROR(
                    "DestinationName enum has no FAYOUM/FAYUM/AL_FAYYOUM/AL_FAYOUM member. "
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

        # Textual fields
        obj.description = DESCRIPTION
        obj.is_featured = FEATURED
        obj.featured_position = FEATURED_POSITION

        # Optional tagline: left untouched unless you want to seed it
        # obj.tagline = "…"  # uncomment and set if needed

        # Hero subtitle (if field exists)
        if hasattr(obj, "hero_subtitle"):
            obj.hero_subtitle = HERO_SUBTITLE

        # Images: assign path by setting .name (works with FileField/ImageField)
        if hasattr(obj, "card_image"):
            if overwrite_images or not getattr(obj.card_image, "name", ""):
                obj.card_image.name = CARD_IMAGE_PATH

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

        # --- Gallery seeding ---
        GalleryModel = None
        try:
            from web.models import DestinationGalleryImage
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

                    has_image = bool(getattr(gi.image, "name", ""))
                    if overwrite_images or not has_image:
                        if not dry_run:
                            gi.image.name = img_path
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
                            f"({gi.image.name}); skip (use --overwrite-images to replace)."
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
            self.stdout.write(self.style.SUCCESS("Fayoum seeding complete."))
