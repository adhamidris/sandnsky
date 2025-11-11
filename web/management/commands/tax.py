from __future__ import annotations

from decimal import Decimal, ROUND_HALF_UP, InvalidOperation
from typing import Literal
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from web.models import Trip  # adjust app label if needed

Target = Literal["adult", "child", "both"]

def _bump_no_decimals(value: Decimal, factor: Decimal) -> Decimal:
    # Multiply then round to whole amount (no decimals), HALF_UP.
    return (value * factor).quantize(Decimal("1"), rounding=ROUND_HALF_UP)

class Command(BaseCommand):
    help = "Increase Trip price(s) by a percentage with no decimals (adult/child/both)."

    def add_arguments(self, parser):
        parser.add_argument("--percent", default="14",
                            help="Percent to increase (e.g., 14 for +14%%). Default: 14")
        parser.add_argument("--target", choices=["adult", "child", "both"], default="both",
                            help="Which prices to change. Default: both.")
        parser.add_argument("--exclude-services", action="store_true",
                            help="Skip trips where Trip.is_service=True.")
        parser.add_argument("--materialize-child-if-null", action="store_true",
                            help="If child price is NULL, create one based on adult×(1+percent).")
        parser.add_argument("--dry-run", action="store_true",
                            help="Preview changes without saving.")

    def handle(self, *args, **opts):
        # Parse inputs
        try:
            pct = Decimal(opts["percent"])
        except InvalidOperation as e:
            raise CommandError(f"Invalid --percent: {opts['percent']!r}") from e
        if pct <= Decimal("-100"):
            raise CommandError("Percent must be greater than -100.")
        factor = (Decimal(100) + pct) / Decimal(100)

        target: Target = opts["target"]
        exclude_services: bool = opts["exclude_services"]
        materialize_child: bool = opts["materialize_child_if_null"]
        dry_run: bool = opts["dry_run"]

        qs = Trip.objects.all()
        if exclude_services:
            qs = qs.filter(is_service=False)

        scanned = updated_adult = updated_child = skipped_child_null = 0

        ctx = transaction.atomic() if not dry_run else _NullCtx()
        with ctx:
            for trip in qs.iterator():
                scanned += 1
                dirty = []

                # Adult
                if target in ("adult", "both"):
                    old_a = trip.base_price_per_person
                    new_a = _bump_no_decimals(old_a, factor)
                    if new_a != old_a:
                        self.stdout.write(f"[ADULT] {trip.title!r}: {old_a} -> {new_a}" + (" [preview]" if dry_run else ""))
                        trip.base_price_per_person = new_a
                        dirty.append("base_price_per_person")
                        updated_adult += 1

                # Child
                if target in ("child", "both"):
                    if trip.child_price_per_person is None:
                        if materialize_child:
                            basis = trip.base_price_per_person
                            new_c = _bump_no_decimals(basis, factor)
                            self.stdout.write(f"[CHILD] {trip.title!r}: NULL -> {new_c}" + (" [preview]" if dry_run else ""))
                            trip.child_price_per_person = new_c
                            dirty.append("child_price_per_person")
                            updated_child += 1
                        else:
                            skipped_child_null += 1
                    else:
                        old_c = trip.child_price_per_person
                        new_c = _bump_no_decimals(old_c, factor)
                        if new_c != old_c:
                            self.stdout.write(f"[CHILD] {trip.title!r}: {old_c} -> {new_c}" + (" [preview]" if dry_run else ""))
                            trip.child_price_per_person = new_c
                            dirty.append("child_price_per_person")
                            updated_child += 1

                if dirty and not dry_run:
                    trip.save(update_fields=dirty)

        self.stdout.write(self.style.SUCCESS(
            f"Done. trips_scanned={scanned}, adult_updated={updated_adult}, "
            f"child_updated={updated_child}, child_skipped_null={skipped_child_null}, dry_run={dry_run}"
        ))

class _NullCtx:
    def __enter__(self): return self
    def __exit__(self, exc_type, exc, tb): return False
