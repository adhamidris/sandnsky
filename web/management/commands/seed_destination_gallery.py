# web/management/commands/seed_destination_gallery.py
from __future__ import annotations

import os
from pathlib import Path
from typing import Dict, List, Optional, Iterable

import boto3
from botocore.config import Config

from django.core.files import File
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils.text import slugify
from django.conf import settings

from web.models import Destination, DestinationName, DestinationGalleryImage

IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".webp", ".gif"}
JUNK_NAMES = {".ds_store", "thumbs.db", "desktop.ini"}

FOLDER_TO_DEST: Dict[str, str] = {
    "siwa": DestinationName.SIWA.value,
    "fayoum": DestinationName.FAYOUM.value,
    "white desert": DestinationName.WHITE_BLACK.value,
    "white-desert": DestinationName.WHITE_BLACK.value,
    "black desert": DestinationName.WHITE_BLACK.value,
    "black-desert": DestinationName.WHITE_BLACK.value,
    "farafra": DestinationName.FARAFRA.value,
    "dakhla": DestinationName.DAKHLA.value,
    "kharga": DestinationName.KHARGA.value,
    "bahareya": DestinationName.BAHAREYA.value,
    "bahariya": DestinationName.BAHAREYA.value,
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

def norm(s: str) -> str:
    return s.strip().lower().replace("_", " ").replace("-", " ")

def humanize_caption(filename: str) -> str:
    base = Path(filename).stem
    base = base.replace("_", " ").replace("-", " ")
    base = " ".join(base.split())
    return base.title()[:200]

def is_image_name(name: str) -> bool:
    return Path(name).suffix.lower() in IMAGE_EXTS and name.lower() not in JUNK_NAMES

def get_boto3_client(endpoint: str | None) -> boto3.client:
    cfg = Config(s3={"addressing_style": os.environ.get("CLOUDFLARE_R2_ADDRESSING_STYLE", "path")})
    return boto3.client(
        "s3",
        endpoint_url=endpoint,
        aws_access_key_id=os.environ.get("CLOUDFLARE_R2_ACCESS_KEY_ID"),
        aws_secret_access_key=os.environ.get("CLOUDFLARE_R2_SECRET_ACCESS_KEY"),
        region_name=os.environ.get("CLOUDFLARE_R2_REGION", "auto"),
        config=cfg,
    )

def s3_list_objects(c, bucket: str, prefix: str) -> Iterable[dict]:
    token = None
    while True:
        kw = {"Bucket": bucket, "Prefix": prefix}
        if token:
            kw["ContinuationToken"] = token
        resp = c.list_objects_v2(**kw)
        for it in resp.get("Contents", []):
            yield it
        if resp.get("IsTruncated"):
            token = resp.get("NextContinuationToken")
        else:
            break

class Command(BaseCommand):
    help = "Seed DestinationGalleryImage from local dir or Cloudflare R2."

    def add_arguments(self, parser):
        # Local mode (old behavior)
        parser.add_argument("--base-dir", default=None, help="Local base dir like 'media/tripz'")

        # S3/R2 mode
        parser.add_argument("--s3-bucket", default=None, help="Bucket name (R2)")
        parser.add_argument("--s3-endpoint", default=os.environ.get("CLOUDFLARE_R2_ENDPOINT_URL"), help="Endpoint URL")
        parser.add_argument("--s3-prefix", default="tripz/", help="Key prefix to scan, e.g. 'tripz/'")

        # Common options
        parser.add_argument("--dry-run", action="store_true")
        parser.add_argument("--wipe", action="store_true")
        parser.add_argument("--caption-from-name", action="store_true")

    def handle(self, *args, **opts):
        base_dir: Optional[str] = opts["base_dir"]
        s3_bucket: Optional[str] = opts["s3_bucket"] or os.environ.get("CLOUDFLARE_R2_BUCKET")
        s3_endpoint: Optional[str] = opts["s3_endpoint"]
        s3_prefix: str = opts["s3_prefix"].lstrip("/")

        dry = opts["dry_run"]
        wipe = opts["wipe"]
        caption_from_name = opts["caption_from_name"]

        local_mode = bool(base_dir)
        s3_mode = bool(s3_bucket)

        if local_mode and s3_mode:
            raise CommandError("Choose either --base-dir (local) OR --s3-bucket (R2), not both.")
        if not local_mode and not s3_mode:
            raise CommandError("Provide --base-dir for local OR --s3-bucket for R2 mode.")

        # Build folder → Destination
        dest_map: Dict[str, Destination] = {}

        if local_mode:
            root = Path(base_dir).resolve()
            if not root.exists() or not root.is_dir():
                raise CommandError(f"Base dir not found or not a directory: {root}")
            buckets = [p for p in sorted(root.iterdir()) if p.is_dir()]
            for bucket in buckets:
                key = FOLDER_TO_DEST.get(norm(bucket.name)) or FOLDER_TO_DEST.get(norm(slugify(bucket.name)))
                if not key:
                    self.stdout.write(self.style.WARNING(f"Unmapped folder (skip): {bucket.name}"))
                    continue
                try:
                    dest_map[bucket.name] = Destination.objects.get(name=key)
                except Destination.DoesNotExist:
                    self.stdout.write(self.style.ERROR(f"Missing Destination row: {key}"))
        else:
            # Group S3 keys by immediate subfolder under s3_prefix
            c = get_boto3_client(s3_endpoint)
            seen_folders = {}
            for obj in s3_list_objects(c, s3_bucket, s3_prefix):
                key = obj["Key"]
                if not key.startswith(s3_prefix):
                    continue
                rest = key[len(s3_prefix):]
                parts = rest.split("/", 1)
                if len(parts) < 2:
                    continue
                folder = parts[0]  # e.g., "Siwa", "white-desert", etc.
                seen_folders[folder] = True

            for folder in sorted(seen_folders.keys()):
                folder_norm = norm(folder)
                key_name = FOLDER_TO_DEST.get(folder_norm) or FOLDER_TO_DEST.get(norm(slugify(folder)))
                if not key_name:
                    self.stdout.write(self.style.WARNING(f"Unmapped folder (skip): {folder}"))
                    continue
                try:
                    dest_map[folder] = Destination.objects.get(name=key_name)
                except Destination.DoesNotExist:
                    self.stdout.write(self.style.ERROR(f"Missing Destination row: {key_name}"))

        # Plan
        self.stdout.write(self.style.MIGRATE_HEADING("Planned seeding:"))
        if local_mode:
            for folder, dest in dest_map.items():
                cnt = sum(1 for _ in (Path(base_dir) / folder).rglob("*") if _.is_file() and is_image_name(_.name))
                self.stdout.write(f"  {folder} → {dest.name} ({cnt} images)")
        else:
            c = get_boto3_client(s3_endpoint)
            for folder, dest in dest_map.items():
                cnt = 0
                for obj in s3_list_objects(c, s3_bucket, f"{s3_prefix.rstrip('/')}/{folder}/"):
                    if is_image_name(obj["Key"]):
                        cnt += 1
                self.stdout.write(f"  {folder} → {dest.name} ({cnt} images)")

        if dry:
            self.stdout.write(self.style.NOTICE("Dry-run: no DB writes."))

        with transaction.atomic():
            affected_ids = list({d.pk for d in dest_map.values()})
            if wipe and affected_ids:
                qs = DestinationGalleryImage.objects.filter(destination_id__in=affected_ids)
                n = qs.count()
                if dry:
                    self.stdout.write(self.style.WARNING(f"[dry-run] Would delete {n} gallery rows"))
                else:
                    qs.delete()
                    self.stdout.write(self.style.WARNING(f"Deleted existing gallery rows: {n}"))

            created = 0

            if local_mode:
                for folder, dest in dest_map.items():
                    base = Path(base_dir) / folder
                    # next position
                    existing_max = (DestinationGalleryImage.objects
                                    .filter(destination=dest)
                                    .order_by("-position")
                                    .values_list("position", flat=True)
                                    .first())
                    pos = (existing_max or 0) + 1

                    for p in sorted(base.rglob("*")):
                        if not (p.is_file() and is_image_name(p.name)):
                            continue

                        filename = p.name
                        if DestinationGalleryImage.objects.filter(destination=dest, image__iendswith=f"/{filename}").exists():
                            self.stdout.write(self.style.NOTICE(f"Skip duplicate name: {dest.name} · {filename}"))
                            continue

                        relkey = f"{dest.slug}/{filename}"  # under upload_to base
                        if dry:
                            self.stdout.write(f"[dry-run] + {dest.name} · pos={pos} · {p}")
                            pos += 1
                            continue

                        with open(p, "rb") as fh:
                            row = DestinationGalleryImage(
                                destination=dest,
                                position=pos,
                                caption=(humanize_caption(filename) if caption_from_name else "")
                            )
                            row.image.save(relkey, File(fh), save=False)
                            row.save()
                        created += 1
                        pos += 1
                        self.stdout.write(self.style.SUCCESS(f"+ {dest.name} · pos={pos-1} · {filename}"))

            else:
                # S3 → S3 direct copy (server-side), no download
                c = get_boto3_client(s3_endpoint)
                bucket = s3_bucket

                for folder, dest in dest_map.items():
                    existing_max = (DestinationGalleryImage.objects
                                    .filter(destination=dest)
                                    .order_by("-position")
                                    .values_list("position", flat=True)
                                    .first())
                    pos = (existing_max or 0) + 1

                    prefix = f"{s3_prefix.rstrip('/')}/{folder}/"
                    for obj in s3_list_objects(c, bucket, prefix):
                        key = obj["Key"]
                        if not is_image_name(key):
                            continue
                        filename = Path(key).name

                        if DestinationGalleryImage.objects.filter(destination=dest, image__iendswith=f"/{filename}").exists():
                            self.stdout.write(self.style.NOTICE(f"Skip duplicate name: {dest.name} · {filename}"))
                            continue

                        target = f"destinations/gallery/{dest.slug}/{filename}"

                        if dry:
                            self.stdout.write(f"[dry-run] + {dest.name} · pos={pos} · s3://{bucket}/{key} -> {target}")
                            pos += 1
                            continue

                        # server-side copy within the same bucket
                        c.copy(
                            CopySource={"Bucket": bucket, "Key": key},
                            Bucket=bucket,
                            Key=target,
                        )

                        row = DestinationGalleryImage(
                            destination=dest,
                            position=pos,
                            caption=(humanize_caption(filename) if caption_from_name else "")
                        )
                        # Point ImageField to the copied key (no upload)
                        row.image.name = target
                        row.save()

                        created += 1
                        pos += 1
                        self.stdout.write(self.style.SUCCESS(f"+ {dest.name} · pos={pos-1} · {filename}"))

            if dry:
                self.stdout.write(self.style.MIGRATE_HEADING("[dry-run] Done. Created=0"))
            else:
                self.stdout.write(self.style.MIGRATE_HEADING(f"Done. Created={created}"))
