"""
Attach hero, card image, and gallery images to existing Trip objects
by matching their *exact* DB titles to corresponding folders in
Cloudflare R2 (S3‑compatible) that were uploaded via `aws s3 sync`.

Folder layout in the bucket (keys):
  <PREFIX>/<Trip Folder>/
    ├── card and hero/
    │     ├── hero.<ext>
    │     └── card.<ext>
    └── trip gallery/
          ├── *.jpg|*.png|*.webp|*.avif|*.jpeg|*.heic
          └── ...

Usage examples:
  python manage.py seed_trip_media \
    --bucket sandnsky \
    --endpoint-url https://320d5978e214ca30814db520232615b1.r2.cloudflarestorage.com \
    --prefix trips-final/ \
    --replace-gallery

Notes:
- Credentials are read from standard AWS env vars (AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY).
- Works with django-storages S3Boto3 or any storage, because we assign ImageField.name
  directly to the object key (no upload). Make sure your live app can serve these keys
  (i.e., DEFAULT_FILE_STORAGE points to your R2 storage backend).
- Idempotent: by default, avoids re-adding gallery images that already exist for a Trip
  (compares by key). Use --replace-gallery to wipe & re-seed gallery.
- Safe by default: --dry-run prints what would change without saving. Omit to commit.

If your keys actually include a leading "media/" (e.g., media/trips-final/...), you can pass
--prefix media/trips-final/ OR keep --prefix trips-final/ and the command will auto-fallback
if it finds no folders under the first prefix.
"""

from __future__ import annotations

import os
import re
import sys
import itertools
from typing import Dict, List, Optional, Tuple

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils.text import slugify

try:
    import boto3
    from botocore.config import Config as BotoConfig
except Exception as e:  # pragma: no cover
    boto3 = None

from web.models import Trip, TripGalleryImage

