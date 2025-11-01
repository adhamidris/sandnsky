from __future__ import annotations

from typing import Tuple, Type

from django.core.management.base import BaseCommand, CommandError
from django.db.models import Model

from PIL import Image, ImageFile, UnidentifiedImageError

from web.models import DestinationGalleryImage, TripGalleryImage


ImageFile.LOAD_TRUNCATED_IMAGES = True


class Command(BaseCommand):
    help = "Populate cached width/height fields for gallery images to avoid runtime file reads."

    def add_arguments(self, parser):
        parser.add_argument(
            "--model",
            action="append",
            choices=["destination", "trip"],
            help="Limit to specific gallery models (can repeat). Default: both.",
        )
        parser.add_argument(
            "--force",
            action="store_true",
            help="Recompute dimensions even when values are already set.",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Report what would change without writing to the database.",
        )

    def handle(self, *args, **options):
        requested = options.get("model") or ["destination", "trip"]
        force = options.get("force", False)
        dry_run = options.get("dry_run", False)

        model_map: dict[str, Type[Model]] = {
            "destination": DestinationGalleryImage,
            "trip": TripGalleryImage,
        }

        unknown = [value for value in requested if value not in model_map]
        if unknown:
            raise CommandError(f"Unrecognized model labels: {', '.join(sorted(unknown))}")

        model_choices: list[str] = []
        seen: set[str] = set()
        for value in requested:
            if value in seen:
                continue
            seen.add(value)
            model_choices.append(value)

        total_processed = total_updated = total_skipped = 0

        for label in model_choices:
            model = model_map[label]
            queryset = model.objects.all().order_by("pk")
            self.stdout.write(self.style.HTTP_INFO(f"Processing {model._meta.label} ({queryset.count()} rows)"))

            for obj in queryset.iterator():
                total_processed += 1
                field = getattr(obj, "image", None)
                if not field or not getattr(field, "name", ""):
                    total_skipped += 1
                    continue

                current_dims = (getattr(obj, "image_width", None), getattr(obj, "image_height", None))
                if not force and all(current_dims):
                    total_skipped += 1
                    continue

                try:
                    width, height = _determine_dimensions(field)
                except (OSError, UnidentifiedImageError) as exc:  # pragma: no cover - defensive
                    total_skipped += 1
                    self.stdout.write(self.style.WARNING(f"  [skip] {field.name} ({exc})"))
                    continue

                if not width or not height:
                    total_skipped += 1
                    self.stdout.write(self.style.WARNING(f"  [skip] {field.name} (unable to determine size)"))
                    continue

                if dry_run:
                    total_updated += 1
                    self.stdout.write(self.style.NOTICE(f"  [dry-run] {field.name}: {width}×{height}"))
                    continue

                model.objects.filter(pk=obj.pk).update(image_width=width, image_height=height)
                total_updated += 1
                self.stdout.write(self.style.SUCCESS(f"  Updated {field.name}: {width}×{height}"))

        summary = (
            f"Done. processed={total_processed} updated={total_updated} skipped={total_skipped} "
            f"dry_run={'yes' if dry_run else 'no'}"
        )
        self.stdout.write(self.style.SUCCESS(summary))


def _determine_dimensions(field_file) -> Tuple[int | None, int | None]:
    """
    Return (width, height) for the given FieldFile without leaving file handles open.
    """
    storage = field_file.storage
    name = field_file.name
    with storage.open(name, "rb") as fh:
        with Image.open(fh) as image:
            width, height = image.size
    return int(width), int(height)
