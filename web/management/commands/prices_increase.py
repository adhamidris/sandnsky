from django.core.management.base import BaseCommand
from django.db import transaction
from django.db.models import Q
from decimal import Decimal, ROUND_HALF_UP, InvalidOperation
import csv
import os
import re

from web.models import Trip  # adjust import if your app label is different

def q2(amount):
    """Quantize to 2 decimals, half up."""
    return amount.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

class Command(BaseCommand):
    help = (
        "Bulk-update Trip prices by fixed deltas. "
        "Adults: +adult_delta on base_price_per_person. "
        "Children: +child_delta on the EFFECTIVE child price; "
        "child_price_per_person is set explicitly to that new value."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--adult-delta",
            type=str,
            default="15",
            help="Amount to add to adult price (default: 15). Use decimal string, e.g. 12.50",
        )
        parser.add_argument(
            "--child-delta",
            type=str,
            default="10",
            help="Amount to add to child effective price (default: 10). Use decimal string.",
        )
        parser.add_argument(
            "--only-destinations",
            type=str,
            help='Comma-separated list of Destination.name values to include (e.g. "Cairo,Giza").',
        )
        parser.add_argument(
            "--slug-regex",
            type=str,
            help="Regex to filter Trip.slug (e.g. '^cairo-').",
        )
        parser.add_argument(
            "--include-services",
            action="store_true",
            help="Include trips where is_service=True (default: excluded).",
        )
        parser.add_argument(
            "--snapshot",
            type=str,
            help="Write a CSV snapshot (before & after) to this filepath.",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Preview changes without saving.",
        )

    def handle(self, *args, **opts):
        # Parse deltas as Decimal
        try:
            adult_delta = Decimal(opts["adult_delta"])
            child_delta = Decimal(opts["child_delta"])
        except (InvalidOperation, TypeError):
            self.stderr.write(self.style.ERROR("Invalid --adult-delta or --child-delta value."))
            return

        only_destinations = None
        if opts.get("only_destinations"):
            only_destinations = [s.strip() for s in opts["only_destinations"].split(",") if s.strip()]

        slug_regex = opts.get("slug_regex")
        include_services = opts.get("include_services")
        snapshot_path = opts.get("snapshot")
        dry_run = opts.get("dry_run")

        # Build queryset
        qs = Trip.objects.all().select_related("destination")
        if not include_services:
            qs = qs.filter(is_service=False)
        if only_destinations:
            qs = qs.filter(destination__name__in=only_destinations)
        if slug_regex:
            try:
                re.compile(slug_regex)
            except re.error as e:
                self.stderr.write(self.style.ERROR(f"Invalid --slug-regex: {e}"))
                return
            qs = qs.filter(slug__regex=slug_regex)

        count = qs.count()
        if count == 0:
            self.stdout.write(self.style.WARNING("No trips matched the filters. Nothing to do."))
            return

        self.stdout.write(self.style.NOTICE(f"Matched {count} trip(s)."))
        rows_for_snapshot = []

        # Prepare CSV header if snapshot requested
        if snapshot_path:
            os.makedirs(os.path.dirname(snapshot_path), exist_ok=True)
            rows_for_snapshot.append([
                "trip_id", "slug", "title", "destination",
                "adult_old", "adult_new",
                "child_effective_old", "child_new",
                "child_was_null", "is_service"
            ])

        planned = 0

        def new_prices(trip):
            adult_old = Decimal(trip.base_price_per_person)
            adult_new = q2(adult_old + adult_delta)
            # effective child BEFORE the change (your helper)
            child_effective_old = Decimal(trip.get_child_price_per_person())
            child_new = q2(child_effective_old + child_delta)
            return adult_old, adult_new, child_effective_old, child_new

        # Dry-run preview lines
        for t in qs.iterator():
            adult_old, adult_new, child_eff_old, child_new = new_prices(t)
            child_was_null = (t.child_price_per_person is None)
            self.stdout.write(
                f"- {t.slug} | {t.title} @ {t.destination.name} | "
                f"Adult: {adult_old} -> {adult_new} | "
                f"Child: {child_eff_old} -> {child_new} "
                f"{'(child was NULL)' if child_was_null else ''}"
            )
            if snapshot_path:
                rows_for_snapshot.append([
                    t.id,
                    t.slug,
                    t.title,
                    t.destination.name,
                    f"{adult_old}",
                    f"{adult_new}",
                    f"{child_eff_old}",
                    f"{child_new}",
                    "yes" if child_was_null else "no",
                    "yes" if t.is_service else "no",
                ])
            planned += 1

        if snapshot_path:
            with open(snapshot_path, "w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerows(rows_for_snapshot)
            self.stdout.write(self.style.SUCCESS(f"Snapshot written: {snapshot_path}"))

        if dry_run:
            self.stdout.write(self.style.SUCCESS("Dry-run complete. No changes made."))
            return

        # Apply in a transaction
        with transaction.atomic():
            updated = 0
            for t in qs.iterator():
                adult_old, adult_new, child_eff_old, child_new = new_prices(t)
                t.base_price_per_person = adult_new
                # Always set an explicit child price so +$10 applies even if previously NULL
                t.child_price_per_person = child_new
                t.save(update_fields=["base_price_per_person", "child_price_per_person", "updated_at"])
                updated += 1

        self.stdout.write(self.style.SUCCESS(f"Updated {updated} trip(s)."))