# --- Exact Trip titles we intend to seed (from user's list) ---
TRIP_TITLES: List[str] = [
    "Alexandria Port to Giza: Pyramids & Grand Egyptian Museum (Shore Excursion)",
    "Alexandria to Cairo: Pyramids & Egyptian Museum Day Tour",
    "Alexandria to El Alamein: 2-Day City & WWII History (War Museum & Cemeteries)",
    "Aswan to Luxor: 4-Day Nile Cruise with Temples & Valley of Kings",
    "Cairo by Night: Free Walking Tour — Horse Carriage, Ice Cream & Cairo Tower Views",
    "Cairo to Ain Sokhna: Cable Car Experience & Red Sea Day Trip",
    "Cairo to Ain Sokhna: Luxury Yacht Day Trip on Red Sea",
    "Cairo to Alexandria: 2-Day Highlights (Pyramids, Museum & Coastal City) — Meals Included",
    "Cairo to Alexandria: 3-Day Highlights (Pyramids ATV, GEM & Nile Dinner Cruise)",
    "Cairo to Alexandria: 4-Day Egypt Highlights with Fayoum Oasis",
    "Cairo to Alexandria: Africano Park Safari Day Trip (Family-Friendly Wildlife Experience)",
    "Cairo to Alexandria: Full-Day Private City Highlights with Lunch",
    "Cairo to Bahariya Oasis: Overnight Desert Safari (Black Desert, Crystal Mountain & White Desert)",
    "Cairo to El Ain Sokhna: 3-Day City Tour & Beach Escape",
    "Cairo to El Ain Sokhna: Private Red Sea Beach Day Trip",
    "Cairo to El Alamein: War Museum & WWII Cemeteries Day Tour (Private)",
    "Cairo to El-Fayoum: 2-Day Pyramids & Oasis Tour",
    "Cairo to El-Minya: Full-Day Tour (Beni Hassan & Tell El-Amarna)",
    "Cairo to Fayoum: Oasis Safari & Valley of Whales Day Tour",
    "Cairo to Fayoum: Overnight Desert Camp (Wadi El Rayan & Magic Lake)",
    "Cairo to Giza, Saqqara & Memphis: Full-Day Pyramids Tour with Lunch",
    "Cairo to Giza: Dahshur, Saqqara & Memphis Pyramid Tour",
    "Cairo to Giza: Grand Egyptian Museum Day Tour",
    "Cairo to Giza: Museums Double — Grand Egyptian Museum & Egyptian Museum Day Tour",
    "Cairo to Giza: Pyramids & Grand Egyptian Museum (Full-Day Tour)",
    "Cairo to Giza: Pyramids & Sphinx (Half-Day Tour with Egyptologist)",
    "Cairo to Luxor: Day Trip by Flight (Karnak, Valley of the Kings & Hatshepsut)",
    "Cairo to Sinai: Mount Sunrise & St. Catherine Monastery Overnight Trip",
    "Cairo to Siwa Oasis: 3-Day Desert Escape — Oracle Temple, Salt Lakes & Great Sand Sea",
    "Cairo to Siwa: 4-Day Oasis Tour with Desert Safari & Salt Lakes",
    "Cairo to White Desert: 3-Day Bahariya Oasis & Desert Safari",
    "Cairo to White Desert: 5-Day City Tour & Desert Safari",
    "Cairo to White Desert: 7-Day Adventure (Bahariya Oasis, El-Fayoum & Pyramids)",
    "Cairo: 3-Day Guided City Tour with Pyramids & Museums",
    "Cairo: Felucca Nile Cruise — Traditional Sailboat Experience",
    "Cairo: Half-Day Old Cairo — Coptic Churches & Ben Ezra Synagogue",
    "Cairo: Khan El-Khalili Souk & Local Crafts — Guided Shopping Walk",
    "Cairo: Nile Maxim Luxury Dinner Cruise with Entertainment",
    "Cairo: Royal Palaces Day Tour - Abdeen, Baron & Manial Palace",
    "Giza Pyramids Desert: Quad Bike (ATV) Sunrise/Sunset Ride",
    "Giza to Cairo: Luxury Pyramids, Egyptian Museum & Khan el-Khalili (Private Day Tour)",
    "Giza: Pyramids & Sphinx with Camel Safari — Half-Day Adventure",
    "Giza: Pyramids Sound & Light Show Night Experience",
    "Giza: Pyramids Sound & Light Show with Dinner Experience",
    "Luxor to Aswan: 5-Day Nile Cruise with Temples & Valley of Kings",
    "Old Cairo Heritage: Coptic & Islamic Landmarks + Khan Al Khalili",
]

# Acceptable image extensions we'll consider
IMG_EXTS = {".jpg", ".jpeg", ".png", ".webp", ".avif", ".gif", ".heic"}

CARD_DIR = "card and hero/"
GALLERY_DIR = "trip gallery/"

NAME_RE = re.compile(r"[^a-z0-9]+")

def normalize(s: str) -> str:
    s = s.lower().strip()
    return NAME_RE.sub(" ", s).strip()

def tokens(s: str) -> set:
    return set(normalize(s).split())

from difflib import SequenceMatcher

def sim_score(a: str, b: str) -> float:
    # Combine Jaccard token similarity with sequence ratio
    ta, tb = tokens(a), tokens(b)
    if not ta or not tb:
        jaccard = 0.0
    else:
        inter = len(ta & tb)
        union = len(ta | tb)
        jaccard = inter / union if union else 0.0
    seq = SequenceMatcher(None, normalize(a), normalize(b)).ratio()
    return 0.6 * jaccard + 0.4 * seq

