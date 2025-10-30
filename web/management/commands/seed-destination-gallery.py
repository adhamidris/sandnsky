# your_app/management/commands/seed_destination_gallery.py
from __future__ import annotations

import os
from pathlib import Path
from typing import Dict, List

from django.core.files import File
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils.text import slugify

from web.models import Destination, DestinationName, DestinationGalleryImage  # <-- adjust app path


IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".webp", ".gif"}  # extend if needed
JUNK_NAMES = {".ds_store", "thumbs.db", "desktop.ini"}

# Map directory names under base-dir -> DestinationName.value
# (keys are compared case-insensitively; spaces/dashes tolerated)
FOLDER_TO_DEST: Dict[str, str] = {
    "siwa": DestinationName.SIWA.value,
    "fayoum": DestinationName.FAYOUM.value,
    "white-desert": DestinationName.WHITE_BLACK.value,
    "black-desert": DestinationName.WHITE_BLACK.value,
    "farafra": DestinationName.FARAFRA.value,     # present for future
    "dakhla": DestinationName.DAKHLA.value,       # present for future
    "kharga": DestinationName.KHARGA.value,       # present for future
    "bahareya": DestinationName.BAHAREYA.value,
    "bahariya": DestinationName.BAHAREYA.value,   # common alt spelling
    "bahareya oasis": DestinationName.BAHAREYA.value,
    "giza": DestinationName.GIZA.value,
    "cairo": DestinationName.CAIRO.value,
    "alexandria": DestinationName.ALEXANDRIA.value,
    "ain el sokhna": DestinationName.AIN_EL_SOKHNA.value,
    "ain-sokhna": DestinationName.AIN_EL_SOKHNA.value,
    "sokhna": DestinationName.AIN_EL_SOKHNA.value,
    "sinai": DestinationName.SINAI.value,
    "saint catherine": DestinationName.SINAI.value,
    "luxor": DestinationName.LUXOR.value,
    "aswan": DestinationName.ASWAN.value,
}

def normalize_key(name: str) -> str:
    # make matching forgiving: lowercase, collapse dashes/underscores, strip
    return name.strip().lower().replace("_", " ").replace("-", " ")

def is_image(path: Path) -> bool:
    return path.suffix.lower() in IMAGE_EXTS and path.name.lower() not in JUNK_NAMES

def humanize_caption(filename: str) -> str:
    base = Path(filename).stem
    # simple cleanup for nicer default captions
    base = base.replace("_", " ").replace("-", " ")
    base = " ".join(base.split())
    return base.title()[:200]


class Command(BaseCommand):
    help = "Seed DestinationGalleryImage from a folder tree (uploads via configured storage)."

    def add_arguments(self, parser):
        parser.add_argument(
            "--base-dir",
            default="media/tripz",
            help="Base directory to scan (default: media/tripz)",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Print actions without creating/updating anything.",
        )
        parser.add_argument(
            "--wipe",
            action="store_true",
            help="Delete existing gallery items for destinations that will be seeded.",
        )
        parser.add_argument(
            "--caption-from-name",
            action="store_true",
            help="Auto-fill caption from filename (default: blank captions).",
        )

    def handle(self, *args, **opts):
        base_dir = Path(opts["base_dir"]).resolve()
        dry_run = opts["dry_run"]
        wipe = opts["wipe"]
        caption_from_name = opts["caption_from_name"]

        if not base_dir.exists() or not base_dir.is_dir():
            raise CommandError(f"Base dir not found or not a directory: {base_dir}")

        # Gather first-level subfolders under base_dir as buckets
        buckets = [p for p in sorted(base_dir.iterdir()) if p.is_dir()]
        if not buckets:
            self.stdout.write(self.style.WARNING(f"No subfolders found in {base_dir}"))
            return

        # Resolve folder names -> Destination objects
        dest_map: Dict[Path, Destination] = {}
        missing: List[str] = []

        for bucket in buckets:
            key = normalize_key(bucket.name)
            # try direct match
            dest_name_value = FOLDER_TO_DEST.get(key)
            if not dest_name_value:
                # try a slugified key to be extra forgiving
                dest_name_value = FOLDER_TO_DEST.get(normalize_key(slugify(bucket.name)))
            if not dest_name_value:
                missing.append(bucket.name)
                continue
            try:
                dest_obj = Destination.objects.get(name=dest_name_value)
                dest_map[bucket] = dest_obj
            except Destination.DoesNotExist:
                self.stdout.write(self.style.ERROR(
                    f"Destination row missing in DB for folder '{bucket.name}' → '{dest_name_value}'."
                ))

        if missing:
            self.stdout.write(self.style.WARNING(
                "Unmapped folders (skipped): " + ", ".join(missing)
            ))

        # Report plan
        self.stdout.write(self.style.MIGRATE_HEADING("Planned seeding:"))
        for folder, dest in dest_map.items():
            count = sum(1 for _ in folder.rglob("*") if is_image(_))
            self.stdout.write(f"  {folder.name} → {dest.name} ({count} images)")

        if dry_run:
            self.stdout.write(self.style.NOTICE("Dry-run: no changes will be made."))

        # Start transaction to keep things tidy (esp. when wiping)
        with transaction.atomic():
            affected_dests = list({d.pk for d in dest_map.values()})

            if wipe and affected_dests:
                qs = DestinationGalleryImage.objects.filter(destination_id__in=affected_dests)
                n = qs.count()
                if dry_run:
                    self.stdout.write(self.style.WARNING(f"[dry-run] Would delete {n} existing gallery items for affected destinations"))
                else:
                    deleted = qs.delete()
                    self.stdout.write(self.style.WARNING(f"Deleted existing gallery items: {n}"))

            created_total = 0

            for folder, dest in dest_map.items():
                # Determine next position offset for this destination
                existing_max = (
                    DestinationGalleryImage.objects
                    .filter(destination=dest)
                    .order_by("-position")
                    .values_list("position", flat=True)
                    .first()
                )
                position = (existing_max or 0) + 1

                # Recurse images under this folder (includes nested subfolders)
                for img_path in sorted(folder.rglob("*")):
                    if not img_path.is_file() or not is_image(img_path):
                        continue

                    # Avoid obvious duplicates by filename if already present under this destination
                    filename = img_path.name
                    already = DestinationGalleryImage.objects.filter(
                        destination=dest,
                        image__iendswith=f"/{filename}"
                    ).exists()

                    if already:
                        self.stdout.write(self.style.NOTICE(
                            f"Skip (duplicate name): {dest.name} · {filename}"
                        ))
                        continue

                    # Build path inside upload_to: destinations/gallery/<slug>/<filename>
                    storage_rel_path = f"{dest.slug}/{filename}"

                    if dry_run:
                        self.stdout.write(f"[dry-run] + {dest.name} · pos={position} · {img_path}")
                        position += 1
                        continue

                    with open(img_path, "rb") as fh:
                        dg = DestinationGalleryImage(
                            destination=dest,
                            position=position,
                            caption=(humanize_caption(filename) if caption_from_name else ""),
                        )
                        # Save without auto-save to control filename path under upload_to base
                        dg.image.save(storage_rel_path, File(fh), save=False)
                        dg.save()

                    created_total += 1
                    position += 1
                    self.stdout.write(self.style.SUCCESS(
                        f"+ {dest.name} · pos={position-1} · {filename}"
                    ))

            if dry_run:
                self.stdout.write(self.style.MIGRATE_HEADING(f"[dry-run] Done. Created=0"))
            else:
                self.stdout.write(self.style.MIGRATE_HEADING(f"Done. Created={created_total}"))
