# your_app/management/commands/wipe_media.py
from __future__ import annotations

import os
from typing import Iterable, Tuple, Set
from django.core.management.base import BaseCommand
from django.db import transaction
from django.apps import apps

# Import your concrete models (explicit is safer than reflection for destructive ops)
from web.models import (
    Destination,
    DestinationGalleryImage,
    BlogCategory,   # no files, but included for clarity
    BlogPost,
    BlogSection,
    SiteConfiguration,
    SiteHeroPair,
    Trip,
    TripHighlight,  # no files
    TripAbout,      # no files
    TripItineraryDay,  # no files
    TripItineraryStep, # no files
    TripInclusion,     # no files
    TripExclusion,     # no files
    TripFAQ,           # no files
    TripExtra,         # no files
)

# (model, list of file field names)
FILE_FIELDS: Tuple[Tuple[object, Tuple[str, ...]], ...] = (
    (Destination, ("card_image", "hero_image",)),
    (DestinationGalleryImage, ("image",)),
    (BlogPost, ("hero_image", "card_image")),
    (BlogSection, ("section_image",)),
    (SiteConfiguration, ("hero_image", "hero_video", "trips_hero_image", "gallery_background_image")),
    (SiteHeroPair, ("hero_image", "hero_video", "overlay_image")),
    (Trip, ("card_image", "hero_image")),
    # Add any future models w/ FileField here.
)

def iter_all_file_paths() -> Set[str]:
    """
    Return a set of all file *name* values referenced by DB FileFields (the storage key, not absolute path).
    This is used to detect 'unreferenced' files.
    """
    referenced: Set[str] = set()
    for Model, fields in FILE_FIELDS:
        for obj in Model.objects.all().only(*fields):
            for fname in fields:
                f = getattr(obj, fname, None)
                if f and getattr(f, "name", ""):
                    referenced.add(f.name)
    return referenced

def collect_storage_roots() -> Set[Tuple[object, str]]:
    """
    Collect unique (storage, base_location) pairs seen across our FileFields.
    For S3/R2, base_location is the storage.location/prefix; for local, it's MEDIA_ROOT-relative location.
    """
    storages: Set[Tuple[object, str]] = set()
    for Model, fields in FILE_FIELDS:
        # Use a dummy instance to access the FieldFile.storage
        inst = Model()
        for fname in fields:
            field = getattr(Model, fname).field  # FileField
            storage = field.storage
            location = getattr(storage, "location", "") or getattr(storage, "base_location", "") or ""
            storages.add((storage, location))
    return storages


class Command(BaseCommand):
    help = (
        "Delete uploaded media and/or clear references.\n"
        "By default deletes all file blobs referenced by DB and clears fields; "
        "use --only-unreferenced to only delete files that are not referenced by DB.\n"
        "Safe with local MEDIA_ROOT and remote storages (S3/R2) via django-storages."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Show what would be deleted/cleared without changing anything.",
        )
        parser.add_argument(
            "--only-unreferenced",
            action="store_true",
            help="Only delete blobs not referenced by any DB FileField. Does not clear fields.",
        )
        parser.add_argument(
            "--confirm",
            action="store_true",
            help="Required to actually perform deletions (prevents accidents).",
        )

    @transaction.atomic
    def handle(self, *args, **opts):
        dry = opts["dry_run"]
        only_unref = opts["only_unreferenced"]
        confirm = opts["confirm"]

        if dry:
            self.stdout.write(self.style.WARNING("Running in --dry-run mode"))
        if not dry and not confirm:
            self.stderr.write(self.style.ERROR("Refusing to proceed without --confirm. Re-run with --confirm (and optionally --dry-run first)."))
            return

        if only_unref:
            self._delete_unreferenced(dry)
        else:
            self._wipe_all_referenced_and_clear_fields(dry)

        if dry:
            self.stdout.write(self.style.WARNING("Dry-run complete. No changes were made."))
        else:
            self.stdout.write(self.style.SUCCESS("Done."))

    # ---------- Modes ----------

    def _wipe_all_referenced_and_clear_fields(self, dry: bool):
        """
        Deletes every file currently referenced by our FileFields and clears those fields in DB.
        Also deletes DestinationGalleryImage rows (files removed) to keep DB clean.
        """
        total_deleted = 0
        total_cleared = 0
        # 1) Delete gallery rows (will delete their files via field.delete())
        for gi in DestinationGalleryImage.objects.all():
            if dry:
                if gi.image and gi.image.name:
                    self.stdout.write(f"[dry-run] delete file & row: {gi.image.name}  (DestinationGalleryImage id={gi.id})")
            else:
                if gi.image and gi.image.name:
                    gi.image.delete(save=False)
                gi.delete()
            total_deleted += 1

        # 2) For the rest, delete files and clear fields
        for Model, fields in FILE_FIELDS:
            if Model is DestinationGalleryImage:
                continue  # already handled
            qs = Model.objects.all().only(*fields)
            for obj in qs:
                modified = False
                for fname in fields:
                    f = getattr(obj, fname, None)
                    if f and getattr(f, "name", ""):
                        name = f.name
                        if dry:
                            self.stdout.write(f"[dry-run] delete file: {name}  ({Model.__name__} id={obj.pk}, field={fname})")
                        else:
                            # Delete blob from storage
                            f.delete(save=False)
                        # Clear pointer in DB
                        setattr(obj, fname, "")
                        modified = True
                        total_deleted += 1
                if modified:
                    if dry:
                        self.stdout.write(f"[dry-run] clear fields on {Model.__name__} id={obj.pk}")
                    else:
                        obj.save(update_fields=list(fields))
                        total_cleared += 1

        self.stdout.write(self.style.MIGRATE_HEADING(f"Referenced files deleted: {total_deleted}, Objects updated: {total_cleared}"))

    def _delete_unreferenced(self, dry: bool):
        """
        Deletes blobs present in storage trees but not referenced by DB file fields.
        Works best on local file storage; on S3/R2 it relies on storage.listdir recursion.
        """
        referenced = iter_all_file_paths()
        self.stdout.write(self.style.MIGRATE_HEADING(f"Referenced (kept) files: {len(referenced)}"))

        deleted = 0
        storages = collect_storage_roots()

        for storage, base in storages:
            # Recursively list files for this storage
            # On FileSystemStorage, listdir returns (dirs, files) for a given path.
            # We'll walk breadth-first without assuming OS paths.
            stack = [""]
            while stack:
                prefix = stack.pop()
                try:
                    dirs, files = storage.listdir(prefix)
                except Exception as e:
                    self.stdout.write(self.style.WARNING(f"Could not listdir('{prefix}') on {storage.__class__.__name__}: {e}"))
                    continue

                for d in dirs:
                    stack.append(os.path.join(prefix, d))

                for name in files:
                    key = os.path.join(prefix, name) if prefix else name
                    # Skip collectstatic outputs (just in case storage points there)
                    if key.startswith("static/"):
                        continue
                    if key in referenced:
                        continue
                    if dry:
                        self.stdout.write(f"[dry-run] delete unreferenced: {key}")
                    else:
                        try:
                            storage.delete(key)
                        except Exception as e:
                            self.stdout.write(self.style.WARNING(f"Failed deleting {key}: {e}"))
                            continue
                    deleted += 1

        self.stdout.write(self.style.MIGRATE_HEADING(f"Unreferenced files deleted: {deleted}"))