class Command(BaseCommand):
    help = "Seed Trip.hero_image, Trip.card_image, and TripGalleryImage from Cloudflare R2"

    def add_arguments(self, parser):
        parser.add_argument("--bucket", required=True)
        parser.add_argument("--endpoint-url", required=True)
        parser.add_argument("--prefix", default="trips-final/", help="Root prefix that contains per-trip folders (default: trips-final/)")
        parser.add_argument("--dry-run", action="store_true", help="Print actions without saving")
        parser.add_argument("--replace-gallery", action="store_true", help="Delete existing gallery images before re-seeding")
        parser.add_argument("--only-missing", action="store_true", help="Only set hero/card if currently empty")
        parser.add_argument("--trip", action="append", help="Limit to a specific Trip title (can repeat)")
        parser.add_argument("--threshold", type=float, default=0.55, help="Min similarity score to accept folder match (default: 0.55)")

    def s3(self, endpoint_url: str):
        if boto3 is None:
            raise CommandError("boto3 is required: pip install boto3")
        return boto3.client(
            "s3",
            endpoint_url=endpoint_url,
            region_name=os.environ.get("AWS_DEFAULT_REGION", "auto"),
            config=BotoConfig(s3={"addressing_style": "path"}),
        )

    def list_trip_folders(self, s3, bucket: str, prefix: str) -> List[str]:
        """Return a list of folder prefixes under prefix (each ends with '/')."""
        paginator = s3.get_paginator("list_objects_v2")
        folders: List[str] = []
        for page in paginator.paginate(Bucket=bucket, Prefix=prefix, Delimiter="/"):
            for cp in page.get("CommonPrefixes", []):
                folders.append(cp["Prefix"])  # e.g., 'trips-final/41- Old Cairo .../'
        return folders

    def pick_hero_card(self, s3, bucket: str, base_prefix: str) -> Tuple[Optional[str], Optional[str]]:
        """Return (hero_key, card_key) or (None, None) if not found."""
        hero_key = card_key = None
        prefix = base_prefix + CARD_DIR
        resp = s3.list_objects_v2(Bucket=bucket, Prefix=prefix)
        for obj in resp.get("Contents", []) or []:
            key = obj["Key"]
            ext = os.path.splitext(key)[1].lower()
            if ext not in IMG_EXTS:
                continue
            fn = os.path.basename(key).lower()
            if fn.startswith("hero"):
                hero_key = key
            elif fn.startswith("card"):
                card_key = key
        return hero_key, card_key

    def list_gallery(self, s3, bucket: str, base_prefix: str) -> List[str]:
        prefix = base_prefix + GALLERY_DIR
        keys: List[str] = []
        paginator = s3.get_paginator("list_objects_v2")
        for page in paginator.paginate(Bucket=bucket, Prefix=prefix):
            for obj in page.get("Contents", []) or []:
                k = obj["Key"]
                if k.endswith("/"):
                    continue
                ext = os.path.splitext(k)[1].lower()
                if ext in IMG_EXTS and not k.lower().endswith(".ds_store"):
                    keys.append(k)
        keys.sort()
        return keys

    def match_folder(self, trip_title: str, folder_prefixes: List[str]) -> Optional[str]:
        # Strip the leading prefix for matching and drop any numeric counter like '41- '
        best: Tuple[float, Optional[str]] = (0.0, None)
        for full in folder_prefixes:
            tail = full.rstrip("/")
            # remove top prefix path components, keep last folder name
            name = tail.split("/")[-1]
            # drop possible leading index "NN- "
            name_wo_idx = re.sub(r"^\d+\s*[-–—]\s*", "", name)
            score = sim_score(trip_title, name_wo_idx)
            if score > best[0]:
                best = (score, full)
        return best[1]

    @transaction.atomic
    def handle(self, *args, **opts):
        bucket = opts["bucket"]
        endpoint_url = opts["endpoint_url"]
        prefix = opts["prefix"]
        dry_run = opts["dry_run"]
        replace_gallery = opts["replace_gallery"]
        only_missing = opts["only_missing"]
        threshold = float(opts["threshold"]) or 0.55

        s3 = self.s3(endpoint_url)

        # Gather candidate folder prefixes; fallback if empty
        folders = self.list_trip_folders(s3, bucket, prefix)
        if not folders and prefix.startswith("trips-final/"):
            alt = "media/" + prefix
            self.stdout.write(self.style.WARNING(f"No folders under '{prefix}', trying '{alt}'..."))
            folders = self.list_trip_folders(s3, bucket, alt)
        if not folders:
            raise CommandError(f"No trip folders found under prefix '{prefix}'.")

        self.stdout.write(self.style.NOTICE(f"Found {len(folders)} trip folders under '{prefix}'."))

        # Filter target trips
        limit_titles = set(opts.get("trip") or [])
        exact_targets = TRIP_TITLES
        if limit_titles:
            exact_targets = [t for t in TRIP_TITLES if t in limit_titles]
            if not exact_targets:
                raise CommandError("--trip provided but none matched TRIP_TITLES constant.")

        # Load existing Trip objects present in DB
        trips_qs = Trip.objects.filter(title__in=exact_targets)
        trips_by_title: Dict[str, Trip] = {t.title: t for t in trips_qs}

        missing = set(exact_targets) - set(trips_by_title.keys())
        if missing:
            self.stdout.write(self.style.WARNING(
                f"{len(missing)} titles not found in DB (skipping):\n - " + "\n - ".join(sorted(missing))
            ))

        processed, skipped = 0, 0

        for title, trip in trips_by_title.items():
            match = self.match_folder(title, folders)
            if not match:
                skipped += 1
                self.stdout.write(self.style.WARNING(f"No folder matched for: {title}"))
                continue

            # Check similarity threshold by re-scoring the chosen folder
            folder_name = match.rstrip('/').split('/')[-1]
            folder_name_wo_idx = re.sub(r"^\d+\s*[-–—]\s*", "", folder_name)
            score = sim_score(title, folder_name_wo_idx)
            if score < threshold:
                skipped += 1
                self.stdout.write(self.style.WARNING(
                    f"Low match score {score:.2f} (<{threshold}) — skipping: {title} ↔ {folder_name}"
                ))
                continue

            hero_key, card_key = self.pick_hero_card(s3, bucket, match)
            gallery_keys = self.list_gallery(s3, bucket, match)

            if not hero_key and not card_key and not gallery_keys:
                skipped += 1
                self.stdout.write(self.style.WARNING(f"No media found in '{match}' for: {title}"))
                continue

            self.stdout.write(self.style.HTTP_INFO(
                f"\nTrip: {title}\n  Folder: {match}\n  Hero: {hero_key or '—'}\n  Card: {card_key or '—'}\n  Gallery: {len(gallery_keys)} images"
            ))

            # Apply changes
            changed_fields: List[str] = []

            if hero_key and (not only_missing or not trip.hero_image.name):
                trip.hero_image.name = hero_key
                changed_fields.append("hero_image")

            if card_key and (not only_missing or not trip.card_image.name):
                trip.card_image.name = card_key
                changed_fields.append("card_image")

            if changed_fields:
                if dry_run:
                    self.stdout.write(self.style.NOTICE(f"  WOULD SAVE fields: {', '.join(changed_fields)}"))
                else:
                    trip.save(update_fields=changed_fields)
                    self.stdout.write(self.style.SUCCESS(f"  Saved: {', '.join(changed_fields)}"))

            # Gallery seeding
            if gallery_keys:
                existing_keys = set(trip.gallery_images.values_list("image", flat=True))

                if replace_gallery and not dry_run:
                    trip.gallery_images.all().delete()
                    existing_keys = set()
                    self.stdout.write(self.style.WARNING("  Cleared existing gallery (replace-gallery)"))

                next_pos = (trip.gallery_images.aggregate_max("position") or 0) if hasattr(trip.gallery_images, 'aggregate_max') else None
                if next_pos is None:
                    # fallback: compute manually
                    try:
                        next_pos = (trip.gallery_images.order_by("-position").first().position or 0)
                    except Exception:
                        next_pos = 0

                adds = [k for k in gallery_keys if k not in existing_keys]
                if not adds:
                    self.stdout.write(self.style.NOTICE("  No new gallery images to add."))
                else:
                    if dry_run:
                        self.stdout.write(self.style.NOTICE(f"  WOULD ADD {len(adds)} gallery images."))
                    else:
                        for i, k in enumerate(adds, start=1):
                            TripGalleryImage.objects.create(
                                trip=trip,
                                image=k,  # assign key directly
                                caption=os.path.basename(k),
                                position=next_pos + i,
                            )
                        self.stdout.write(self.style.SUCCESS(f"  Added {len(adds)} gallery images."))

            processed += 1

        self.stdout.write(self.style.SUCCESS(f"\nDone. Processed {processed} trips, skipped {skipped}. Dry-run={dry_run}"))
