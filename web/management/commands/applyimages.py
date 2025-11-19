from __future__ import annotations

import json
from pathlib import Path

from django.core.management.base import BaseCommand, CommandError
from web.models import Trip, TripGalleryImage


class Command(BaseCommand):
    help = (
        "Apply novtrip_images.json (exported from local) to this database: "
        "wires card/hero/gallery image names without re-uploading files."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--manifest",
            default="novtrip_images.json",
            help="Path to the manifest JSON file exported from local.",
        )

    def handle(self, *args, **options):
        manifest_path = Path(options["manifest"])

        if not manifest_path.exists():
            raise CommandError(f"Manifest file not found: {manifest_path}")

        data = json.loads(manifest_path.read_text())

        updated_trips = 0
        skipped_missing = 0

        for title, payload in data.items():
            trip = Trip.objects.filter(title=title).first()
            if not trip:
                self.stdout.write(
                    self.style.WARNING(
                        f"Trip not found on this DB, skipping: {title}"
                    )
                )
                skipped_missing += 1
                continue

            card_image_name = payload.get("card_image") or ""
            hero_image_name = payload.get("hero_image") or ""
            gallery_items = payload.get("gallery") or []

            changed_fields: list[str] = []

            # Only set if empty on this DB, so it's safe/idempotent.
            if card_image_name and not trip.card_image.name:
                trip.card_image.name = card_image_name
                changed_fields.append("card_image")

            if hero_image_name and not trip.hero_image.name:
                trip.hero_image.name = hero_image_name
                changed_fields.append("hero_image")

            if changed_fields:
                trip.save(update_fields=changed_fields)

            # Only create gallery if there isn't one already.
            created_gallery = False
            if gallery_items and not trip.gallery_images.exists():
                for item in gallery_items:
                    img_name = item.get("image")
                    if not img_name:
                        continue

                    g = TripGalleryImage(
                        trip=trip,
                        caption=item.get("caption", ""),
                        position=item.get("position") or 0,
                        image_width=item.get("image_width"),
                        image_height=item.get("image_height"),
                    )
                    # Crucial: set the ImageField's .name directly (no upload).
                    g.image.name = img_name
                    g.save()
                created_gallery = True

            if changed_fields or created_gallery:
                updated_trips += 1
                self.stdout.write(
                    self.style.SUCCESS(f"Updated images for: {title}")
                )
            else:
                self.stdout.write(
                    f"No image changes needed for: {title}"
                )

        self.stdout.write(
            self.style.SUCCESS(
                f"Done. Updated {updated_trips} trips. "
                f"Skipped (not found on this DB): {skipped_missing}."
            )
        )
