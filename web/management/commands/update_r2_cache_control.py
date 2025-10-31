from __future__ import annotations

import os
from typing import Dict, List, Sequence, Set, Tuple

import boto3
from botocore.config import Config
from botocore.exceptions import ClientError

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.db import models

from web import models as web_models


MEDIA_MODEL_FIELDS: Sequence[Tuple[models.Model, Sequence[str]]] = (
    (web_models.Trip, ("hero_image", "card_image")),
    (web_models.TripGalleryImage, ("image",)),
    (web_models.Destination, ("hero_image", "card_image")),
    (web_models.DestinationGalleryImage, ("image",)),
    (web_models.LandingGalleryImage, ("image",)),
    (web_models.BlogPost, ("hero_image", "card_image")),
    (web_models.BlogSection, ("section_image",)),
    (web_models.SiteConfiguration, ("hero_image", "trips_hero_image", "gallery_background_image")),
    (web_models.SiteHeroPair, ("hero_image", "overlay_image")),
)


DEFAULT_CACHE_CONTROL = os.environ.get("CLOUDFLARE_R2_CACHE_CONTROL", "max-age=86400")


def _client() -> boto3.client:
    """
    Return a boto3 S3 client configured for Cloudflare R2 using the project's settings.
    """
    required_attrs = (
        "AWS_ACCESS_KEY_ID",
        "AWS_SECRET_ACCESS_KEY",
        "AWS_STORAGE_BUCKET_NAME",
        "AWS_S3_ENDPOINT_URL",
    )
    missing = [attr for attr in required_attrs if not getattr(settings, attr, None)]
    if missing:
        raise CommandError(
            "Cloudflare R2 storage is not configured in settings; "
            f"missing attributes: {', '.join(missing)}"
        )

    cfg = Config(
        s3={
            "addressing_style": getattr(settings, "AWS_S3_ADDRESSING_STYLE", "path"),
        }
    )
    return boto3.client(
        "s3",
        endpoint_url=getattr(settings, "AWS_S3_ENDPOINT_URL"),
        aws_access_key_id=getattr(settings, "AWS_ACCESS_KEY_ID"),
        aws_secret_access_key=getattr(settings, "AWS_SECRET_ACCESS_KEY"),
        region_name=getattr(settings, "AWS_S3_REGION_NAME", "auto"),
        config=cfg,
    )


def gather_object_keys() -> Set[str]:
    """
    Collect all unique object keys referenced by media fields we care about.
    """
    keys: Set[str] = set()
    for model_cls, field_names in MEDIA_MODEL_FIELDS:
        qs = model_cls.objects.all().only(*field_names)
        for instance in qs.iterator():
            for field_name in field_names:
                field_file = getattr(instance, field_name, None)
                if not field_file:
                    continue
                name = getattr(field_file, "name", "")
                if not name:
                    continue
                if name.startswith("http://") or name.startswith("https://"):
                    continue
                keys.add(name.lstrip("/"))
    return keys


def _copy_kwargs_from_head(head: Dict, cache_control: str) -> Dict:
    """
    Build kwargs for copy_object that preserve existing metadata.
    """
    params: Dict = {"MetadataDirective": "REPLACE", "CacheControl": cache_control}
    if head.get("ContentType"):
        params["ContentType"] = head["ContentType"]
    if head.get("ContentLanguage"):
        params["ContentLanguage"] = head["ContentLanguage"]
    if head.get("ContentEncoding"):
        params["ContentEncoding"] = head["ContentEncoding"]
    if head.get("ContentDisposition"):
        params["ContentDisposition"] = head["ContentDisposition"]
    if head.get("Metadata"):
        params["Metadata"] = head["Metadata"]
    return params


class Command(BaseCommand):
    help = "Ensure Cloudflare R2 objects have the desired Cache-Control header."

    def add_arguments(self, parser):
        parser.add_argument(
            "--cache-control",
            default=DEFAULT_CACHE_CONTROL,
            help=f"Cache-Control header to apply (default: %(default)s).",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Enumerate affected keys without performing updates.",
        )
        parser.add_argument(
            "--limit",
            type=int,
            default=None,
            help="Only process the first N keys (useful for testing).",
        )
        parser.add_argument(
            "--include-prefix",
            action="append",
            default=None,
            help="Restrict updates to keys that start with the given prefix. Can repeat.",
        )

    def handle(self, *args, **options):
        cache_control: str = options["cache_control"]
        dry_run: bool = options["dry_run"]
        limit: int | None = options["limit"]
        include_prefixes: List[str] | None = options["include_prefix"] or None

        if not cache_control:
            raise CommandError("Provide a non-empty Cache-Control value.")

        client = _client()
        bucket = getattr(settings, "AWS_STORAGE_BUCKET_NAME")

        keys = sorted(gather_object_keys())
        if include_prefixes:
            prefixes = tuple(p.strip("/") for p in include_prefixes)
            keys = [k for k in keys if k.startswith(prefixes)]

        if not keys:
            self.stdout.write(self.style.WARNING("No object keys found to update."))
            return

        if limit:
            keys = keys[:limit]

        self.stdout.write(self.style.HTTP_INFO(f"Processing {len(keys)} R2 object(s)."))
        updated = skipped = errors = 0

        for key in keys:
            try:
                head = client.head_object(Bucket=bucket, Key=key)
            except ClientError as exc:
                errors += 1
                self.stdout.write(
                    self.style.ERROR(f"[{key}] head_object failed: {exc.response['Error'].get('Message', exc)}")
                )
                continue

            current_cc = head.get("CacheControl")
            if current_cc == cache_control:
                skipped += 1
                continue

            if dry_run:
                updated += 1
                self.stdout.write(self.style.NOTICE(f"[dry-run] Would update Cache-Control for {key!r} (current={current_cc!r})"))
                continue

            params = {
                "Bucket": bucket,
                "Key": key,
                "CopySource": {"Bucket": bucket, "Key": key},
            }
            params.update(_copy_kwargs_from_head(head, cache_control))

            try:
                client.copy_object(**params)
            except ClientError as exc:
                errors += 1
                self.stdout.write(
                    self.style.ERROR(f"[{key}] copy_object failed: {exc.response['Error'].get('Message', exc)}")
                )
                continue

            updated += 1
            self.stdout.write(self.style.SUCCESS(f"Updated Cache-Control for {key!r}"))

        summary = (
            f"Done. Updated={updated} Skipped={skipped} Errors={errors} "
            f"Dry-run={'yes' if dry_run else 'no'}"
        )
        if errors:
            self.stdout.write(self.style.ERROR(summary))
        else:
            self.stdout.write(self.style.SUCCESS(summary))
